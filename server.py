from flask import Flask, request, send_file
from modules.asr import transcribe_audio
from modules.llm import generate_response
from modules.tts import text_to_speech
from modules.lipsync import run_lipsync
import time
import os

app = Flask(__name__)

@app.route('/process', methods=['POST'])
def process_audio():
    file = request.files['audio']
    audio_path = "input_audio.wav"
    output_video_path = "result.mp4"

    file.save(audio_path)
    print("🎧 Received audio, processing...")

    start = time.time()
    transcript = transcribe_audio(audio_path)
    response = generate_response(transcript)
    text_to_speech(response, "output_audio.wav")
    run_lipsync("medusa_01.mp4", "output_audio.wav", output_video_path)
    end = time.time()

    print(f"✅ Generation complete in {end - start:.2f} sec")
    return send_file(output_video_path, mimetype="video/mp4")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
