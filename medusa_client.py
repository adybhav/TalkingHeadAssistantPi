import os

os.environ["ALSA_LOG_LEVEL"] = "none"  # silence ALSA spam

import json
import socket
import time
import signal
import subprocess
import requests
import speech_recognition as sr

# ---- Paths ----
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
IDLE_VIDEO   = os.path.join(BASE_DIR, "idle.mp4")
ASK_VIDEO    = os.path.join(BASE_DIR, "askmeaquestion.mp4")
OUTPUT_VIDEO = os.path.join(BASE_DIR, "result.mp4")
AUDIO_FILE   = os.path.join(BASE_DIR, "input_audio.wav")
MPV_SOCKET   = "/tmp/medusa-mpv.sock"


# ---- Display + rotation ----

# Set these to your ROTATED screen resolution.a
# If your TV is 1920x1080 landscape and you rotate 90°, set 1080x1920.
SCREEN_W = 720
SCREEN_H = 1280
ROTATE_DEG = 270  # use 270 if rotated the other way

# mpv filter that scales to COVER the screen (no stretch), then crops overflow
VF_COVER = f"scale={SCREEN_W}:{SCREEN_H}:force_original_aspect_ratio=increase,crop={SCREEN_W}:{SCREEN_H}"



# ---- Wake & server ----

WAKE_WORDS = ["hey medusa", "gaze into my eyes"]
SERVER_URL = "http://192.168.1.157:5000/process"
VIDEO_PREROLL_SECONDS = 0.35

mpv_process = None
mpv_request_id = 0
recognizer = sr.Recognizer()
mic = sr.Microphone()

COMMON_MPV_FLAGS = [
    "--no-terminal", "--really-quiet",
    "--fs",
    "--gpu-context=drm",               # render directly to console (no X)
    f"--video-rotate={ROTATE_DEG}",
    f"--vf={VF_COVER}",                # force fill screen regardless of source AR
    "--audio-stream-silence=yes",      # keep audio device warm between clips
    "--gapless-audio=yes",
    "--input-default-bindings=no",
    "--input-vo-keyboard=no",
]

def send_mpv_command(command):
    """Send one JSON IPC command to the persistent mpv process."""
    global mpv_request_id
    mpv_request_id += 1
    request_id = mpv_request_id

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(2)
        client.connect(MPV_SOCKET)
        payload = {"command": command, "request_id": request_id}
        client.sendall((json.dumps(payload) + "\n").encode("utf-8"))

        buffer = ""
        while True:
            buffer += client.recv(4096).decode("utf-8")
            for line in buffer.splitlines():
                if not line:
                    continue
                response = json.loads(line)
                if response.get("request_id") == request_id:
                    return response

def get_mpv_property(name):
    """Read one property from the persistent mpv process."""
    response = send_mpv_command(["get_property", name])
    return response.get("data")

def start_mpv():
    """Start one persistent mpv process so the display never drops to desktop."""
    global mpv_process
    if mpv_process and mpv_process.poll() is None:
        return

    try:
        os.unlink(MPV_SOCKET)
    except FileNotFoundError:
        pass

    cmd = [
        "mpv", *COMMON_MPV_FLAGS,
        f"--input-ipc-server={MPV_SOCKET}",
        "--idle=yes",
        "--force-window=yes",
        "--loop-file=inf",
    ]
    mpv_process = subprocess.Popen(
        cmd,
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid
    )

    for _ in range(20):
        if os.path.exists(MPV_SOCKET):
            return
        time.sleep(0.1)

def load_video(path, loop=False, paused=False):
    """Load a video into the persistent mpv process."""
    abs_path = os.path.abspath(path)
    if not os.path.exists(abs_path):
        return False
    start_mpv()
    send_mpv_command(["set_property", "pause", paused])
    send_mpv_command(["set_property", "loop-file", "inf" if loop else "no"])
    send_mpv_command(["loadfile", abs_path, "replace"])
    return True

def start_idle_video():
    """Start or switch back to the looping idle video."""
    load_video(IDLE_VIDEO, loop=True)

def stop_idle_video():
    """Stop mpv cleanly."""
    global mpv_process
    if mpv_process and mpv_process.poll() is None:
        mpv_process.send_signal(signal.SIGINT)
        try:
            mpv_process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            mpv_process.kill()
    mpv_process = None

def play_video(path, return_to_idle=True):
    """Play a single video fullscreen, then return to idle."""
    abs_path = os.path.abspath(path)
    if not os.path.exists(abs_path):
        return
    load_video(abs_path, loop=False, paused=True)
    time.sleep(VIDEO_PREROLL_SECONDS)
    send_mpv_command(["set_property", "pause", False])
    while mpv_process and mpv_process.poll() is None:
        try:
            if get_mpv_property("idle-active") is True:
                break
        except (OSError, json.JSONDecodeError, TimeoutError):
            break
        time.sleep(0.1)
    if return_to_idle:
        start_idle_video()

def calibrate_microphone():
    """Calibrate once while the user is not speaking."""
    recognizer.pause_threshold = 0.8
    recognizer.non_speaking_duration = 0.2
    recognizer.dynamic_energy_threshold = True
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.75)
    recognizer.energy_threshold = max(100, recognizer.energy_threshold * 0.8)
    recognizer.dynamic_energy_threshold = False

def listen_for_wake_word():
    with mic as source:
        while True:
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                text  = recognizer.recognize_google(audio).lower()
                if any(p in text for p in WAKE_WORDS):
                    return
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                continue
            except sr.RequestError:
                time.sleep(2)

def record_user_input():
    with mic as source:
        audio = recognizer.listen(source, timeout=None, phrase_time_limit=12)
    with open(AUDIO_FILE, "wb") as f:
        f.write(audio.get_wav_data())

def send_audio_to_server():
    try:
        with open(AUDIO_FILE, "rb") as audio_file:
            r = requests.post(SERVER_URL, files={"audio": audio_file}, timeout=180)
        if r.status_code == 200:
            with open(OUTPUT_VIDEO, "wb") as f:
                f.write(r.content)
            return True
        return False
    except requests.RequestException:
        return False

def run_client():
    calibrate_microphone()
    start_idle_video()  # keep idle looping in the background
    while True:
        listen_for_wake_word()   # idle keeps playing
        play_video(ASK_VIDEO, return_to_idle=False)
        record_user_input()      # idle still playing
        start_idle_video()
        if send_audio_to_server():
            play_video(OUTPUT_VIDEO)

if __name__ == "__main__":
    try:
        run_client()
    finally:
        stop_idle_video()

