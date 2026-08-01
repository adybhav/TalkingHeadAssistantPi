import os
import subprocess

def run_lipsync(video_path, audio_path, output_path):
    # Paths
    wav2lip_python = r"C:\Projects\Wav2Lip\venv\Scripts\python.exe"
    wav2lip_script = r"C:\Projects\Wav2Lip\inference.py"
    checkpoint = r"C:\Projects\Wav2Lip\checkpoints\wav2lip_gan.pth"

    # Wav2Lip command
    command = [
        wav2lip_python,
        wav2lip_script,
        "--checkpoint_path", checkpoint,
        "--face", os.path.abspath(video_path),
        "--audio", os.path.abspath(audio_path),
        "--outfile", os.path.abspath(output_path),
        "--nosmooth"
    ]

    # Run Wav2Lip
    subprocess.run(command, check=True,stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)


