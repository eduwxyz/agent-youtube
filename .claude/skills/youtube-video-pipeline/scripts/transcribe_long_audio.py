#!/usr/bin/env python3
"""
Script para transcrever áudios muito longos dividindo em chunks.
Resolve o problema de CUDA out of memory para vídeos > 30 minutos.

Uso:
    python transcribe_long_audio.py audio.mp3 -o transcricao.txt
"""

import subprocess
import sys
import os
import tempfile
import json
from pathlib import Path


def get_audio_duration(audio_path: str) -> float:
    """Retorna a duração do áudio em segundos."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())


def split_audio(audio_path: str, chunk_duration: int = 600, output_dir: str = None) -> list:
    """
    Divide o áudio em chunks.

    Args:
        audio_path: Caminho do áudio
        chunk_duration: Duração de cada chunk em segundos (padrão: 600 = 10 min)
        output_dir: Diretório para os chunks

    Returns:
        Lista de caminhos dos chunks
    """
    audio_path = Path(audio_path)
    total_duration = get_audio_duration(str(audio_path))

    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="audio_chunks_")
    else:
        os.makedirs(output_dir, exist_ok=True)

    chunks = []
    start = 0
    chunk_num = 1

    print(f"Dividindo áudio de {total_duration:.0f}s em chunks de {chunk_duration}s...")

    while start < total_duration:
        chunk_path = Path(output_dir) / f"chunk_{chunk_num:03d}.wav"

        # Converter para WAV 16kHz mono durante o split
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start),
            "-i", str(audio_path),
            "-t", str(chunk_duration),
            "-ar", "16000",
            "-ac", "1",
            str(chunk_path)
        ]

        subprocess.run(cmd, capture_output=True, text=True)

        if chunk_path.exists():
            chunks.append({
                "path": str(chunk_path),
                "start_time": start,
                "chunk_num": chunk_num
            })
            print(f"  Chunk {chunk_num}: {start:.0f}s - {min(start + chunk_duration, total_duration):.0f}s")

        start += chunk_duration
        chunk_num += 1

    return chunks


def transcribe_chunk(chunk_path: str, model) -> dict:
    """Transcreve um chunk e retorna texto + timestamps."""
    output = model.transcribe([chunk_path], timestamps=True)

    text = output[0].text
    timestamps = []

    if hasattr(output[0], 'timestamp'):
        segment_timestamps = output[0].timestamp.get('segment', [])
        for stamp in segment_timestamps:
            timestamps.append({
                "start": stamp['start'],
                "end": stamp['end'],
                "text": stamp['segment']
            })

    return {"text": text, "timestamps": timestamps}


def transcribe_long_audio(
    audio_path: str,
    output_file: str = None,
    chunk_duration: int = 600,
    model_name: str = "nvidia/parakeet-tdt-0.6b-v3"
) -> str:
    """
    Transcreve áudio longo dividindo em chunks.

    Args:
        audio_path: Caminho do áudio
        output_file: Arquivo de saída
        chunk_duration: Duração de cada chunk (segundos)
        model_name: Modelo a usar

    Returns:
        Transcrição completa
    """
    import nemo.collections.asr as nemo_asr

    audio_path = Path(audio_path)

    if not audio_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {audio_path}")

    total_duration = get_audio_duration(str(audio_path))
    print(f"Duração total: {total_duration/60:.1f} minutos")

    # Dividir em chunks
    chunks = split_audio(str(audio_path), chunk_duration)
    print(f"Total de chunks: {len(chunks)}")

    # Carregar modelo
    print(f"\nCarregando modelo {model_name}...")
    asr_model = nemo_asr.models.ASRModel.from_pretrained(model_name=model_name)

    # Habilitar atenção local para chunks longos
    asr_model.change_attention_model(
        self_attention_model="rel_pos_local_attn",
        att_context_size=[256, 256]
    )

    # Transcrever cada chunk
    full_text = []
    all_timestamps = []

    for chunk in chunks:
        print(f"\nTranscrevendo chunk {chunk['chunk_num']}/{len(chunks)}...")

        try:
            result = transcribe_chunk(chunk['path'], asr_model)
            full_text.append(result['text'])

            # Ajustar timestamps com offset do chunk
            offset = chunk['start_time']
            for ts in result['timestamps']:
                all_timestamps.append({
                    "start": ts['start'] + offset,
                    "end": ts['end'] + offset,
                    "text": ts['text']
                })

            print(f"  OK - {len(result['text'])} caracteres")

        except Exception as e:
            print(f"  ERRO: {e}")
            full_text.append(f"[ERRO NO CHUNK {chunk['chunk_num']}]")

        # Limpar arquivo temporário
        try:
            os.unlink(chunk['path'])
        except:
            pass

    # Montar transcrição final
    transcription = " ".join(full_text)

    # Salvar resultado
    if output_file:
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(transcription)
            f.write("\n\n--- Timestamps ---\n")
            for ts in all_timestamps:
                f.write(f"{ts['start']:.2f}s - {ts['end']:.2f}s : {ts['text']}\n")
        print(f"\nTranscrição salva em: {output_path}")

    print(f"\nTranscrição completa: {len(transcription)} caracteres")
    print(f"Total de segmentos com timestamp: {len(all_timestamps)}")

    return transcription


def main():
    if len(sys.argv) < 2:
        print("Uso: python transcribe_long_audio.py <audio.mp3> [opções]")
        print()
        print("Opções:")
        print("  -o, --output <arquivo>   Salvar transcrição em arquivo")
        print("  -c, --chunk <segundos>   Duração de cada chunk (padrão: 600 = 10 min)")
        print("  -m, --model <nome>       Modelo a usar")
        print()
        print("Exemplo:")
        print("  python transcribe_long_audio.py live.mp3 -o transcricao.txt")
        sys.exit(1)

    audio_path = sys.argv[1]
    output_file = None
    chunk_duration = 600
    model_name = "nvidia/parakeet-tdt-0.6b-v3"

    # Parse argumentos
    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] in ("-o", "--output"):
            output_file = args[i + 1]
            i += 2
        elif args[i] in ("-c", "--chunk"):
            chunk_duration = int(args[i + 1])
            i += 2
        elif args[i] in ("-m", "--model"):
            model_name = args[i + 1]
            i += 2
        else:
            i += 1

    transcribe_long_audio(
        audio_path,
        output_file=output_file,
        chunk_duration=chunk_duration,
        model_name=model_name
    )


if __name__ == "__main__":
    main()
