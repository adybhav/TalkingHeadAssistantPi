import os
import time
import contextlib

from modules.asr import transcribe_audio, record_audio
from modules.llm import generate_response
from modules.lipsync import run_lipsync
from waitandwake import wait_for_wake_and_record


@contextlib.contextmanager
def suppress_console_output():
    with open(os.devnull, "w", encoding="utf-8") as devnull:
        with contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
            yield


# Suppress TTS model initialization messages
with suppress_console_output():
    from modules.tts import text_to_speech


def medusa_loop():
    start_time = time.time()
    print("🎙️ done listening")

    transcript = "What are the major headlines today 07/27/2026"
    response = generate_response(transcript)

    with suppress_console_output():
        text_to_speech(response, "./output_audio.wav")

    run_lipsync(
        "./medusa_01.mp4",
        "./output_audio.wav",
        "./result.mp4",
    )

    total_time = time.time() - start_time
    print(f"\n🕒 Total generation time: {total_time:.2f} seconds")


if __name__ == "__main__":
    medusa_loop()