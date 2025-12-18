#!/usr/bin/env python3
"""
Script para extrair clipes/cortes de vídeos usando timestamps.
Usa ffmpeg para cortar sem recodificar (quando possível).

Uso:
    python extract_clip.py video.mp4 --start 125.5 --end 245.8 -o corte1.mp4
    python extract_clip.py video.mp4 --start 2:05 --end 4:05 -o corte1.mp4
    python extract_clip.py video.mp4 --clips clips.json
"""

import subprocess
import sys
import json
import re
from pathlib import Path
from typing import Optional


def parse_timestamp(timestamp: str) -> float:
    """
    Converte timestamp para segundos.

    Aceita formatos:
    - 125.5 (segundos)
    - 2:05 (minutos:segundos)
    - 1:02:05 (horas:minutos:segundos)

    Returns:
        Tempo em segundos (float)
    """
    timestamp = str(timestamp).strip()

    # Se já é um número (segundos)
    if re.match(r'^[\d.]+$', timestamp):
        return float(timestamp)

    # Formato HH:MM:SS ou MM:SS
    parts = timestamp.split(':')
    if len(parts) == 2:
        minutes, seconds = parts
        return int(minutes) * 60 + float(seconds)
    elif len(parts) == 3:
        hours, minutes, seconds = parts
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)

    raise ValueError(f"Formato de timestamp inválido: {timestamp}")


