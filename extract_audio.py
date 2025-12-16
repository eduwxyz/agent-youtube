#!/usr/bin/env python3
"""
Script para extrair áudio de arquivos de vídeo MP4.
Requer ffmpeg instalado no sistema.
"""

import subprocess
import sys
import os
from pathlib import Path


def extract_audio(video_path: str, output_path: str = None, audio_format: str = "mp3") -> str:
    """
    Extrai o áudio de um arquivo de vídeo.

    Args:
        video_path: Caminho para o arquivo de vídeo MP4
        output_path: Caminho para o arquivo de áudio de saída (opcional)
        audio_format: Formato do áudio de saída (mp3, wav, aac, etc.)

    Returns:
        Caminho do arquivo de áudio gerado
    """
    video_path = Path(video_path)

    if not video_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {video_path}")

    if output_path is None:
        output_path = video_path.with_suffix(f".{audio_format}")
    else:
        output_path = Path(output_path)

    # Comando ffmpeg para extrair áudio
    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-vn",  # Sem vídeo
        "-acodec", "libmp3lame" if audio_format == "mp3" else "copy",
        "-y",  # Sobrescrever arquivo existente
        str(output_path)
    ]

    print(f"Extraindo áudio de: {video_path}")
    print(f"Salvando em: {output_path}")

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"Áudio extraído com sucesso: {output_path}")
        return str(output_path)
    except subprocess.CalledProcessError as e:
        print(f"Erro ao extrair áudio: {e.stderr}")
        raise
    except FileNotFoundError:
        print("Erro: ffmpeg não encontrado. Instale com: brew install ffmpeg")
        raise


def main():
    if len(sys.argv) < 2:
        print("Uso: python extract_audio.py <caminho_video.mp4> [caminho_saida] [formato]")
        print("Exemplo: python extract_audio.py video.mp4")
        print("Exemplo: python extract_audio.py video.mp4 audio.mp3")
        print("Exemplo: python extract_audio.py video.mp4 audio.wav wav")
        sys.exit(1)

    video_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    audio_format = sys.argv[3] if len(sys.argv) > 3 else "mp3"

    extract_audio(video_path, output_path, audio_format)


if __name__ == "__main__":
    main()
