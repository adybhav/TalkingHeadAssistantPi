from flask import Flask, request, send_file
from modules.asr import transcribe_audio
from modules.llm_provider import generate_response
from modules.tts import text_to_speech
from musetalk_runner import preload_worker, run_lipsync
import time
import wave

app = Flask(__name__)

RESPONSE_AUDIO_PATH = "output_audio.wav"
PADDED_RESPONSE_AUDIO_PATH = "output_audio_padded.wav"
RESPONSE_PREROLL_SECONDS = 1.0
USE_OLLAMA = False

def prepend_silence(input_path, output_path, seconds):
    """Add leading silence so playback devices do not clip the first words."""
    with wave.open(input_path, "rb") as source:
        params = source.getparams()
        audio = source.readframes(source.getnframes())

    silent_frames = int(params.framerate * seconds)
    silence = b"\x00" * silent_frames * params.nchannels * params.sampwidth

    with wave.open(output_path, "wb") as destination:
        destination.setparams(params)
        destination.writeframes(silence + audio)

@app.route('/process', methods=['POST'])
def process_audio():
    file = request.files['audio']
    audio_path = "input_audio.wav"
    output_video_path = "result.mp4"

    file.save(audio_path)
    print("🎧 Received audio, processing...")

    start = time.time()
    transcript = transcribe_audio(audio_path)
    print(transcript)
    response = generate_response(transcript, use_ollama=USE_OLLAMA)
    text_to_speech(response, RESPONSE_AUDIO_PATH)
    prepend_silence(RESPONSE_AUDIO_PATH, PADDED_RESPONSE_AUDIO_PATH, RESPONSE_PREROLL_SECONDS)
    run_lipsync("idle_720p.mp4", PADDED_RESPONSE_AUDIO_PATH, output_video_path)
    end = time.time()

    print(f"✅ Generation complete in {end - start:.2f} sec")
    return send_file(output_video_path, mimetype="video/mp4")

if __name__ == '__main__':
    preload_worker()
    app.run(host="0.0.0.0", port=5000)
