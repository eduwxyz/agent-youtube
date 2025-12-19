#!/usr/bin/env python3
"""
Analisa transcrição de vídeo e identifica os melhores momentos para clips.
Usa Gemini para identificar quotes impactantes, insights e momentos de engajamento.

Uso:
    python analyze_clips.py transcricao.txt -o clips.json
    python analyze_clips.py transcricao.txt --max-clips 5 -o clips.json
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from google import genai

load_dotenv()


def parse_transcription_with_timestamps(content: str) -> list[dict]:
    """
    Parseia transcrição com timestamps.

    Formato esperado:
    123.45s - 130.67s : texto do segmento

    Returns:
        Lista de segmentos com start, end, text
    """
    segments = []
    timestamp_pattern = r'(\d+\.?\d*)s?\s*-\s*(\d+\.?\d*)s?\s*:\s*(.+)'

    for line in content.split('\n'):
        match = re.match(timestamp_pattern, line.strip())
        if match:
            segments.append({
                'start': float(match.group(1)),
                'end': float(match.group(2)),
                'text': match.group(3).strip()
            })

    return segments


def format_segments_for_analysis(segments: list[dict]) -> str:
    """Formata segmentos para análise pela IA."""
    formatted = []
    for seg in segments:
        formatted.append(f"[{seg['start']:.1f}s - {seg['end']:.1f}s] {seg['text']}")
    return '\n'.join(formatted)


def analyze_clips_with_gemini(
    transcription: str,
    max_clips: int = 5,
    segments: list[dict] = None
) -> dict:
    """
    Usa Gemini para identificar os melhores momentos para clips.

    Args:
        transcription: Texto da transcrição
        max_clips: Número máximo de clips a identificar
        segments: Segmentos com timestamps (opcional)

    Returns:
        Dict com lista de cortes sugeridos
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY não encontrada no ambiente")

    client = genai.Client(api_key=api_key)

    # Preparar contexto com timestamps se disponível
    if segments:
        context = format_segments_for_analysis(segments)
        timestamp_instruction = """
Os timestamps estão no formato [inicio - fim] antes de cada segmento.
Use esses timestamps EXATOS para definir inicio_segundos e fim_segundos.
Ajuste os tempos para capturar o contexto completo do momento (alguns segundos antes e depois se necessário)."""
    else:
        context = transcription
        timestamp_instruction = """
IMPORTANTE: Como não há timestamps, estime os tempos baseado na posição do texto.
Assuma velocidade média de fala de 150 palavras por minuto.
Conte as palavras até o trecho identificado para estimar o tempo."""

    prompt = f"""Analise a transcrição abaixo e identifique os {max_clips} melhores momentos para criar clips virais para redes sociais (YouTube Shorts, TikTok, Reels).

{timestamp_instruction}

CRITÉRIOS PARA BONS CLIPS:
1. **Quotes impactantes**: Frases memoráveis, provocativas ou inspiradoras
2. **Insights únicos**: Momentos de revelação ou aprendizado valioso
3. **Emoção**: Humor, surpresa, indignação, motivação
4. **Histórias completas**: Mini-narrativas com início, meio e fim
5. **Ganchos fortes**: Momentos que capturam atenção imediatamente

REGRAS:
- Cada clip deve ter entre 30 segundos e 3 minutos (ideal: 45-90 segundos)
- O clip deve começar com um gancho forte (não no meio de uma frase)
- O clip deve ter um encerramento natural (conclusão da ideia)
- Priorize momentos que fazem sentido isolados (sem contexto externo)

TRANSCRIÇÃO:
{context}

Responda APENAS com JSON válido no formato:
{{
    "cortes": [
        {{
            "numero": 1,
            "inicio_segundos": 125.5,
            "fim_segundos": 185.0,
            "duracao_estimada": "59s",
            "titulo_sugerido": "Título viral para o clip",
            "gancho": "Primeira frase que aparece no clip",
            "motivo": "Por que esse momento é bom para clip",
            "potencial_viral": "alto/médio/baixo"
        }}
    ],
    "resumo_video": "Breve resumo do conteúdo geral do vídeo"
}}"""

    print("Analisando transcrição com Gemini...")
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    # Extrair JSON da resposta
    response_text = response.text.strip()

    # Remover marcadores de código se presentes
    if response_text.startswith('```'):
        lines = response_text.split('\n')
        response_text = '\n'.join(lines[1:-1])

    try:
        result = json.loads(response_text)
    except json.JSONDecodeError as e:
        print(f"Erro ao parsear JSON: {e}")
        print(f"Resposta: {response_text[:500]}...")
        raise

    return result


