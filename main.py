from modules.asr import transcribe_audio, record_audio
from modules.llm import generate_response
from modules.tts import text_to_speech
from modules.lipsync import run_lipsync
from waitandwake import wait_for_wake_and_record
import time

def medusa_loop():
    while True:
        AUDIO_PATH = "./input_audio.wav"

        wait_for_wake_and_record(AUDIO_PATH, wake_phrases=["hey medusa", "gaze into my eyes", "hey assistant"])
        start_time = time.time()  # START TIMER
        print("🎙️ done listening")

        transcript = transcribe_audio(AUDIO_PATH)
        # Step 2: LLM response
        response = generate_response(transcript)

        # Step 3: Generate speech from response
        text_to_speech(response, "./output_audio.wav")
        # Step 4: Generate talking head video
        run_lipsync("./medusa_01.mp4", "./output_audio.wav", "./result.mp4")
        end_time = time.time()  # END TIMER
        total_time = end_time - start_time
        print(f"\n🕒 Total generation time: {total_time:.2f} seconds")

if __name__ == "__main__":
    medusa_loop()