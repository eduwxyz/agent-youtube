---
name: clip-generator
description: "Gera clips/cortes automáticos a partir de vídeos MP4 usando IA para identificar os melhores momentos. Use quando o usuário quiser: (1) Criar clips virais de um vídeo longo, (2) Identificar melhores momentos para shorts/reels, (3) Extrair trechos específicos de um MP4. Requer transcrição do vídeo (com ou sem timestamps)."
---

# Clip Generator

Identifica automaticamente os melhores momentos de um vídeo para criar clips virais. **O Claude Code faz a análise diretamente** (NÃO usa Gemini).

## Dependências

- **ffmpeg**: Para extração dos clips
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

### Passo 2: Analisar Clips (Claude Code faz diretamente)

**IMPORTANTE: NÃO usar o script analyze_clips.py (que usa Gemini). O Claude Code deve analisar diretamente.**

1. Ler o arquivo de transcrição com timestamps
2. Analisar o conteúdo identificando os melhores momentos para clips virais
3. Gerar o JSON no formato especificado abaixo
4. Salvar em `clips.json`

**Critérios para identificar bons clips:**
- **Quotes impactantes**: Frases memoráveis, provocativas ou inspiradoras
- **Insights únicos**: Momentos de revelação ou aprendizado valioso
- **Emoção**: Humor, surpresa, indignação, motivação
- **Histórias completas**: Mini-narrativas com início, meio e fim
- **Ganchos fortes**: Momentos que capturam atenção imediatamente

**Regras:**
- **SEM LIMITE DE DURAÇÃO** - o clip pode ter 30 segundos ou 15 minutos, o que importa é o conteúdo fazer sentido completo
- O clip deve começar com um gancho forte (não no meio de uma frase)
- O clip deve ter um encerramento natural (conclusão da ideia)
- Priorize momentos que fazem sentido isolados (sem contexto externo)
- Use os timestamps EXATOS da transcrição
- Se um tema/explicação leva 10 minutos mas é valioso, inclua os 10 minutos completos

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
