---
description: Pipeline completo para gerar clips virais a partir de uma URL do YouTube
arguments:
  - name: url
    description: URL do vídeo do YouTube
    required: true
  - name: quantidade
    description: Quantidade máxima de clips a gerar (padrão 5)
    required: false
---

# Pipeline de Geração de Clips

Este comando executa o pipeline completo para gerar clips virais a partir de um vídeo do YouTube.

## Configuração de Paths

<!-- ⚠️ PERSONALIZAR: Ajuste os caminhos abaixo para seu ambiente -->
- **Linux**: `/home/eduardo/Documentos/agent-youtube`
- **macOS**: `/Users/eduardo/Documents/youtube/agent-youtube`

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

**Para listar arquivos sem cores:**
```bash
ssh linux "ls --color=never /path/"
```

---

## Workflow Completo

### Passo 0: Limpeza Prévia (OBRIGATÓRIO)

Antes de QUALQUER execução, limpar arquivos de execuções anteriores:

```bash
ssh linux "bash -c 'cd /home/eduardo/Documentos/agent-youtube && rm -rf chunks/ transcricoes/ clips/ && rm -f *.mp3 clips.json transcricao_completa.txt concat_transcricoes.py'"
```

### Passo 1: Download do Vídeo no Linux

**Usar yt-dlp diretamente** (mais confiável):

```bash
ssh linux "cd /home/eduardo/Documentos/agent-youtube && ./venv/bin/yt-dlp -f 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best' --merge-output-format mp4 -o '%(title)s.%(ext)s' '$ARGUMENTS.url'"
```

Capture o nome do arquivo baixado da saída (geralmente termina em .mp4).

### Passo 2: Extrair Áudio

```bash
ssh linux "cd /home/eduardo/Documentos/agent-youtube && ./venv/bin/python .claude/skills/youtube-video-pipeline/scripts/extract_audio.py 'VIDEO.mp4'"
```

### Passo 3: Verificar Duração e Dividir em Chunks (se necessário)

```bash
# Verificar duração do áudio
ssh linux "ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 'VIDEO.mp3'"
```

**Se duração > 600 segundos (10 min), dividir em chunks de 5 minutos:**

```bash
ssh linux "cd /home/eduardo/Documentos/agent-youtube && mkdir -p chunks && ffmpeg -i 'VIDEO.mp3' -f segment -segment_time 300 -c copy chunks/chunk_%03d.mp3 -y"
```

### Passo 4: Transcrever

**Se dividiu em chunks:**
```bash
ssh linux "bash -c 'cd /home/eduardo/Documentos/agent-youtube && mkdir -p transcricoes && for f in chunks/chunk_*.mp3; do ./venv/bin/python .claude/skills/youtube-video-pipeline/scripts/transcribe_audio.py \"\$f\" -t -o \"transcricoes/\$(basename \$f .mp3).txt\" -l; done'"
```

**Se não dividiu (vídeo curto):**
```bash
ssh linux "cd /home/eduardo/Documentos/agent-youtube && ./venv/bin/python .claude/skills/youtube-video-pipeline/scripts/transcribe_audio.py VIDEO.mp3 -t -o transcricao.txt -l"
```

### Passo 5: Concatenar Transcrições (se usou chunks)

Criar e executar script de concatenação:

```bash
ssh linux "bash -c 'cat > /home/eduardo/Documentos/agent-youtube/concat_transcricoes.py << '\''PYEOF'\''
import re, os

def format_ts(s): return f\"{int(s//60):02d}:{s%60:05.2f}\"

def process(n, off):
    f = f\"transcricoes/chunk_{n:03d}.txt\"
    if not os.path.exists(f): return \"\", \"\"
    c = open(f).read()
    p = c.split(\"--- Timestamps ---\")
    if len(p) < 2: return c.strip(), \"\"
    ts = []
    for l in p[1].strip().split(\"\\n\"):
        m = re.match(r\"(\\d+\\.\\d+)s - (\\d+\\.\\d+)s : (.+)\", l)
        if m:
            ts.append(f\"{format_ts(float(m[1])+off)} - {format_ts(float(m[2])+off)} : {m[3]}\")
    return p[0].strip(), \"\\n\".join(ts)

chunks = sorted([f for f in os.listdir(\"transcricoes\") if f.startswith(\"chunk_\")])
txt, ts = [], []
for i in range(len(chunks)):
    t, s = process(i, i*300)
    if t: txt.append(f\"\\n[{i*5}-{(i+1)*5}min]\\n{t}\")
    if s: ts.append(f\"\\n[Chunk {i}]\\n{s}\")
open(\"transcricao_completa.txt\",\"w\").write(\"\\n\".join(txt)+\"\\n\\n=== TIMESTAMPS ===\\n\"+\"\\n\".join(ts))
print(f\"OK: {len(chunks)} chunks\")
PYEOF'"

ssh linux "cd /home/eduardo/Documentos/agent-youtube && ./venv/bin/python concat_transcricoes.py"
```

