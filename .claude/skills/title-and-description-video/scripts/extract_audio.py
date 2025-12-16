#!/usr/bin/env python3
"""Extrai áudio de arquivos MP4 usando ffmpeg."""

import subprocess
import sys
from pathlib import Path


def extract_audio(video_path: str, output_path: str = None) -> str:
    """
    Extrai o áudio de um arquivo de vídeo MP4.

    Args:
        video_path: Caminho para o arquivo de vídeo MP4
        output_path: Caminho para o arquivo de áudio de saída (opcional)

    Returns:
        Caminho do arquivo de áudio gerado
    """
    video_path = Path(video_path)

    if not video_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {video_path}")

    if output_path is None:
        output_path = video_path.with_suffix(".mp3")
    else:
        output_path = Path(output_path)

    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-vn",
        "-acodec", "libmp3lame",
        "-y",
        str(output_path)
    ]

    print(f"Extraindo áudio de: {video_path}")
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    print(f"Áudio extraído: {output_path}")
    return str(output_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python extract_audio.py <video.mp4> [output.mp3]")
        sys.exit(1)

    video = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else None
    extract_audio(video, output)
