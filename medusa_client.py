import os
os.environ["ALSA_LOG_LEVEL"] = "none"  # silence ALSA spam

import json
import socket
import time
import requests
import speech_recognition as sr

# -------- Config --------
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
IDLE_VIDEO    = os.path.join(BASE_DIR, "idle.mp4")
OUTPUT_VIDEO  = os.path.join(BASE_DIR, "result.mp4")
AUDIO_FILE    = os.path.join(BASE_DIR, "input_audio.wav")
SERVER_URL    = "http://192.168.1.157:5000/process"   # your desktop server
WAKE_WORDS    = ["hey medusa", "gaze into my eyes"]
MPV_SOCKET    = "/tmp/medusa-mpv.sock"
ROTATE_DEG    = 90   # set to 270 if rotated the other way

# -------- mpv control via IPC --------
def start_mpv_idle():
    """Launch a single mpv instance in DRM fullscreen, rotated, looping idle.mp4, with IPC socket."""
    # clean old socket
    try:
        if os.path.exists(MPV_SOCKET):
            os.remove(MPV_SOCKET)
    except Exception:
        pass

    cmd = [
        "mpv",
        "--no-terminal", "--really-quiet",
        "--fs",
        "--gpu-context=drm",            # render directly to console
        f"--video-rotate={ROTATE_DEG}", # rotate both idle & result
        "--idle=yes",                   # keep mpv alive between loads
        "--keep-open=no",
        "--loop-file=inf",              # loop idle
        f"--input-ipc-server={MPV_SOCKET}",
        IDLE_VIDEO,
    ]
    # Start detached; mpv will own the screen
    os.spawnlp(os.P_NOWAIT, cmd[0], *cmd)

    # wait for socket to appear
    for _ in range(50):
        if os.path.exists(MPV_SOCKET):
            # slight extra delay to ensure mpv is ready to accept commands
            time.sleep(0.2)
            return
        time.sleep(0.1)
    # If we get here, mpv didn't start; let it fail loudly on next command.

def mpv_send(cmd_dict):
    """Send a single command to mpv IPC and return parsed response lines (if any)."""
    data = (json.dumps(cmd_dict) + "\n").encode("utf-8")
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.connect(MPV_SOCKET)
        s.sendall(data)
        # read a few responses (mpv responds with one line per command)
        s.settimeout(1.0)
        try:
            buf = s.recv(4096)
            if not buf:
                return None
            # mpv can send multiple JSON lines; split and parse best-effort
            lines = [l for l in buf.decode("utf-8", "ignore").splitlines() if l.strip()]
            parsed = []
            for line in lines:
                try:
                    parsed.append(json.loads(line))
                except Exception:
                    pass
            return parsed
        except socket.timeout:
            return None

def mpv_wait_for_endfile():
    """Block until mpv reports end of current file, then return."""
    # Subscribe to events by reading the socket continuously until end-file arrives.
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.connect(MPV_SOCKET)
        s.settimeout(None)
        while True:
            line = s.recv(4096).decode("utf-8", "ignore")
            for entry in [l for l in line.splitlines() if l.strip()]:
                try:
                    evt = json.loads(entry)
                    if evt.get("event") == "end-file":
                        return
                except Exception:
                    continue

def show_result_then_return_to_idle():
    """Load result.mp4, wait for it to finish, then restore idle loop—all inside the same mpv."""
    if not os.path.exists(OUTPUT_VIDEO):
        return
    # play result once
    mpv_send({"command": ["set", "loop-file", "no"]})
    mpv_send({"command": ["loadfile", OUTPUT_VIDEO, "replace"]})
    # wait for it to finish
    mpv_wait_for_endfile()
    # back to idle looping
    mpv_send({"command": ["set", "loop-file", "inf"]})
    mpv_send({"command": ["loadfile", IDLE_VIDEO, "replace"]})

# -------- Audio / Wake --------
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

# -------- Network --------
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

# -------- Main loop --------
def run_client():
    start_mpv_idle()            # mpv owns the screen, loops idle rotated
    while True:
        listen_for_wake_word()  # idle keeps showing underneath
        record_user_input()
        if send_audio_to_server():
            show_result_then_return_to_idle()

if __name__ == "__main__":
    run_client()