### Passo 6: Ler Transcrição

```bash
ssh linux "cat /home/eduardo/Documentos/agent-youtube/transcricao_completa.txt"
```

### Passo 7: Analisar e Identificar Clips (Claude faz diretamente)

**IMPORTANTE: NÃO usar scripts externos. O Claude Code analisa diretamente.**

1. Leia a transcrição com timestamps
2. Identifique os melhores momentos para clips virais:
   - **Quotes impactantes**: Frases memoráveis
   - **Insights únicos**: Revelações valiosas
   - **Emoção**: Humor, surpresa, motivação
   - **Histórias completas**: Mini-narrativas
   - **Ganchos fortes**: Capturam atenção

3. **SEM LIMITE DE DURAÇÃO** - pode ter 30s ou 15min

4. Gere o JSON:

```json
{
    "cortes": [
        {
            "numero": 1,
            "inicio_segundos": 125.5,
            "fim_segundos": 185.0,
            "duracao_estimada": "59s",
            "titulo_sugerido": "Título viral",
            "gancho": "Primeira frase",
            "motivo": "Por que é bom",
            "potencial_viral": "alto"
        }
    ],
    "resumo_video": "Resumo"
}
```

5. **Salvar JSON no Linux** (criar local e enviar):

```bash
# Criar arquivo local com o JSON
cat > /tmp/clips.json << 'EOF'
{JSON_AQUI}
EOF

# Enviar para Linux
scp /tmp/clips.json linux:/home/eduardo/Documentos/agent-youtube/
```

### Passo 8: Extrair Clips no Linux

```bash
ssh linux "cd /home/eduardo/Documentos/agent-youtube && ./venv/bin/python .claude/skills/youtube-video-pipeline/scripts/extract_clip.py 'VIDEO.mp4' --clips clips.json"
```

### Passo 9: Transferir para macOS

**IMPORTANTE: scp com glob `*.mp4` NÃO funciona diretamente!**

```bash
# Criar pasta com data de hoje
mkdir -p "/Users/eduardo/Documents/youtube/agent-youtube/clips/$(date +%d-%m-%Y)"

# Usar rsync (funciona com globs remotos)
rsync -avz linux:/home/eduardo/Documentos/agent-youtube/clips/ "/Users/eduardo/Documents/youtube/agent-youtube/clips/$(date +%d-%m-%Y)/"
```

### Passo 10: Limpeza no Linux

```bash
ssh linux "bash -c 'cd /home/eduardo/Documentos/agent-youtube && rm -rf chunks/ transcricoes/ clips/ && rm -f *.mp4 *.mp3 clips.json transcricao_completa.txt concat_transcricoes.py'"
```

---

## Parâmetros

- **URL**: $ARGUMENTS.url
- **Quantidade de clips**: $ARGUMENTS.quantidade (padrão: 5)

## Checklist de Problemas Comuns

| Problema | Solução |
|----------|---------|
| `fish: Missing end` | Usar `bash -c '...'` |
| `yt-dlp não instalado` | Usar `./venv/bin/yt-dlp` diretamente |
| Chunks antigos | Executar Passo 0 (limpeza) |
| `scp *.mp4` falha | Usar `rsync` em vez de `scp` com glob |
| Output com cores | Usar `ls --color=never` |
| Heredoc falha | Criar arquivo local e usar `scp` |

## Fluxo Resumido

```
Limpeza → Download → Áudio → Chunks (se longo) → Transcrição → Concatenar → Análise IA → JSON → Extração → rsync → Limpeza
```

**Execute o pipeline completo agora com a URL: $ARGUMENTS.url**
