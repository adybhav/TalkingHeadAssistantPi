import os
os.environ["ALSA_LOG_LEVEL"] = "none"  # silence ALSA spam

import time
import signal
import subprocess
import requests
import speech_recognition as sr

# ---- Paths ----
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
IDLE_VIDEO   = os.path.join(BASE_DIR, "idle.mp4")
OUTPUT_VIDEO = os.path.join(BASE_DIR, "result.mp4")
AUDIO_FILE   = os.path.join(BASE_DIR, "input_audio.wav")

# ---- Display + rotation ----
# Set these to your ROTATED screen resolution.
# If your TV is 1920x1080 landscape and you rotate 90°, set 1080x1920.
SCREEN_W = 1080
SCREEN_H = 1920
ROTATE_DEG = 90  # use 270 if rotated the other way

# mpv filter that scales to COVER the screen (no stretch), then crops overflow
VF_COVER = f"scale={SCREEN_W}:{SCREEN_H}:force_original_aspect_ratio=increase,crop={SCREEN_W}:{SCREEN_H}"

# ---- Wake & server ----
WAKE_WORDS = ["hey medusa", "gaze into my eyes"]
SERVER_URL = "http://192.168.1.157:5000/process"

idle_process = None

COMMON_MPV_FLAGS = [
    "--no-terminal", "--really-quiet",
    "--fs",
    "--gpu-context=drm",               # render directly to console (no X)
    f"--video-rotate={ROTATE_DEG}",
    f"--vf={VF_COVER}",                # force fill screen regardless of source AR
    "--input-default-bindings=no",
    "--input-vo-keyboard=no",
]

def start_idle_video():
    """Start looping idle video with mpv and keep a handle to it."""
    global idle_process
    if idle_process and idle_process.poll() is None:
        return
    if not os.path.exists(IDLE_VIDEO):
        return

    cmd = ["mpv", *COMMON_MPV_FLAGS, "--loop-file=inf", IDLE_VIDEO]
    idle_process = subprocess.Popen(
        cmd,
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid
    )
    time.sleep(0.3)  # let mpv appear

def stop_idle_video():
    """Stop idle video cleanly."""
    global idle_process
    if idle_process and idle_process.poll() is None:
        idle_process.send_signal(signal.SIGINT)
        try:
            idle_process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            idle_process.kill()
    idle_process = None

def play_video(path):
    """Play a single video fullscreen; returns when it ends."""
    abs_path = os.path.abspath(path)
    if not os.path.exists(abs_path):
        return
    cmd = ["mpv", *COMMON_MPV_FLAGS, "--loop-file=no", abs_path]
    subprocess.run(
        cmd,
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

def listen_for_wake_word():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
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
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
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
    start_idle_video()  # keep idle looping in the background
    while True:
        listen_for_wake_word()   # idle keeps playing
        record_user_input()      # idle still playing
        if send_audio_to_server():
            stop_idle_video()    # pause idle
            play_video(OUTPUT_VIDEO)
            start_idle_video()   # resume idle

if __name__ == "__main__":
    run_client()
