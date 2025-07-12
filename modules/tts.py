import config

from TTS.api import TTS

# Load the YourTTS model (zero-shot voice cloning)
tts = TTS(
    model_name="tts_models/multilingual/multi-dataset/your_tts",
    progress_bar=False
)
tts.to("cuda")  # Use GPU if available

def text_to_speech(text, out_path, speaker_wav="./medusa_audio.wav"):
    tts.tts_to_file(
        text=text,
        speaker_wav=speaker_wav,
        language="en",
        file_path=out_path
    )
