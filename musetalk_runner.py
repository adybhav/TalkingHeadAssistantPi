from __future__ import annotations

import atexit
import json
import math
import os
import shutil
import subprocess
import tempfile
import threading
import uuid
import wave
from pathlib import Path


MUSETALK_DIR = Path(r"C:\Projects\MuseTalk")
MUSETALK_PYTHON = (
    MUSETALK_DIR / ".venv" / "Scripts" / "python.exe"
)

REFERENCE_VIDEO = Path(
    r"C:\Projects\TalkingHeadAssistantPi\idle_720p.mp4"
)

AVATAR_ID = "talking_head"
FPS = 14
BATCH_SIZE = 5


class MuseTalkWorker:
    """A persistent MuseTalk subprocess with models loaded once."""

    def __init__(self, batch_size: int = BATCH_SIZE) -> None:
        if not MUSETALK_PYTHON.is_file():
            raise FileNotFoundError(
                f"MuseTalk Python was not found: {MUSETALK_PYTHON}"
            )

        self.batch_size = batch_size

        if not REFERENCE_VIDEO.is_file():
            raise FileNotFoundError(
                f"Reference video was not found: {REFERENCE_VIDEO}"
            )

        self._lock = threading.Lock()

        config_directory = (
            MUSETALK_DIR / "results" / "_worker"
        )
        config_directory.mkdir(parents=True, exist_ok=True)

        self.config_path = (
            config_directory / "talking_head_worker.yaml"
        )

        # The avatar was already prepared, so preparation stays false.
        config_text = (
            f"{AVATAR_ID}:\n"
            f"  preparation: false\n"
            f"  bbox_shift: 0\n"
            f"  video_path: "
            f"{json.dumps(str(REFERENCE_VIDEO.resolve()))}\n"
            f"  audio_clips: {{}}\n"
        )

        self.config_path.write_text(
            config_text,
            encoding="utf-8",
        )

        command = [
            str(MUSETALK_PYTHON),
            "-u",
            "-m",
            "scripts.realtime_inference",
            "--worker",
            "--inference_config",
            str(self.config_path),
            "--unet_model_path",
            r"models\musetalkV15\unet.pth",
            "--unet_config",
            r"models\musetalkV15\musetalk.json",
            "--version",
            "v15",
            "--fps",
            str(FPS),
            "--batch_size",
            str(self.batch_size),
            "--gpu_id",
            "0",
            "--extra_margin",
            "10",
            "--parsing_mode",
            "jaw",
        ]

        environment = os.environ.copy()
        environment["PYTHONUTF8"] = "1"
        environment["PYTHONPATH"] = str(MUSETALK_DIR)

        # Keep stdout available for worker result messages.
        # Let stderr appear normally for tqdm and errors.
        self.process = subprocess.Popen(
            command,
            cwd=str(MUSETALK_DIR),
            env=environment,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=None,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )

        self._wait_until_ready()

    def _wait_until_ready(self) -> None:
        assert self.process.stdout is not None

        while True:
            line = self.process.stdout.readline()

            if not line:
                return_code = self.process.poll()

                if return_code is not None:
                    raise RuntimeError(
                        "MuseTalk worker exited during startup "
                        f"with code {return_code}."
                    )

                continue

            print(line, end="")

            if line.strip() == "MUSETALK_WORKER_READY":
                return

    def generate(
        self,
        audio_path: str | Path,
        output_path: str | Path,
    ) -> Path:
        audio_path = Path(audio_path).resolve()
        output_path = Path(output_path).resolve()

        if not audio_path.is_file():
            raise FileNotFoundError(
                f"Audio file was not found: {audio_path}"
            )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if self.process.poll() is not None:
            raise RuntimeError("MuseTalk worker is not running.")

        job_id = f"job_{uuid.uuid4().hex}"

        message = {
            "audio_path": str(audio_path),
            "output_name": job_id,
        }

        # MuseTalk currently handles one inference at a time.
        with self._lock:
            assert self.process.stdin is not None
            assert self.process.stdout is not None

            self.process.stdin.write(
                json.dumps(message) + "\n"
            )
            self.process.stdin.flush()

            while True:
                line = self.process.stdout.readline()

                if not line:
                    return_code = self.process.poll()

                    if return_code is not None:
                        raise RuntimeError(
                            "MuseTalk worker stopped unexpectedly "
                            f"with code {return_code}."
                        )

                    continue

                print(line, end="")

                prefix = "MUSETALK_RESULT "

                if not line.startswith(prefix):
                    continue

                result = json.loads(
                    line[len(prefix):]
                )

                if not result["ok"]:
                    raise RuntimeError(
                        "MuseTalk failed:\n"
                        + result.get("error", "Unknown error")
                    )

                generated_path = Path(
                    result["output_path"]
                )

                if not generated_path.is_file():
                    raise RuntimeError(
                        "MuseTalk reported success but the "
                        "output file was not found:\n"
                        f"{generated_path}"
                    )

                if output_path.exists():
                    output_path.unlink()

                shutil.move(
                    str(generated_path),
                    str(output_path),
                )

                return output_path

    def close(self) -> None:
        if not hasattr(self, "process"):
            return

        if self.process.poll() is not None:
            return

        try:
            if self.process.stdin is not None:
                self.process.stdin.write(
                    json.dumps(
                        {"command": "shutdown"}
                    )
                    + "\n"
                )
                self.process.stdin.flush()

            self.process.wait(timeout=10)

        except (OSError, subprocess.TimeoutExpired):
            self.process.terminate()


