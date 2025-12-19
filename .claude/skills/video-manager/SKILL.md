---
name: video-manager
description: "Gerencia o status de todos os vídeos do canal. Use para: (1) Listar vídeos por status (draft/ready/scheduled/published), (2) Atualizar status após upload, (3) Adicionar novos vídeos ao tracking, (4) Ver resumo geral do canal."
---

# Video Manager

Gerencia o arquivo `videos_status.json` que rastreia todos os vídeos do canal YouTube.

## Arquivo de Status

O arquivo `videos_status.json` na raiz do projeto contém:

```json
{
  "last_updated": "2025-12-19",
  "videos": [
    {
      "id": "clip_01",
      "file_path": "clips/01_video.mp4",
      "title": "Título do vídeo",
      "status": "ready",
      "has_thumbnail": false,
      "has_transcription": false,
      "has_description": false,
      "published_at": null,
      "scheduled_at": null,
      "youtube_url": null,
      "notes": ""
    }
  ]
}
```

## Status Possíveis

| Status | Descrição |
|--------|-----------|
| `draft` | Vídeo bruto, sem processamento |
| `processing` | Em processo de transcrição/thumbnail/descrição |
| `ready` | Pronto para publicar |
| `scheduled` | Agendado para publicação |
| `published` | Já publicado no YouTube |

## Comandos

### Listar Vídeos por Status

```bash
# Listar todos
python .claude/skills/video-manager/scripts/video_status.py list

# Filtrar por status
python .claude/skills/video-manager/scripts/video_status.py list --status ready
python .claude/skills/video-manager/scripts/video_status.py list --status published
```

### Adicionar Novo Vídeo

```bash
python .claude/skills/video-manager/scripts/video_status.py add \
  --file "clips/novo_video.mp4" \
  --title "Título do Vídeo" \
  --status ready
```

### Atualizar Status de Vídeo

```bash
# Marcar como publicado
python .claude/skills/video-manager/scripts/video_status.py update clip_01 \
  --status published \
  --youtube-url "https://youtube.com/watch?v=abc123" \
  --published-at "2025-12-19"

# Marcar como agendado
python .claude/skills/video-manager/scripts/video_status.py update clip_01 \
  --status scheduled \
  --scheduled-at "2025-12-25"

# Atualizar assets
python .claude/skills/video-manager/scripts/video_status.py update clip_01 \
  --has-thumbnail true \
  --has-transcription true
```

### Ver Resumo

```bash
python .claude/skills/video-manager/scripts/video_status.py summary
```

Mostra contagem por status e próximos passos sugeridos.

## Integração com Outras Skills

### Após Upload (youtube-video-pipeline)

Depois de fazer upload de um vídeo, **sempre** atualizar o status:

```bash
python .claude/skills/video-manager/scripts/video_status.py update <video_id> \
  --status published \
  --youtube-url "<url_retornada>" \
  --published-at "$(date +%Y-%m-%d)"
```

### Após Gerar Clips (clip-generator)

Depois de extrair clips, adicionar cada um ao tracking:

```bash
python .claude/skills/video-manager/scripts/video_status.py add \
  --file "clips/<nome_clip>.mp4" \
  --title "<titulo_sugerido>" \
  --status draft
```

### Após Gerar Assets

Quando gerar thumbnail, transcrição ou descrição:

```bash
python .claude/skills/video-manager/scripts/video_status.py update <video_id> \
  --has-thumbnail true \
  --has-transcription true \
  --has-description true
```

## Workflow Típico

1. **Clip gerado** → Adiciona com status `draft`
2. **Transcrição gerada** → Atualiza `has_transcription: true`
3. **Título/Descrição gerados** → Atualiza `has_description: true`, status `processing`
4. **Thumbnail gerada** → Atualiza `has_thumbnail: true`, status `ready`
5. **Upload feito** → Atualiza status `published`, adiciona `youtube_url`

## Fluxo Resumido

```
Novo vídeo → add (draft) → processar assets → update (ready) → upload → update (published)
```
