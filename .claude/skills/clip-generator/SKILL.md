---
name: clip-generator
description: "Gera clips/cortes automáticos a partir de uma URL do YouTube. Use quando o usuário quiser: (1) Criar clips de qualquer duração de um vídeo, (2) Identificar momentos que fazem sentido como vídeos individuais, (3) Extrair trechos completos de um vídeo do YouTube. Requer apenas a URL do vídeo."
---

# Clip Generator

Identifica automaticamente os melhores momentos de um vídeo para criar clips que funcionam como vídeos individuais. **O Claude Code faz a análise diretamente** (NÃO usa Gemini).

**Filosofia:** O tempo do clip é irrelevante. Pode ser 5 segundos ou 40 minutos. O que importa é: faz sentido postar como vídeo individual?

## Uso Principal: Pipeline Completo via URL

**Use o comando `/generate-clips` para o fluxo completo automatizado:**

```
/generate-clips <url_do_youtube>
```

Este comando executa automaticamente (tudo no Linux):
1. Download do vídeo no Linux
2. Extração de áudio e transcrição (NVIDIA Parakeet)
3. Análise de clips pelo Claude
4. Extração dos clips no Linux
5. Transferência dos clips para o macOS (organizados por data)

### Organização

Clips são salvos organizados por data no macOS:
```
clips/23-12-2025/clip1.mp4
clips/23-12-2025/clip2.mp4
```

### Paths Configurados

<!-- ⚠️ PERSONALIZAR: Ajuste os caminhos para seu ambiente -->
- **Linux**: `/home/eduardo/Documentos/agent-youtube`
- **macOS**: `/Users/eduardo/Documents/youtube/agent-youtube/clips/<DD-MM-YYYY>/`

---

## IMPORTANTE: Regras para Comandos no Linux

O Linux usa **fish** como shell padrão. Para comandos bash complexos:

```bash
# ERRADO - não funciona com fish:
ssh linux "for i in ...; do ...; done"

# CORRETO - usar bash -c:
ssh linux "bash -c 'for i in ...; do ...; done'"
```

**Sempre usar `bash -c` para:**
- Loops (`for`, `while`)
- Heredocs (`<< EOF`)
- Expansões complexas (`$()`, `${}`)

**Para listar arquivos sem cores (evita parsing quebrado):**
```bash
ssh linux "ls --color=never /path/to/files/"
```

---

## Workflow Manual (Alternativo)

### Passo 0: Limpeza Prévia (OBRIGATÓRIO)

Antes de iniciar, SEMPRE limpar arquivos de execuções anteriores:

```bash
ssh linux "bash -c 'cd /home/eduardo/Documentos/agent-youtube && rm -rf chunks/ transcricoes/ clips/ && rm -f *.mp3 clips.json transcricao_completa.txt concat_transcricoes.py'"
```

### Passo 1: Download do Vídeo

**Usar yt-dlp diretamente** (mais confiável que o script):

```bash
ssh linux "cd /home/eduardo/Documentos/agent-youtube && ./venv/bin/yt-dlp -f 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best' --merge-output-format mp4 -o '%(title)s.%(ext)s' 'URL_DO_VIDEO'"
```

### Passo 2: Extrair Áudio

```bash
ssh linux "cd /home/eduardo/Documentos/agent-youtube && ./venv/bin/python .claude/skills/youtube-video-pipeline/scripts/extract_audio.py 'VIDEO.mp4'"
```

### Passo 3: Transcrição (COM CHUNKS para vídeos longos)

**Para vídeos > 10 minutos, dividir em chunks de 5 minutos:**

```bash
# Verificar duração
ssh linux "ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 'VIDEO.mp3'"

# Se > 600 segundos, dividir em chunks:
ssh linux "cd /home/eduardo/Documentos/agent-youtube && mkdir -p chunks && ffmpeg -i 'VIDEO.mp3' -f segment -segment_time 300 -c copy chunks/chunk_%03d.mp3 -y"

# Transcrever cada chunk
ssh linux "bash -c 'cd /home/eduardo/Documentos/agent-youtube && mkdir -p transcricoes && for i in \$(ls chunks/*.mp3 | sort); do ./venv/bin/python .claude/skills/youtube-video-pipeline/scripts/transcribe_audio.py \"\$i\" -t -o \"transcricoes/\$(basename \$i .mp3).txt\" -l; done'"
```

### Passo 4: Concatenar Transcrições com Timestamps Ajustados

Criar script de concatenação no Linux:

