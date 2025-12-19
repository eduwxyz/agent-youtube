---
name: clip-generator
description: "Gera clips/cortes automáticos a partir de vídeos MP4 usando IA para identificar os melhores momentos. Use quando o usuário quiser: (1) Criar clips virais de um vídeo longo, (2) Identificar melhores momentos para shorts/reels, (3) Extrair trechos específicos de um MP4. Requer transcrição do vídeo (com ou sem timestamps)."
---

# Clip Generator

Identifica automaticamente os melhores momentos de um vídeo para criar clips virais usando análise de transcrição com IA.

## Dependências

- **ffmpeg**: Para extração dos clips
- **Google GenAI**: `pip install google-genai python-dotenv`
- **Transcrição**: Usar youtube-video-pipeline para transcrever se necessário

## Ambiente Virtual (venv) no Linux

No Linux, usar o venv existente na raiz do projeto:

```bash
# Usar o Python do venv diretamente:
./venv/bin/python script.py

# Ou ativar o venv antes de executar:
source venv/bin/activate
```

**IMPORTANTE:** Todos os comandos `python` abaixo devem usar `./venv/bin/python` no Linux.

## Workflow

### Passo 1: Obter Transcrição

Se não existe transcrição, gerar usando:

```bash
# Linux (com venv):
./venv/bin/python .claude/skills/youtube-video-pipeline/scripts/extract_audio.py video.mp4
./venv/bin/python .claude/skills/youtube-video-pipeline/scripts/transcribe_audio.py video.mp3 -t -o video_transcricao.txt -l

# macOS:
python .claude/skills/youtube-video-pipeline/scripts/extract_audio.py video.mp4
python .claude/skills/youtube-video-pipeline/scripts/transcribe_audio.py video.mp3 -t -o video_transcricao.txt -l
```

A flag `-t` inclui timestamps (recomendado para precisão).

### Passo 2: Analisar Clips

```bash
# Linux (com venv):
./venv/bin/python .claude/skills/clip-generator/scripts/analyze_clips.py video_transcricao.txt -o clips.json

# macOS:
python .claude/skills/clip-generator/scripts/analyze_clips.py video_transcricao.txt -o clips.json
```

Opções:
- `-n, --max-clips <num>`: Número máximo de clips (padrão: 5)
- `-o, --output <arquivo>`: Salvar JSON com clips identificados

O script identifica momentos com:
- Quotes impactantes e memoráveis
- Insights únicos e revelações
- Momentos de emoção (humor, surpresa, motivação)
- Mini-histórias com início, meio e fim
- Ganchos fortes para capturar atenção

### Passo 3: Extrair Clips

```bash
# Linux (com venv):
./venv/bin/python .claude/skills/youtube-video-pipeline/scripts/extract_clip.py video.mp4 --clips clips.json

# macOS:
python .claude/skills/youtube-video-pipeline/scripts/extract_clip.py video.mp4 --clips clips.json
```

Gera clips no diretório `clips/` com nomes baseados nos títulos sugeridos.

## Formato do JSON

```json
{
    "cortes": [
        {
            "numero": 1,
            "inicio_segundos": 125.5,
            "fim_segundos": 185.0,
            "duracao_estimada": "59s",
            "titulo_sugerido": "Título viral para o clip",
            "gancho": "Primeira frase do clip",
            "motivo": "Por que esse momento é bom",
            "potencial_viral": "alto"
        }
    ],
    "resumo_video": "Resumo do conteúdo"
}
```

## Fluxo Resumido

```
MP4 → Transcrição (com timestamps) → Análise IA → JSON → Extração clips
```

## Extração Manual

Para extrair um único clip manualmente:

```bash
# Linux (com venv):
./venv/bin/python .claude/skills/youtube-video-pipeline/scripts/extract_clip.py video.mp4 --start 2:05 --end 4:30 -o clip.mp4

# macOS:
python .claude/skills/youtube-video-pipeline/scripts/extract_clip.py video.mp4 --start 2:05 --end 4:30 -o clip.mp4
```
