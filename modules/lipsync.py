import subprocess
import os

def run_lipsync(image_path, audio_path, output_path):
    wav2lip_path = "C:/Projects/Wav2Lip/inference.py"  # ✅ adjust this to your cloned repo
    checkpoint_path = "C:/Projects/Wav2Lip/checkpoints/wav2lip_gan.pth"  # ✅ full path to checkpoint

    #video
    # command = [
    #     "python", wav2lip_path,
    #     "--checkpoint_path", checkpoint_path,
    #     "--face", image_path,
    #     "--audio", audio_path,
    #     "--outfile", output_path,
    #     "--pads", "0", "0", "0", "0",
    #     "--nosmooth"
    # ]

    #static
    command = [
        "python", wav2lip_path,
        "--checkpoint_path", checkpoint_path,
        "--face", image_path,
        "--audio", audio_path,
        "--outfile", output_path,
        "--pads", "0", "0", "0", "0",
        "--nosmooth",
        "--static" ,"True" # ✅ Required when input is a single image
    ]

    subprocess.run(command)
