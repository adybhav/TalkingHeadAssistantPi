import speech_recognition as sr
import time
import subprocess
import requests
import os

IDLE_VIDEO = "idle.mp4"
OUTPUT_VIDEO = "result.mp4"
AUDIO_FILE = "input_audio.wav"
WAKE_WORDS = ["hey medusa", "gaze into my eyes"]

SERVER_URL = "http://192.168.1.157:5000/process"  # Replace with actual PC/server IP

def play_video(path):
    # Uses ffplay to play fullscreen, no window border
    subprocess.run(["ffplay", "-loglevel", "quiet", "-autoexit", "-fs", path])

def listen_for_wake_word():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    print("🟡 Waiting for wake word...")

    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        while True:
            try:
                print("🎙️ Listening...")
                audio = recognizer.listen(source, timeout=None, phrase_time_limit=5)
                print("🔍 Recognizing...")
                transcript = recognizer.recognize_google(audio).lower()
                print(f"📢 Heard: {transcript}")
                if any(phrase in transcript for phrase in WAKE_WORDS):
                    print("🟢 Wake word detected!")
                    return
            except sr.UnknownValueError:
                print("🛑 Couldn't understand. Listening again...")
            except sr.RequestError as e:
                print(f"⚠️ Speech recognition error: {e}")
                time.sleep(2)

def record_user_input():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    print("🎙️ Speak your request...")

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
        print("✅ Received result video.")
        return True
    else:
        print(f"❌ Failed to get response: {response.status_code}")
        return False

def run_client():
    while True:
        play_video(IDLE_VIDEO)
        listen_for_wake_word()
        record_user_input()
        if send_audio_to_server():
            play_video(OUTPUT_VIDEO)

if __name__ == "__main__":
    run_client()
