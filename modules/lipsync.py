import subprocess
import os

import os
import subprocess

def run_lipsync(video_path, audio_path, output_path):
    # Paths
    wav2lip_python = r"C:\Projects\Wav2Lip\venv\Scripts\python.exe"
    wav2lip_script = r"C:\Projects\Wav2Lip\inference.py"
    checkpoint = r"C:\Projects\Wav2Lip\checkpoints\wav2lip_gan.pth"

    # Resize the input video to 1280x720 using ffmpeg
    resized_video_path = os.path.splitext(video_path)[0] + "_720p.mp4"
    resize_cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", "scale=720:1280",
        resized_video_path
    ]
    subprocess.run(resize_cmd, check=True)

    # Wav2Lip command
    command = [
        wav2lip_python,
        wav2lip_script,
        "--checkpoint_path", checkpoint,
        "--face", os.path.abspath(resized_video_path),
        "--audio", os.path.abspath(audio_path),
        "--outfile", os.path.abspath(output_path),
        "--nosmooth",
        "--static", "True",
        "--resize_factor", "2"
    ]

    # Run Wav2Lip
    subprocess.run(command, check=True)
