import os
os.environ["ALSA_LOG_LEVEL"] = "none"

import speech_recognition as sr
import time
import subprocess
import requests
import sys
import signal

IDLE_VIDEO = "idle.mp4"
OUTPUT_VIDEO = "result.mp4"
AUDIO_FILE  = "input_audio.wav"
WAKE_WORDS  = ["hey medusa", "gaze into my eyes"]
SERVER_URL  = "http://192.168.1.157:5000/process"

idle_process = None

def start_idle_video():
    """Start looping idle video in the background and keep a handle to it."""
    global idle_process
    # already running?
    if idle_process and idle_process.poll() is None:
        return
    idle_process = subprocess.Popen(
        ["ffplay",
         "-loglevel", "quiet",
         "-fs",                 # fullscreen
         "-nostats", "-hide_banner",
         "-nostdin",            # don't read from terminal
         "-stream_loop", "-1",  # loop forever
         IDLE_VIDEO],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid    # its own session, less likely to lose focus
    )

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
    """Play a single video fullscreen and return when it ends."""
    subprocess.run(
        ["ffplay", "-loglevel", "quiet", "-autoexit", "-fs", "-nostdin", path],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

def listen_for_wake_word():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        while True:
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                transcript = recognizer.recognize_google(audio).lower()
                if any(phrase in transcript for phrase in WAKE_WORDS):
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
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source, timeout=None, phrase_time_limit=10)
    with open(AUDIO_FILE, "wb") as f:
        f.write(audio.get_wav_data())

def send_audio_to_server():
    with open(AUDIO_FILE, "rb") as audio_file:
        r = requests.post(SERVER_URL, files={"audio": audio_file})
    if r.status_code == 200:
        with open(OUTPUT_VIDEO, "wb") as f:
            f.write(r.content)
        return True
    return False

def run_client():
    start_idle_video()  # keep it running continuously
    while True:
        listen_for_wake_word()
        record_user_input()
        # keep idle video running while server processes
        if send_audio_to_server():
            # now stop idle and show the result, then restart idle
            stop_idle_video()
            play_video(OUTPUT_VIDEO)
            start_idle_video()

if __name__ == "__main__":
    run_client()
