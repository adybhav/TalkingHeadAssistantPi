import os
os.environ["ALSA_LOG_LEVEL"] = "none"  # silence ALSA spam

import time
import signal
import subprocess
import requests
import speech_recognition as sr

# ---- Paths (absolute avoids surprises) ----
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
IDLE_VIDEO   = os.path.join(BASE_DIR, "idle.mp4")
OUTPUT_VIDEO = os.path.join(BASE_DIR, "result.mp4")
AUDIO_FILE   = os.path.join(BASE_DIR, "input_audio.wav")

# ---- Wake & server ----
WAKE_WORDS = ["hey medusa", "gaze into my eyes"]
SERVER_URL = "http://192.168.1.157:5000/process"  # your desktop server

# ---- Video settings ----
ROTATE_DEG = 270   # change to 270 if needed
# Fill the whole screen: panscan zooms while preserving aspect (no stretching).
COMMON_MPV_FLAGS = [
    "--no-terminal", "--really-quiet",
    "--fs",
    "--gpu-context=drm",
    f"--video-rotate={ROTATE_DEG}",
    "--input-default-bindings=no",
    "--input-vo-keyboard=no",
]
 #   "--panscan=1.0",         # zoom to fill screen


idle_process = None

# ---------- Video (mpv / DRM / fullscreen) ----------
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
    time.sleep(0.3)  # give mpv a moment to appear

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

# ---------- Audio / Wake ----------
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

# ---------- Network ----------
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

# ---------- Main loop ----------
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
