from modules.asr import transcribe_audio, record_audio
from modules.llm import generate_response
from modules.tts import text_to_speech
from modules.lipsync import run_lipsync


AUDIO_PATH = "./input_audio.wav"

# Step 1: Transcribe user input
record_audio(out_path=AUDIO_PATH, duration=4)  # Create the file
transcript = transcribe_audio(AUDIO_PATH)
# Step 2: LLM response
response = generate_response(transcript)

# Step 3: Generate speech from response
text_to_speech(response, "./output_audio.wav")
print("done tts")
# Step 4: Generate talking head video
run_lipsync("./medusa_01.mp4", "./output_audio.wav", "./result.mp4")