def analyze_transcription(
    transcription_path: str,
    output_path: Optional[str] = None,
    max_clips: int = 5
) -> dict:
    """
    Analisa arquivo de transcrição e gera JSON com clips sugeridos.

    Args:
        transcription_path: Caminho para arquivo de transcrição
        output_path: Caminho para salvar JSON (opcional)
        max_clips: Número máximo de clips

    Returns:
        Dict com clips sugeridos
    """
    transcription_path = Path(transcription_path)

    if not transcription_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {transcription_path}")

    content = transcription_path.read_text(encoding='utf-8')

    # Tentar extrair segmentos com timestamps
    segments = parse_transcription_with_timestamps(content)

    if segments:
        print(f"Encontrados {len(segments)} segmentos com timestamps")
    else:
        print("Transcrição sem timestamps - estimando tempos")

    # Extrair texto puro (sem timestamps) para contexto
    if '--- Timestamps ---' in content:
        transcription_text = content.split('--- Timestamps ---')[0].strip()
    else:
        transcription_text = content

    # Analisar com Gemini
    result = analyze_clips_with_gemini(
        transcription=transcription_text,
        max_clips=max_clips,
        segments=segments if segments else None
    )

    # Salvar resultado
    if output_path:
        output_path = Path(output_path)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\nClips salvos em: {output_path}")

    return result


def print_clips_summary(result: dict):
    """Imprime resumo dos clips identificados."""
    print("\n" + "=" * 60)
    print("CLIPS IDENTIFICADOS")
    print("=" * 60)

    if 'resumo_video' in result:
        print(f"\nResumo do vídeo: {result['resumo_video']}")

    for corte in result.get('cortes', []):
        print(f"\n--- Clip {corte['numero']} ---")
        print(f"Título: {corte['titulo_sugerido']}")
        print(f"Tempo: {corte['inicio_segundos']}s - {corte['fim_segundos']}s ({corte.get('duracao_estimada', 'N/A')})")
        print(f"Gancho: \"{corte.get('gancho', 'N/A')}\"")
        print(f"Motivo: {corte.get('motivo', 'N/A')}")
        print(f"Potencial: {corte.get('potencial_viral', 'N/A')}")

    print("\n" + "=" * 60)


def main():
    if len(sys.argv) < 2:
        print("Uso: python analyze_clips.py <transcricao.txt> [opções]")
        print()
        print("Opções:")
        print("  -o, --output <arquivo>   Salvar JSON com clips")
        print("  -n, --max-clips <num>    Número máximo de clips (padrão: 5)")
        print()
        print("Exemplos:")
        print("  python analyze_clips.py video_transcricao.txt")
        print("  python analyze_clips.py video_transcricao.txt -o clips.json")
        print("  python analyze_clips.py video_transcricao.txt -n 10 -o clips.json")
        sys.exit(1)

    transcription_path = sys.argv[1]
    output_path = None
    max_clips = 5

    # Parse argumentos
    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] in ("-o", "--output"):
            output_path = args[i + 1]
            i += 2
        elif args[i] in ("-n", "--max-clips"):
            max_clips = int(args[i + 1])
            i += 2
        else:
            i += 1

    result = analyze_transcription(
        transcription_path,
        output_path=output_path,
        max_clips=max_clips
    )

    print_clips_summary(result)

    if not output_path:
        print("\nDica: Use -o clips.json para salvar e depois extrair com:")
        print(f"  python extract_clip.py video.mp4 --clips clips.json")


if __name__ == "__main__":
    main()
