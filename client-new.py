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
AUDIO_FILE = "input_audio.wav"
WAKE_WORDS = ["hey medusa", "gaze into my eyes"]

SERVER_URL = "http://192.168.1.157:5000/process"  # Replace with actual PC/server IP

idle_process = None
def play_video(path):
    # Uses ffplay to play fullscreen, no window border
    subprocess.Popen(["ffplay", "-loglevel", "quiet", "-autoexit", "-fs", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,stdin=subprocess.DEVNULL)

def play_idle_video(path):
    global idle_process
    subprocess.Popen(["ffplay", "-loglevel", "quiet", "-autoexit", "-fs", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
def stop_idle_video(path):
    global idle_process
    if idle_process and idle_process.poll() is None:
        idle_process.send_signal(signal.SIGINT)
        idle_process.wait()
        idle_process = None

def listen_for_wake_word():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    '''print("🟡 Waiting for wake word..")'''

    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        while True:
            try:
                '''print("🎙️ Listening..")'''
                audio = recognizer.listen(source, timeout=None, phrase_time_limit=5)
                '''print("🔍 Recognizing..")'''
                transcript = recognizer.recognize_google(audio).lower()
                '''print(f"📢 Heard: {transcript")'''
                if any(phrase in transcript for phrase in WAKE_WORDS):
                    '''print("🟢 Wake word detected")'''
                    return
            except sr.UnknownValueError:
                '''print("🛑 Couldn't understand. Listening again..")'''
            except sr.RequestError as e:
                '''print(f"⚠️ Speech recognition error: {e}")'''
                time.sleep(2)

def record_user_input():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    '''print("🎙️ Speak your request..")'''

    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source, timeout=None, phrase_time_limit=10)

    with open(AUDIO_FILE, "wb") as f:
        f.write(audio.get_wav_data())

def send_audio_to_server():
    with open(AUDIO_FILE, "rb") as audio_file:
        response = requests.post(SERVER_URL, files={"audio": audio_file})

    if response.status_code == 200:
        with open(OUTPUT_VIDEO, "wb") as f:
            f.write(response.content)
        '''print("✅ Received result video.")'''
        return True
    else:
        '''print(f"❌ Failed to get response: {response.status_code}")'''
        return False

def suppressalsa():
    sys.sderr = open(os.devnull,'w')

def run_client():
    while True:
        suppressalsa()
        play_idle_video(IDLE_VIDEO)
        listen_for_wake_word()
        record_user_input()
        stop_idle_video(IDLE_VIDEO)
        if send_audio_to_server():
            play_video(OUTPUT_VIDEO)

if __name__ == "__main__":
    run_client()
