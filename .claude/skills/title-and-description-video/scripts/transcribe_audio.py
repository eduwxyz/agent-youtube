#!/usr/bin/env python3
"""Transcreve áudio usando NVIDIA Parakeet TDT v3."""

import subprocess
import sys
import os
import tempfile
from pathlib import Path


def convert_mp3_to_wav(mp3_path: str, wav_path: str = None) -> str:
    """Converte MP3 para WAV 16kHz mono."""
    mp3_path = Path(mp3_path)
    if wav_path is None:
        wav_path = mp3_path.with_suffix(".wav")
    else:
        wav_path = Path(wav_path)

    cmd = [
        "ffmpeg",
        "-i", str(mp3_path),
        "-ar", "16000",
        "-ac", "1",
        "-y",
        str(wav_path)
    ]

    print(f"Convertendo para WAV 16kHz mono...")
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return str(wav_path)


def transcribe_audio(audio_path: str, output_file: str = None, long_audio: bool = False) -> str:
    """
    Transcreve áudio usando o modelo Parakeet TDT v3.

    Args:
        audio_path: Caminho para o arquivo de áudio (MP3 ou WAV)
        output_file: Arquivo para salvar a transcrição (opcional)
        long_audio: Se True, usa atenção local para áudios longos

    Returns:
        Texto transcrito
    """
    import nemo.collections.asr as nemo_asr

    audio_path = Path(audio_path)

    if not audio_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {audio_path}")

    wav_path = audio_path
    temp_wav = None

    if audio_path.suffix.lower() == ".mp3":
        temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_wav.close()
        wav_path = convert_mp3_to_wav(str(audio_path), temp_wav.name)

    try:
        print(f"Carregando modelo nvidia/parakeet-tdt-0.6b-v3...")
        asr_model = nemo_asr.models.ASRModel.from_pretrained(
            model_name="nvidia/parakeet-tdt-0.6b-v3"
        )

        if long_audio:
            print("Habilitando modo de áudio longo...")
            asr_model.change_attention_model(
                self_attention_model="rel_pos_local_attn",
                att_context_size=[256, 256]
            )

        print(f"Transcrevendo: {audio_path}")
        output = asr_model.transcribe([str(wav_path)])
        transcription = output[0].text

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(transcription)
            print(f"Transcrição salva em: {output_file}")

        return transcription

    finally:
        if temp_wav and os.path.exists(temp_wav.name):
            os.unlink(temp_wav.name)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python transcribe_audio.py <audio.mp3> [-o output.txt] [-l]")
        sys.exit(1)

    audio = sys.argv[1]
    output = None
    long_mode = False

    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] in ("-o", "--output"):
            output = args[i + 1]
            i += 2
        elif args[i] in ("-l", "--long"):
            long_mode = True
            i += 1
        else:
            i += 1

    result = transcribe_audio(audio, output, long_mode)
    print("\n--- Transcrição ---")
    print(result)
