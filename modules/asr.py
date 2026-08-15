import sounddevice as sd
from scipy.io.wavfile import write
from faster_whisper import WhisperModel
import os

WHISPER_MODEL_SIZE = "small"
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE_TYPE = "int8"

model = WhisperModel(
    WHISPER_MODEL_SIZE,
    device=WHISPER_DEVICE,
    compute_type=WHISPER_COMPUTE_TYPE,
)

def record_audio(out_path="assets/input_audio.wav", duration=5, fs=16000):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    print(f"🎤 Recording for {duration} seconds...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()
    write(out_path, fs, recording)
    print(f"✅ Saved recording to {out_path}")

def transcribe_audio(audio_path):
    segments, _ = model.transcribe(audio_path)
    return " ".join([s.text for s in segments])
