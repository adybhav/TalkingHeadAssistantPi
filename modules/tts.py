import os

from TTS.api import TTS


TTS_MODEL_NAME = os.getenv(
    "TTS_MODEL_NAME",
    "tts_models/multilingual/multi-dataset/your_tts",
)
TTS_DEVICE = os.getenv("TTS_DEVICE", "cuda")


def _load_tts():
    """Load the voice-cloning model and move it to the requested device."""
    engine = TTS(
        model_name=TTS_MODEL_NAME,
        progress_bar=False,
    )
    try:
        engine.to(TTS_DEVICE)
    except Exception:
        if TTS_DEVICE != "cpu":
            engine.to("cpu")
        else:
            raise
    return engine


tts = _load_tts()

def text_to_speech(text, out_path, speaker_wav="./medusa_audio.wav"):
    tts.tts_to_file(
        text=text,
        speaker_wav=speaker_wav,
        language="en",
        file_path=out_path
    )
