---
name: title-and-description-video
description: Gera título e descrição otimizados para vídeos do YouTube a partir de um arquivo MP4. Use quando o usuário fornecer um caminho para um vídeo MP4 e quiser gerar título e descrição para YouTube. O pipeline extrai o áudio, transcreve usando NVIDIA Parakeet, e gera sugestões de título + descrição completa.
---

# Title And Description Video

Pipeline completo para gerar título e descrição de vídeos do YouTube a partir de um arquivo MP4.

## Dependências

- **ffmpeg**: `brew install ffmpeg`
- **NeMo ASR**: `pip install nemo_toolkit[asr]`

## Workflow

Dado um caminho para um arquivo MP4, executar os passos na ordem:

### Passo 1: Extrair áudio

```bash
python scripts/extract_audio.py <video.mp4>
```

Gera `<video>.mp3` no mesmo diretório.

### Passo 2: Transcrever áudio

```bash
python scripts/transcribe_audio.py <video.mp3> -o <video>_transcricao.txt -l
```

- Use `-l` para vídeos longos (mais de 24 minutos)
- Gera arquivo de transcrição `.txt`

### Passo 3: Gerar título

Ler a transcrição e gerar 5 opções de títulos seguindo estas regras:

**Regras para títulos:**
- Máximo 60 caracteres
- Gatilhos mentais: curiosidade, urgência, exclusividade, números, resultados
- Evitar clickbait vazio, títulos genéricos, muitas maiúsculas
- Começar com palavra impactante
- Usar parênteses para contexto: "... (funciona mesmo)"

**Formato de saída para cada título:**
- O título
- Por que funciona (breve)
- Impacto estimado (baixo/médio/alto)

Recomendar o melhor título ao final.

### Passo 4: Gerar descrição

Com base na transcrição, gerar descrição otimizada para SEO:

**Estrutura:**

1. **Gancho inicial (2-3 linhas)**: primeiros 150 caracteres são cruciais
2. **Corpo**: expandir valor do vídeo, parágrafos curtos, 3-5 keywords secundárias
3. **CTA**: pedir inscrição, likes, comentários
4. **Links/recursos**: placeholders para links mencionados
5. **Hashtags**: 3-5 hashtags relevantes

**Regras SEO:**
- Tamanho ideal: 200-500 palavras
- Evitar keyword stuffing
- Incluir perguntas para estimular comentários

## Output Final

Apresentar ao usuário:

1. **Título recomendado** + alternativas
2. **Descrição completa** pronta para copiar
3. **Versão curta** (~150 caracteres) para preview
