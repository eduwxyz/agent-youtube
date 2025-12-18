#!/usr/bin/env python3
"""
Script para transcrever áudio MP3 em chunks de 6 minutos usando NVIDIA Parakeet TDT v3.
Otimizado para máximo uso de GPU através de batch processing.

Uso: python transcribe_chunks.py <arquivo.mp3> [-o output.txt]
"""

import subprocess
import sys
import os
import tempfile
import shutil
from pathlib import Path
import torch


def get_audio_duration(audio_path: str) -> float:
    """Retorna a duração do áudio em segundos usando ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(audio_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())


def split_audio_into_chunks(
    audio_path: str,
    chunk_duration: int = 360,  # 6 minutos em segundos
    output_dir: str = None
) -> list[str]:
    """
    Divide o áudio em chunks de duração especificada.

    Args:
        audio_path: Caminho para o arquivo de áudio
        chunk_duration: Duração de cada chunk em segundos (padrão: 360 = 6 min)
        output_dir: Diretório para salvar os chunks

    Returns:
        Lista de caminhos dos chunks gerados
    """
    audio_path = Path(audio_path)

    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="audio_chunks_")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Obter duração total
    total_duration = get_audio_duration(str(audio_path))
    print(f"Duração total do áudio: {total_duration:.1f}s ({total_duration/60:.1f} min)")

    # Calcular número de chunks
    num_chunks = int(total_duration // chunk_duration) + (1 if total_duration % chunk_duration > 0 else 0)
    print(f"Dividindo em {num_chunks} chunks de {chunk_duration}s ({chunk_duration/60:.1f} min) cada...")

    chunk_paths = []

    for i in range(num_chunks):
        start_time = i * chunk_duration
        chunk_path = output_dir / f"chunk_{i:04d}.wav"

        cmd = [
            "ffmpeg",
            "-i", str(audio_path),
            "-ss", str(start_time),
            "-t", str(chunk_duration),
            "-ar", "16000",  # 16kHz para o modelo
            "-ac", "1",       # Mono
            "-y",
            str(chunk_path)
        ]

        subprocess.run(cmd, check=True, capture_output=True, text=True)
        chunk_paths.append(str(chunk_path))
        print(f"  Chunk {i+1}/{num_chunks}: {start_time}s - {min(start_time + chunk_duration, total_duration):.1f}s")

    return chunk_paths


def transcribe_chunks_batch(
    chunk_paths: list[str],
    model_name: str = "nvidia/parakeet-tdt-0.6b-v3",
    batch_size: int = None
) -> list[str]:
    """
    Transcreve múltiplos chunks usando batch processing para máximo uso de GPU.

    Args:
        chunk_paths: Lista de caminhos dos chunks
        model_name: Nome do modelo Parakeet
        batch_size: Tamanho do batch (auto-detectado se None)

    Returns:
        Lista de transcrições na mesma ordem dos chunks
    """
    import nemo.collections.asr as nemo_asr
    import gc

    # Verificar GPU disponível
    use_gpu = torch.cuda.is_available()
    if use_gpu:
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"GPU detectada: {gpu_name} ({gpu_memory:.1f} GB)")
        batch_size = 1  # Forçar batch=1 para estabilidade
        print(f"Usando batch size: {batch_size} (um chunk por vez)")
    else:
        print("AVISO: GPU não detectada, usando CPU (será mais lento)")
        batch_size = 1

    transcriptions = []
    total_chunks = len(chunk_paths)

    # Processar um chunk por vez, recarregando modelo para evitar memory leak
    for i, chunk_path in enumerate(chunk_paths):
        print(f"Transcrevendo chunk {i + 1}/{total_chunks}...")

        # Carregar modelo fresco para cada chunk
        asr_model = nemo_asr.models.ASRModel.from_pretrained(model_name=model_name)
        if use_gpu:
            asr_model = asr_model.cuda()

        # Transcrever
        outputs = asr_model.transcribe([chunk_path])
        transcriptions.append(outputs[0].text)

        # Limpar completamente
        del asr_model
        gc.collect()
        if use_gpu:
            torch.cuda.empty_cache()
            torch.cuda.synchronize()

    return transcriptions


def transcribe_audio_chunked(
    audio_path: str,
    output_file: str = None,
    chunk_duration: int = 360,
    model_name: str = "nvidia/parakeet-tdt-0.6b-v3",
    batch_size: int = None,
    keep_chunks: bool = False
) -> str:
    """
    Transcreve um arquivo de áudio dividindo em chunks.

    Args:
        audio_path: Caminho para o arquivo MP3
        output_file: Arquivo para salvar a transcrição
        chunk_duration: Duração de cada chunk em segundos
        model_name: Nome do modelo
        batch_size: Tamanho do batch para GPU
        keep_chunks: Se True, mantém os chunks temporários

    Returns:
        Transcrição completa
    """
    audio_path = Path(audio_path)

    if not audio_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {audio_path}")

    if audio_path.suffix.lower() != ".mp3":
        raise ValueError(f"Esperado arquivo MP3, recebido: {audio_path.suffix}")

    # Criar diretório temporário para chunks
    temp_dir = tempfile.mkdtemp(prefix="transcribe_chunks_")

    try:
        # 1. Dividir áudio em chunks
        print("\n=== Etapa 1: Dividindo áudio em chunks ===")
        chunk_paths = split_audio_into_chunks(
            str(audio_path),
            chunk_duration=chunk_duration,
            output_dir=temp_dir
        )

        # 2. Transcrever chunks com batch processing
        print("\n=== Etapa 2: Transcrevendo chunks (GPU batch) ===")
        transcriptions = transcribe_chunks_batch(
            chunk_paths,
            model_name=model_name,
            batch_size=batch_size
        )

        # 3. Juntar transcrições
        print("\n=== Etapa 3: Juntando transcrições ===")
        full_transcription = " ".join(transcriptions)

        # 4. Salvar resultado
        if output_file is None:
            output_file = audio_path.with_suffix(".txt")

        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_transcription)

        print(f"\nTranscrição salva em: {output_path}")
        print(f"Total de caracteres: {len(full_transcription)}")

        return full_transcription

    finally:
        # Limpar arquivos temporários
        if not keep_chunks and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print("Chunks temporários removidos.")


def main():
    if len(sys.argv) < 2:
        print("Uso: python transcribe_chunks.py <arquivo.mp3> [opções]")
        print()
        print("Opções:")
        print("  -o, --output <arquivo>    Salvar transcrição em arquivo")
        print("  -c, --chunk <segundos>    Duração do chunk (padrão: 360 = 6 min)")
        print("  -b, --batch <tamanho>     Tamanho do batch GPU (auto-detectado)")
        print("  -k, --keep-chunks         Manter chunks temporários")
        print("  -m, --model <nome>        Modelo (padrão: nvidia/parakeet-tdt-0.6b-v3)")
        print()
        print("Exemplo:")
        print("  python transcribe_chunks.py video.mp3 -o transcricao.txt")
        sys.exit(1)

    audio_path = sys.argv[1]
    output_file = None
    chunk_duration = 360  # 6 minutos
    batch_size = None
    keep_chunks = False
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
        elif args[i] in ("-b", "--batch"):
            batch_size = int(args[i + 1])
            i += 2
        elif args[i] in ("-k", "--keep-chunks"):
            keep_chunks = True
            i += 1
        elif args[i] in ("-m", "--model"):
            model_name = args[i + 1]
            i += 2
        else:
            i += 1

    transcription = transcribe_audio_chunked(
        audio_path,
        output_file=output_file,
        chunk_duration=chunk_duration,
        model_name=model_name,
        batch_size=batch_size,
        keep_chunks=keep_chunks
    )

    print("\n=== Transcrição Completa ===")
    # Mostrar apenas preview se muito longo
    if len(transcription) > 500:
        print(transcription[:500] + "...")
        print(f"\n[... {len(transcription) - 500} caracteres restantes no arquivo de saída]")
    else:
        print(transcription)


if __name__ == "__main__":
    main()
