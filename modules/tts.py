from gtts import gTTS
from pydub import AudioSegment
import os

def text_to_speech(text, out_path):
    # Generate MP3 using gTTS
    tts = gTTS(text=text, lang='en')
    temp_mp3 = out_path.replace(".wav", ".mp3")
    tts.save(temp_mp3)

    # Convert to WAV for Wav2Lip
    sound = AudioSegment.from_mp3(temp_mp3)
    sound.set_frame_rate(16000).set_channels(1).export(out_path, format="wav")

    os.remove(temp_mp3)
    print(f"✅ Generated speech and saved to {out_path}")
