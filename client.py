import requests
import subprocess

with open("input_audio.wav", "rb") as f:
    files = {'audio': f}
    print("📤 Sending audio to server...")
    r = requests.post("http://192.168.1.157:5000/process", files=files)

if r.status_code == 200:
    with open("received_result.mp4", "wb") as f:
        f.write(r.content)
    print("📥 Video received. Now playing...")

    # Play video and audio using ffplay
    subprocess.run(["ffplay", "-autoexit", "-fs", "received_result.mp4"])
else:
    print(f"❌ Server returned error: {r.status_code}")
