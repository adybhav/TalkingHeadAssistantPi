import subprocess

def run_lipsync(image_path, audio_path, output_path):
    command = [
        "python", "Wav2Lip/inference.py",
        "--checkpoint_path", "checkpoints/wav2lip_gan.pth",
        "--face", image_path,
        "--audio", audio_path,
        "--outfile", output_path,
        "--pads", "0", "0", "0", "0",
        "--nosmooth"
    ]
    subprocess.run(command)
