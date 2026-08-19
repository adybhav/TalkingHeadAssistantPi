import os
import time
import contextlib

from modules.llm_provider import generate_response
#from modules.lipsync import run_lipsync
from musetalk_runner import run_lipsync


USE_OLLAMA = False


# THIS IS A TEST FILE FOR TESTING THE LLM and Video Generation on local.
@contextlib.contextmanager
def suppress_console_output():
    with open(os.devnull, "w", encoding="utf-8") as devnull:
        with contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
            yield


# Suppress TTS model initialization messages
with suppress_console_output():
    from modules.tts import text_to_speech


def medusa_loop():
    start_time = time.time()
    print("🎙️ done listening")

    transcript = "What is the temperature in Philadelphia right mow? Should I wear a jacket?"
    response = "What is the temperature in Philadelphia right mow? Should I wear a jacket?"# generate_response(transcript, use_ollama=USE_OLLAMA)

    with suppress_console_output():
        text_to_speech(response, "./output_audio.wav")

    run_lipsync(
        "./idle_720p.mp4",
        "./output_audio.wav",
        "./result.mp4",
    )

    total_time = time.time() - start_time
    print(f"\n🕒 Total generation time: {total_time:.2f} seconds")


if __name__ == "__main__":
    medusa_loop()
