#!/usr/bin/env python3
"""
Script para transcrever áudio MP3 usando o modelo NVIDIA Parakeet TDT v3.
Suporta 25 idiomas europeus com detecção automática de idioma.

Idiomas suportados:
bg, hr, cs, da, nl, en, et, fi, fr, de, el, hu, it, lv, lt, mt, pl, pt, ro, sk, sl, es, sv, ru, uk

Requer: pip install nemo_toolkit[asr]
"""

import subprocess
import sys
import os
import tempfile
from pathlib import Path


def convert_mp3_to_wav(mp3_path: str, wav_path: str = None) -> str:
    """
    Converte MP3 para WAV 16kHz mono (formato esperado pelo modelo).

    Args:
        mp3_path: Caminho para o arquivo MP3
        wav_path: Caminho para o arquivo WAV de saída (opcional)

    Returns:
        Caminho do arquivo WAV gerado
    """
    mp3_path = Path(mp3_path)

    if wav_path is None:
        wav_path = mp3_path.with_suffix(".wav")
    else:
        wav_path = Path(wav_path)

    cmd = [
        "ffmpeg",
        "-i", str(mp3_path),
        "-ar", "16000",  # 16kHz sample rate
        "-ac", "1",       # Mono
        "-y",             # Sobrescrever
        str(wav_path)
    ]

    print(f"Convertendo {mp3_path} para WAV 16kHz mono...")
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    print(f"Arquivo convertido: {wav_path}")

    return str(wav_path)


def transcribe_audio(
    audio_path: str,
    model_name: str = "nvidia/parakeet-tdt-0.6b-v3",
    with_timestamps: bool = False,
    output_file: str = None,
    long_audio: bool = False
) -> str:
    """
    Transcreve um arquivo de áudio usando o modelo Parakeet TDT v3.

    Args:
        audio_path: Caminho para o arquivo de áudio (MP3 ou WAV)
        model_name: Nome do modelo Parakeet a usar
        with_timestamps: Se True, inclui timestamps na saída
        output_file: Arquivo para salvar a transcrição (opcional)
        long_audio: Se True, usa atenção local para áudios longos (até 3 horas)

    Returns:
        Texto transcrito
    """
    import nemo.collections.asr as nemo_asr

    audio_path = Path(audio_path)

    if not audio_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {audio_path}")

    # Converter MP3 para WAV se necessário
    wav_path = audio_path
    temp_wav = None

    if audio_path.suffix.lower() == ".mp3":
        temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_wav.close()
        wav_path = convert_mp3_to_wav(str(audio_path), temp_wav.name)

    try:
        print(f"Carregando modelo {model_name}...")
        asr_model = nemo_asr.models.ASRModel.from_pretrained(model_name=model_name)

        # Configurar atenção local para áudios longos (até 3 horas)
        if long_audio:
            print("Habilitando modo de áudio longo (atenção local)...")
            asr_model.change_attention_model(
                self_attention_model="rel_pos_local_attn",
                att_context_size=[256, 256]
            )

        print(f"Transcrevendo: {audio_path}")
        output = asr_model.transcribe([str(wav_path)], timestamps=with_timestamps)

        transcription = output[0].text

        if with_timestamps and hasattr(output[0], 'timestamp'):
            print("\n--- Transcrição com Timestamps ---")
            segment_timestamps = output[0].timestamp.get('segment', [])
            for stamp in segment_timestamps:
                print(f"{stamp['start']:.2f}s - {stamp['end']:.2f}s : {stamp['segment']}")
            print("--- Fim dos Timestamps ---\n")

        if output_file:
            output_path = Path(output_file)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(transcription)
                if with_timestamps and hasattr(output[0], 'timestamp'):
                    f.write("\n\n--- Timestamps ---\n")
                    for stamp in output[0].timestamp.get('segment', []):
                        f.write(f"{stamp['start']:.2f}s - {stamp['end']:.2f}s : {stamp['segment']}\n")
            print(f"Transcrição salva em: {output_path}")

        return transcription

    finally:
        # Limpar arquivo temporário
        if temp_wav and os.path.exists(temp_wav.name):
            os.unlink(temp_wav.name)


def main():
    if len(sys.argv) < 2:
        print("Uso: python transcribe_audio.py <arquivo.mp3> [opções]")
        print()
        print("Opções:")
        print("  -o, --output <arquivo>   Salvar transcrição em arquivo")
        print("  -t, --timestamps         Incluir timestamps na saída")
        print("  -l, --long               Modo áudio longo (até 3 horas)")
        print("  -m, --model <nome>       Modelo a usar (padrão: nvidia/parakeet-tdt-0.6b-v3)")
        print()
        print("Idiomas suportados (detecção automática):")
        print("  bg, hr, cs, da, nl, en, et, fi, fr, de, el, hu, it, lv, lt,")
        print("  mt, pl, pt, ro, sk, sl, es, sv, ru, uk")
        print()
        print("Exemplos:")
        print("  python transcribe_audio.py audio.mp3")
        print("  python transcribe_audio.py audio.mp3 -o transcricao.txt")
        print("  python transcribe_audio.py audio.mp3 -t -o transcricao.txt")
        print("  python transcribe_audio.py audio.mp3 -l   # para áudios > 24 min")
        sys.exit(1)

    audio_path = sys.argv[1]
    output_file = None
    with_timestamps = False
    long_audio = False
    model_name = "nvidia/parakeet-tdt-0.6b-v3"

    # Parse argumentos
    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] in ("-o", "--output"):
            output_file = args[i + 1]
            i += 2
        elif args[i] in ("-t", "--timestamps"):
            with_timestamps = True
            i += 1
        elif args[i] in ("-l", "--long"):
            long_audio = True
            i += 1
        elif args[i] in ("-m", "--model"):
            model_name = args[i + 1]
            i += 2
        else:
            i += 1

    transcription = transcribe_audio(
        audio_path,
        model_name=model_name,
        with_timestamps=with_timestamps,
        output_file=output_file,
        long_audio=long_audio
    )

    print("\n--- Transcrição ---")
    print(transcription)
    print("--- Fim ---")


if __name__ == "__main__":
    main()