# Created lazily on first use so importing this module doesn't launch a GPU worker.
_worker: MuseTalkWorker | None = None
_worker_lock = threading.Lock()


def _get_worker() -> MuseTalkWorker:
    global _worker

    if _worker is None:
        with _worker_lock:
            if _worker is None:
                _worker = MuseTalkWorker()
                atexit.register(_worker.close)

    return _worker


def preload_worker() -> None:
    """Load models now and run a throwaway inference so cudnn/CUDA kernels are
    already compiled before the first real request comes in."""
    worker = _get_worker()

    # Long enough to include at least one full-size batch, matching production shapes.
    warmup_seconds = math.ceil(worker.batch_size / FPS) + 1

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        warmup_audio_path = temp_dir_path / "warmup_silence.wav"
        warmup_output_path = temp_dir_path / "warmup_output.mp4"

        _write_silence(warmup_audio_path, seconds=warmup_seconds)

        print("Warming up MuseTalk worker...")
        worker.generate(warmup_audio_path, warmup_output_path)
        print("MuseTalk worker warm-up complete.")


def _write_silence(path: Path, seconds: float, framerate: int = 16000) -> None:
    frame_count = int(framerate * seconds)
    silence = b"\x00\x00" * frame_count

    with wave.open(str(path), "wb") as destination:
        destination.setnchannels(1)
        destination.setsampwidth(2)
        destination.setframerate(framerate)
        destination.writeframes(silence)


def run_lipsync(
    video_path: str | Path,
    audio_path: str | Path,
    output_path: str | Path,
) -> Path:
    """
    Generate a video using the persistent MuseTalk worker.

    video_path is checked because the worker supports one fixed avatar.
    """
    supplied_video = Path(video_path).resolve()

    if supplied_video != REFERENCE_VIDEO.resolve():
        raise ValueError(
            "This worker was prepared for a different video:\n"
            f"{REFERENCE_VIDEO}"
        )

    return _get_worker().generate(
        audio_path=audio_path,
        output_path=output_path,
    )

if __name__ == "__main__":
    result = run_lipsync(
        video_path=r"C:\Projects\TalkingHeadAssistant\idle_720p.mp4",
        audio_path=r"C:\Projects\TalkingHeadAssistant\output_audio.wav",
        output_path=r"C:\Projects\TalkingHeadAssistant\output_muse\result.mp4",
    )

    print(f"Created: {result}")