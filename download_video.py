#!/usr/bin/env python3
"""Script para baixar vídeos do YouTube usando yt-dlp."""

import subprocess
import sys
from pathlib import Path


def download_video(url: str, output_dir: str = ".") -> bool:
    """
    Baixa um vídeo do YouTube na melhor qualidade disponível.

    Args:
        url: URL do vídeo do YouTube
        output_dir: Diretório de saída (padrão: diretório atual)

    Returns:
        True se o download foi bem sucedido, False caso contrário
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    cmd = [
        "yt-dlp",
        "-f", "bestvideo+bestaudio/best",
        "--merge-output-format", "mp4",
        "-o", str(output_path / "%(title)s.%(ext)s"),
        "--no-playlist",
        "--progress",
        url
    ]

    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Erro ao baixar vídeo: {e}")
        return False
    except FileNotFoundError:
        print("Erro: yt-dlp não está instalado. Instale com: pip install yt-dlp")
        return False


def main():
    if len(sys.argv) < 2:
        print("Uso: python download_video.py <URL> [diretório_saída]")
        sys.exit(1)

    url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "."

    print(f"Baixando: {url}")
    print(f"Destino: {output_dir}")

    success = download_video(url, output_dir)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
