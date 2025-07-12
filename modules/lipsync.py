import subprocess
import os

def run_lipsync(video_path, audio_path, output_path):
    wav2lip_python = r"C:\Projects\Wav2Lip\venv\Scripts\python.exe"
    wav2lip_script = r"C:\Projects\Wav2Lip\inference.py"
    checkpoint = r"C:\Projects\Wav2Lip\checkpoints\wav2lip_gan.pth"

    command = [
        wav2lip_python,
        wav2lip_script,
        "--checkpoint_path", checkpoint,
        "--face", os.path.abspath(video_path),
        "--audio", os.path.abspath(audio_path),
        "--outfile", os.path.abspath(output_path),
        "--nosmooth",
       "--static", "True"
    ]

    subprocess.run(command)