def format_duration(seconds: float) -> str:
    """Formata segundos para MM:SS ou HH:MM:SS."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def extract_clip(
    video_path: str,
    start_seconds: float,
    end_seconds: float,
    output_path: Optional[str] = None,
    reencode: bool = False
) -> str:
    """
    Extrai um clipe do vídeo usando ffmpeg.

    Args:
        video_path: Caminho do vídeo original
        start_seconds: Tempo de início em segundos
        end_seconds: Tempo de fim em segundos
        output_path: Caminho do arquivo de saída (opcional)
        reencode: Se True, recodifica o vídeo (mais lento, cortes mais precisos)

    Returns:
        Caminho do arquivo de saída
    """
    video_path = Path(video_path)

    if not video_path.exists():
        raise FileNotFoundError(f"Vídeo não encontrado: {video_path}")

    duration = end_seconds - start_seconds
    if duration <= 0:
        raise ValueError(f"Duração inválida: início={start_seconds}s, fim={end_seconds}s")

    # Gerar nome de saída se não especificado
    if output_path is None:
        start_str = format_duration(start_seconds).replace(':', '-')
        end_str = format_duration(end_seconds).replace(':', '-')
        output_path = video_path.parent / f"{video_path.stem}_clip_{start_str}_to_{end_str}{video_path.suffix}"
    else:
        output_path = Path(output_path)

    # Garantir que o diretório de saída existe
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Extraindo clipe:")
    print(f"  Origem: {video_path}")
    print(f"  Início: {format_duration(start_seconds)} ({start_seconds:.2f}s)")
    print(f"  Fim: {format_duration(end_seconds)} ({end_seconds:.2f}s)")
    print(f"  Duração: {format_duration(duration)}")
    print(f"  Saída: {output_path}")

    if reencode:
        # Recodifica - mais lento, mas cortes precisos no frame
        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-ss", str(start_seconds),
            "-t", str(duration),
            "-c:v", "libx264",
            "-c:a", "aac",
            "-y",
            str(output_path)
        ]
    else:
        # Cópia direta - mais rápido, corte no keyframe mais próximo
        # -ss antes de -i para seek rápido
        cmd = [
            "ffmpeg",
            "-ss", str(start_seconds),
            "-i", str(video_path),
            "-t", str(duration),
            "-c", "copy",
            "-avoid_negative_ts", "make_zero",
            "-y",
            str(output_path)
        ]

    print(f"\nExecutando ffmpeg...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Erro no ffmpeg: {result.stderr}")
        raise RuntimeError(f"Falha ao extrair clipe: {result.stderr}")

    print(f"Clipe extraído com sucesso: {output_path}")
    return str(output_path)


def extract_clips_from_json(video_path: str, json_path: str, output_dir: Optional[str] = None) -> list:
    """
    Extrai múltiplos clipes baseado em um arquivo JSON.

    O JSON deve ter o formato:
    {
        "cortes": [
            {
                "numero": 1,
                "inicio_segundos": 125.5,
                "fim_segundos": 245.8,
                "titulo_sugerido": "Título do corte"
            }
        ]
    }

    Args:
        video_path: Caminho do vídeo original
        json_path: Caminho do arquivo JSON com os cortes
        output_dir: Diretório de saída (opcional)

    Returns:
        Lista de caminhos dos arquivos gerados
    """
    video_path = Path(video_path)
    json_path = Path(json_path)

    if not json_path.exists():
        raise FileNotFoundError(f"Arquivo JSON não encontrado: {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    cortes = data.get('cortes', [])
    if not cortes:
        print("Nenhum corte encontrado no JSON.")
        return []

    if output_dir:
        output_dir = Path(output_dir)
    else:
        output_dir = video_path.parent / "clips"

    output_dir.mkdir(parents=True, exist_ok=True)

    outputs = []
    print(f"\nExtraindo {len(cortes)} clipes...")
    print(f"Diretório de saída: {output_dir}\n")

    for corte in cortes:
        numero = corte.get('numero', len(outputs) + 1)
        inicio = corte['inicio_segundos']
        fim = corte['fim_segundos']
        titulo = corte.get('titulo_sugerido', f'clip_{numero}')

        # Sanitizar título para nome de arquivo
        safe_title = re.sub(r'[^\w\s-]', '', titulo)[:50].strip()
        safe_title = re.sub(r'[-\s]+', '_', safe_title)

        output_path = output_dir / f"{numero:02d}_{safe_title}{video_path.suffix}"

        print(f"\n{'='*50}")
        print(f"Corte {numero}: {titulo}")

        try:
            result = extract_clip(
                str(video_path),
                inicio,
                fim,
                str(output_path)
            )
            outputs.append(result)
        except Exception as e:
            print(f"Erro ao extrair corte {numero}: {e}")

    print(f"\n{'='*50}")
    print(f"Extração concluída: {len(outputs)}/{len(cortes)} clipes")

    return outputs


def main():
    if len(sys.argv) < 2:
        print("Uso: python extract_clip.py <video.mp4> [opções]")
        print()
        print("Modo único (extrair um clipe):")
        print("  python extract_clip.py video.mp4 --start 125.5 --end 245.8")
        print("  python extract_clip.py video.mp4 --start 2:05 --end 4:05 -o corte.mp4")
        print()
        print("Modo batch (extrair múltiplos clipes de JSON):")
        print("  python extract_clip.py video.mp4 --clips cortes.json")
        print("  python extract_clip.py video.mp4 --clips cortes.json --output-dir ./clips")
        print()
        print("Opções:")
        print("  --start <tempo>      Tempo de início (segundos ou MM:SS)")
        print("  --end <tempo>        Tempo de fim (segundos ou MM:SS)")
        print("  -o, --output <arq>   Arquivo de saída")
        print("  --clips <json>       Arquivo JSON com lista de cortes")
        print("  --output-dir <dir>   Diretório de saída para modo batch")
        print("  --reencode           Recodificar vídeo (mais lento, cortes precisos)")
        print()
        print("Formato do JSON para modo batch:")
        print('  {"cortes": [{"inicio_segundos": 10, "fim_segundos": 60, "titulo_sugerido": "Título"}]}')
        sys.exit(1)

    video_path = sys.argv[1]
    args = sys.argv[2:]

    # Parse argumentos
    start = None
    end = None
    output = None
    clips_json = None
    output_dir = None
    reencode = False

    i = 0
    while i < len(args):
        if args[i] == "--start":
            start = parse_timestamp(args[i + 1])
            i += 2
        elif args[i] == "--end":
            end = parse_timestamp(args[i + 1])
            i += 2
        elif args[i] in ("-o", "--output"):
            output = args[i + 1]
            i += 2
        elif args[i] == "--clips":
            clips_json = args[i + 1]
            i += 2
        elif args[i] == "--output-dir":
            output_dir = args[i + 1]
            i += 2
        elif args[i] == "--reencode":
            reencode = True
            i += 1
        else:
            i += 1

    # Modo batch (JSON)
    if clips_json:
        outputs = extract_clips_from_json(video_path, clips_json, output_dir)
        print(f"\nArquivos gerados:")
        for out in outputs:
            print(f"  - {out}")

    # Modo único
    elif start is not None and end is not None:
        extract_clip(video_path, start, end, output, reencode)

    else:
        print("Erro: Especifique --start e --end, ou use --clips com um JSON")
        sys.exit(1)


if __name__ == "__main__":
    main()
