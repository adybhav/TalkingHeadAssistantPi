import speech_recognition as sr

def wait_for_wake_and_record(audio_path, wake_phrases, phrase_time_limit=10):
    recognizer = sr.Recognizer()
    mic = sr.Microphone()


    while True:
        with mic as source:
            recognizer.adjust_for_ambient_noise(source)
            try:
                print("🟡 Waiting for wake word...")
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=3)
                wake_transcript = recognizer.recognize_google(audio).lower()
                print(f"🔎 Heard: {wake_transcript}")
                if any(phrase in wake_transcript for phrase in wake_phrases):
                    print("🟢 Wake phrase detected!")
                    break
            except sr.UnknownValueError:
                continue
            except sr.WaitTimeoutError:
                continue

    print("🎙️ Listening... Speak now!")
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source, timeout=None, phrase_time_limit=phrase_time_limit)

    with open(audio_path, "wb") as f:
        f.write(audio.get_wav_data())
