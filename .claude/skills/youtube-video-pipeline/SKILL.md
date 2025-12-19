---
name: youtube-video-pipeline
description: "Pipeline completo para publicar vídeos no YouTube a partir de um arquivo MP4. Use quando o usuário fornecer um caminho para um vídeo MP4 e quiser fazer o fluxo completo de publicação. O pipeline executa: (1) Extrair áudio MP3, (2) Transcrever com NVIDIA Parakeet, (3) Gerar título otimizado, (4) Gerar descrição SEO, (5) Gerar thumbnail viral com IA, (6) Upload para YouTube."
---

# YouTube Video Pipeline

Pipeline automatizado para transformar um arquivo MP4 em um vídeo publicado no YouTube com título, descrição e thumbnail otimizados.

## Dependências

- **ffmpeg**: `brew install ffmpeg` (macOS) ou `sudo pacman -S ffmpeg` (Arch Linux)
- **NeMo ASR**: `pip install nemo_toolkit[asr]`
- **Google GenAI**: `pip install google-genai pillow python-dotenv`
- **YouTube API**: `pip install google-auth-oauthlib google-api-python-client`

## Ambiente Virtual (venv) no Linux

No Linux, existe um venv configurado na raiz do projeto. **Sempre ative o venv antes de executar os scripts Python:**

```bash
# Ativar o venv (executar uma vez por sessão)
source venv/bin/activate

# Ou usar o caminho completo do Python do venv
./venv/bin/python scripts/nome_do_script.py
```

**IMPORTANTE:** Todos os comandos `python` nos exemplos abaixo devem ser executados com o venv ativado ou usando `./venv/bin/python` no Linux.

## Variáveis de Ambiente

Criar `.env` na raiz do projeto:

```
GOOGLE_API_KEY=sua_api_key_gemini
```

## Arquivos de Autenticação YouTube

- `client_secret_*.json` - Credenciais OAuth do Google Cloud Console
- `token.json` - Token gerado após primeira autenticação

## Workflow Completo

Dado um caminho para `<video>.mp4`, executar os passos na ordem:

### Passo 1: Extrair Áudio

```bash
# Linux (com venv):
./venv/bin/python .claude/skills/youtube-video-pipeline/scripts/extract_audio.py <video>.mp4

# macOS:
python .claude/skills/youtube-video-pipeline/scripts/extract_audio.py <video>.mp4
```

Gera `<video>.mp3` no mesmo diretório.

### Passo 2: Transcrever Áudio

```bash
# Linux (com venv):
./venv/bin/python .claude/skills/youtube-video-pipeline/scripts/transcribe_audio.py <video>.mp3 -o <video>_transcricao.txt -l

# macOS:
python .claude/skills/youtube-video-pipeline/scripts/transcribe_audio.py <video>.mp3 -o <video>_transcricao.txt -l
```

- Use `-l` para vídeos longos (mais de 24 minutos)
- Gera arquivo `<video>_transcricao.txt`

### Passo 3: Gerar Título

Ler a transcrição e gerar 5 opções de títulos.

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

### Passo 4: Gerar Descrição

Com base na transcrição, gerar descrição otimizada para SEO.

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

### Passo 5: Gerar Thumbnail

```bash
# Linux (com venv):
./venv/bin/python .claude/skills/youtube-video-pipeline/scripts/generate_thumbnail.py "<título>" -d "<descrição curta>" -o <video>_thumb.png

# macOS:
python .claude/skills/youtube-video-pipeline/scripts/generate_thumbnail.py "<título>" -d "<descrição curta>" -o <video>_thumb.png
```

Opções adicionais:
- `-r <imagem>` - Imagem de referência para consistência de rosto
- Usa Gemini para gerar thumbnail viral estilo MrBeast/MKBHD

### Passo 6: Upload para YouTube

```bash
# Linux (com venv):
./venv/bin/python .claude/skills/youtube-video-pipeline/scripts/upload_youtube.py <video>.mp4 -t "<título>" -d "<descrição>" --tags tag1 tag2 --privacy private

# macOS:
python .claude/skills/youtube-video-pipeline/scripts/upload_youtube.py <video>.mp4 -t "<título>" -d "<descrição>" --tags tag1 tag2 --privacy private
```

**Parâmetros:**
- `-t, --title`: Título do vídeo (obrigatório)
- `-d, --description`: Descrição completa
- `--tags`: Lista de tags separadas por espaço
- `--category`: ID da categoria (padrão: 22 = People & Blogs)
- `--privacy`: `public`, `private` ou `unlisted` (padrão: private)

Na primeira execução, abre navegador para autenticação OAuth.

## Integração com Video Manager

O script `upload_youtube.py` **atualiza automaticamente** o arquivo `videos_status.json` após cada upload:

- Define status como `published`
- Registra a URL do YouTube
- Marca data de publicação
- Atualiza flag de thumbnail

Se o vídeo não existir no tracking, será adicionado automaticamente.

Para verificar o status após upload:

```bash
python .claude/skills/video-manager/scripts/video_status.py summary
```

## Output Final

Apresentar ao usuário:

1. **Arquivos gerados:**
   - `<video>.mp3` - Áudio extraído
   - `<video>_transcricao.txt` - Transcrição completa
   - `<video>_thumb.png` - Thumbnail gerada

2. **Título recomendado** + alternativas

3. **Descrição completa** pronta para copiar

4. **Link do vídeo** no YouTube (se upload realizado)

5. **Status atualizado** no `videos_status.json`

## Fluxo Resumido

```
MP4 → MP3 → Transcrição → Título + Descrição → Thumbnail → YouTube
```

Cada etapa pode ser executada individualmente se necessário.