```bash
ssh linux "bash -c 'cat > /home/eduardo/Documentos/agent-youtube/concat_transcricoes.py << '\''PYEOF'\''
import re
import os

def parse_timestamp(ts_str):
    return float(ts_str.replace(\"s\", \"\"))

def format_timestamp(seconds):
    mins = int(seconds // 60)
    secs = seconds % 60
    return f\"{mins:02d}:{secs:05.2f}\"

def process_chunk(chunk_num, offset_seconds, total_chunks):
    filepath = f\"transcricoes/chunk_{chunk_num:03d}.txt\"
    if not os.path.exists(filepath):
        return \"\", \"\"

    with open(filepath, \"r\") as f:
        content = f.read()

    parts = content.split(\"--- Timestamps ---\")
    if len(parts) < 2:
        return content.strip(), \"\"

    text = parts[0].strip()
    timestamps_section = parts[1].strip()

    adjusted_timestamps = []
    for line in timestamps_section.split(\"\\n\"):
        if not line.strip():
            continue
        match = re.match(r\"(\\d+\\.\\d+)s - (\\d+\\.\\d+)s : (.+)\", line)
        if match:
            start = parse_timestamp(match.group(1)) + offset_seconds
            end = parse_timestamp(match.group(2)) + offset_seconds
            text_part = match.group(3)
            adjusted_timestamps.append(f\"{format_timestamp(start)} - {format_timestamp(end)} : {text_part}\")

    return text, \"\\n\".join(adjusted_timestamps)

# Contar chunks
chunk_files = sorted([f for f in os.listdir(\"transcricoes\") if f.startswith(\"chunk_\") and f.endswith(\".txt\")])
total_chunks = len(chunk_files)

full_text = []
full_timestamps = []

for i in range(total_chunks):
    offset = i * 300
    text, timestamps = process_chunk(i, offset, total_chunks)
    if text:
        full_text.append(f\"\\n[Chunk {i:02d} - {offset//60}min a {(offset+300)//60}min]\\n{text}\")
    if timestamps:
        full_timestamps.append(f\"\\n[Chunk {i:02d}]\\n{timestamps}\")

with open(\"transcricao_completa.txt\", \"w\") as f:
    f.write(\"=== TRANSCRICAO COMPLETA ===\\n\")
    f.write(\"\\n\".join(full_text))
    f.write(\"\\n\\n=== TIMESTAMPS DETALHADOS ===\\n\")
    f.write(\"\\n\".join(full_timestamps))

print(f\"Transcricao completa salva ({total_chunks} chunks)\")
PYEOF'"

# Executar
ssh linux "cd /home/eduardo/Documentos/agent-youtube && ./venv/bin/python concat_transcricoes.py"
```

### Passo 5: Analisar Clips (Claude Code faz diretamente)

**IMPORTANTE: NÃO usar o script analyze_clips.py (que usa Gemini). O Claude Code deve analisar diretamente.**

1. Ler o arquivo de transcrição completa
2. Analisar o conteúdo identificando os melhores momentos para clips virais
3. Gerar o JSON no formato especificado abaixo
4. Salvar em `clips.json`

**Critérios para identificar bons clips:**
- **Quotes impactantes**: Frases memoráveis, provocativas ou inspiradoras
- **Insights únicos**: Momentos de revelação ou aprendizado valioso
- **Emoção**: Humor, surpresa, indignação, motivação
- **Histórias completas**: Mini-narrativas com início, meio e fim
- **Ganchos fortes**: Momentos que capturam atenção imediatamente
- **Explicações valiosas**: Tutoriais, análises ou explicações que agregam valor

**Para salvar o JSON no Linux (usar echo em vez de heredoc):**
```bash
ssh linux "echo '<JSON_ESCAPADO>' > /home/eduardo/Documentos/agent-youtube/clips.json"
```

**Ou criar arquivo localmente e enviar via scp:**
```bash
# Criar arquivo local
echo '<JSON>' > /tmp/clips.json
# Enviar para Linux
scp /tmp/clips.json linux:/home/eduardo/Documentos/agent-youtube/
```

### Passo 6: Extrair Clips

```bash
ssh linux "cd /home/eduardo/Documentos/agent-youtube && ./venv/bin/python .claude/skills/youtube-video-pipeline/scripts/extract_clip.py 'VIDEO.mp4' --clips clips.json"
```

### Passo 7: Transferir para macOS

**IMPORTANTE: scp com glob não funciona diretamente. Usar rsync ou loop:**

```bash
# Criar pasta com data (usar formato correto)
mkdir -p "/Users/eduardo/Documents/youtube/agent-youtube/clips/$(date +%d-%m-%Y)"

# Opção 1: rsync (recomendado)
rsync -avz --include='*.mp4' --exclude='*' linux:/home/eduardo/Documentos/agent-youtube/clips/ "/Users/eduardo/Documents/youtube/agent-youtube/clips/$(date +%d-%m-%Y)/"

# Opção 2: scp da pasta inteira
scp -r linux:/home/eduardo/Documentos/agent-youtube/clips/ "/Users/eduardo/Documents/youtube/agent-youtube/clips/$(date +%d-%m-%Y)/"
```

### Passo 8: Limpeza Final

```bash
ssh linux "bash -c 'cd /home/eduardo/Documentos/agent-youtube && rm -rf chunks/ transcricoes/ clips/ && rm -f *.mp4 *.mp3 clips.json transcricao_completa.txt concat_transcricoes.py'"
```

---

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
Limpeza → Download → Áudio → Chunks (se longo) → Transcrição → Concatenar → Análise IA → JSON → Extração → Transfer → Limpeza
```
