# YouTube Agent Pipeline

Pipeline automatizado para transformar vídeos MP4 em publicações completas no YouTube usando inteligência artificial. O projeto utiliza Claude Code como agente de IA para orquestrar todo o processo de publicação.

## O que este projeto faz?

A partir de um arquivo de vídeo MP4, o pipeline executa automaticamente:

1. **Extração de áudio** - Converte o vídeo para MP3 usando FFmpeg
2. **Transcrição** - Transcreve o áudio usando NVIDIA Parakeet (suporta 25 idiomas)
3. **Geração de título** - Cria títulos otimizados com gatilhos mentais e SEO
4. **Geração de descrição** - Produz descrições otimizadas para SEO do YouTube
5. **Geração de thumbnail** - Usa Google Gemini para criar thumbnails virais
6. **Upload para YouTube** - Publica o vídeo via API oficial do YouTube

```
MP4 → MP3 → Transcrição → Título + Descrição → Thumbnail → YouTube
```

## Funcionalidades

- Transcrição automática com detecção de idioma (25 idiomas suportados)
- Geração de títulos com gatilhos mentais (curiosidade, urgência, números)
- Descrições otimizadas para SEO com CTAs e hashtags
- Thumbnails virais geradas por IA (estilo MrBeast/MKBHD)
- Upload direto para YouTube com metadata completa
- Geração automática de clips a partir de vídeos longos/lives
- Suporte a vídeos de até 3 horas

## Pré-requisitos

### Software

- **Python 3.10+**
- **FFmpeg** - Para processamento de áudio/vídeo
- **Claude Code** - CLI oficial da Anthropic para usar o agente

### Hardware (para transcrição local)

- GPU NVIDIA com CUDA (recomendado para transcrição rápida)
- Mínimo 8GB de VRAM para o modelo Parakeet
- Alternativa: usar máquina remota via SSH

## Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/eduwxyz/agent-youtube.git
cd agent-youtube
```

### 2. Instale as dependências Python

```bash
pip install -r requirements.txt
```

### 3. Instale o FFmpeg

**Linux (Ubuntu/Debian):**
```bash
sudo apt install ffmpeg
```

**Linux (Arch):**
```bash
sudo pacman -S ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
```bash
winget install ffmpeg
```

### 4. Instale o Claude Code

Siga as instruções oficiais em: https://docs.anthropic.com/claude-code

```bash
npm install -g @anthropic-ai/claude-code
```

## Configuração

### 1. Configure a API Key do Google (Gemini)

Crie um arquivo `.env` na raiz do projeto:

```bash
cp .env.example .env
```

Edite o arquivo `.env` e adicione sua API key do Google AI Studio:

```env
GOOGLE_API_KEY=sua-api-key-aqui
```

Para obter uma API key:
1. Acesse https://aistudio.google.com/
2. Clique em "Get API Key"
3. Crie uma nova API key

### 2. Configure as credenciais do YouTube (para upload)

Para fazer upload de vídeos, você precisa configurar OAuth2 do Google:

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto ou selecione um existente
3. Ative a "YouTube Data API v3"
4. Vá em "Credenciais" → "Criar credenciais" → "ID do cliente OAuth"
5. Selecione "Aplicativo de desktop"
6. Baixe o arquivo JSON de credenciais
7. Renomeie para `client_secret_*.json` e coloque na raiz do projeto

Na primeira execução do upload, um navegador abrirá para autenticação. Após autorizar, um arquivo `token.json` será criado automaticamente.

---

## Personalizações Necessárias

> **Nota:** Os arquivos já contêm configurações funcionais. Procure por comentários com `⚠️ PERSONALIZAR` para encontrar o que precisa ser alterado.

Este projeto contém algumas configurações que você precisa ajustar para seu uso:

### 1. Links das Redes Sociais (Obrigatório)

Edite `.claude/commands/generate_description.md` e substitua os links de LinkedIn/GitHub pelos seus.

### 2. Imagem de Referência para Thumbnails (Obrigatório)

O script de geração de thumbnails usa uma imagem de referência do rosto para manter consistência visual.

**O que fazer:**
1. Adicione uma foto sua (rosto bem visível, boa qualidade) na raiz do projeto ou em `.claude/skills/youtube-video-pipeline/assets/`
2. Edite `.claude/commands/generate_thumb.md` e altere o nome do arquivo
3. Edite `.claude/skills/youtube-video-pipeline/scripts/generate_thumbnail.py` (linha 46) se usar o caminho em assets

### 3. Caminhos do Projeto (Se usar Linux remoto)

Se você usa uma máquina Linux remota para transcrição, edite os caminhos em:
- `.claude/commands/generate-clips.md`
- `.claude/skills/clip-generator/SKILL.md`

### 4. Ambiente Linux Remoto (Opcional)

Se você tem uma máquina Linux com GPU:

1. Configure o acesso SSH no seu `~/.ssh/config`:
   ```
   Host linux
       HostName seu-servidor-ou-ip
       User seu-usuario
   ```
2. Clone o projeto também na máquina Linux
3. Crie um venv e instale as dependências lá

**Se você NÃO tem uma máquina Linux remota:**
- Ignore a skill `env-linux` e o comando `/generate-clips`
- Execute a transcrição localmente (requer GPU NVIDIA com 8GB+ VRAM)
- Ou use um serviço de transcrição em nuvem

---

## Uso

### Uso com Claude Code (Recomendado)

A forma mais fácil de usar o pipeline é através do Claude Code:

```bash
cd agent-youtube
claude
```

Dentro do Claude Code, você pode:

**Pipeline completo:**
```
Publique o vídeo /caminho/para/video.mp4 no YouTube
```

**Gerar clips de uma live/vídeo longo:**
```
/generate-clips https://www.youtube.com/watch?v=VIDEO_ID
```

**Comandos individuais:**
```
/generate_title /caminho/para/transcricao.txt
/generate_description /caminho/para/transcricao.txt
/generate_thumb "Título do Vídeo"
/analyze_clips /caminho/para/transcricao.txt
```

### Uso Manual (Scripts Individuais)

Você também pode executar cada etapa manualmente:

#### 1. Extrair áudio

```bash
python .claude/skills/youtube-video-pipeline/scripts/extract_audio.py video.mp4
# Gera: video.mp3
```

#### 2. Transcrever áudio

```bash
# Transcrição simples
python .claude/skills/youtube-video-pipeline/scripts/transcribe_audio.py video.mp3 -o transcricao.txt

# Com timestamps
python .claude/skills/youtube-video-pipeline/scripts/transcribe_audio.py video.mp3 -t -o transcricao.txt

# Para vídeos longos (mais de 24 minutos)
python .claude/skills/youtube-video-pipeline/scripts/transcribe_audio.py video.mp3 -l -o transcricao.txt
```

#### 3. Gerar thumbnail

```bash
python .claude/skills/youtube-video-pipeline/scripts/generate_thumbnail.py "Título do Vídeo" \
    -d "Descrição curta do conteúdo" \
    -r sua_imagem_referencia.jpg \
    -o thumbnail.png
```

#### 4. Upload para YouTube

```bash
python .claude/skills/youtube-video-pipeline/scripts/upload_youtube.py video.mp4 \
    -t "Título do Vídeo" \
    -d "Descrição completa do vídeo" \
    --tags tag1 tag2 tag3 \
    --privacy private
```

**Parâmetros do upload:**
- `-t, --title` - Título do vídeo (obrigatório)
- `-d, --description` - Descrição do vídeo
- `--tags` - Lista de tags separadas por espaço
- `--category` - ID da categoria (padrão: 22 = People & Blogs)
- `--privacy` - `public`, `private` ou `unlisted` (padrão: private)
- `--thumbnail` - Caminho para a thumbnail
- `--from-live` - URL da live original (para clips automáticos)

## Comandos Slash Disponíveis

| Comando | Descrição |
|---------|-----------|
| `/generate_title <arquivo>` | Gera título otimizado a partir da transcrição |
| `/generate_description <arquivo>` | Gera descrição SEO a partir da transcrição |
| `/generate_thumb <título>` | Gera thumbnail viral com IA |
| `/analyze_clips <arquivo>` | Identifica melhores momentos para cortes |
| `/generate-clips <url>` | Pipeline completo de geração de clips |
| `/download-video <url>` | Baixa vídeo do YouTube |
| `/question <pergunta>` | Responde perguntas sobre o projeto |

## Estrutura do Projeto

```
agent-youtube/
├── .claude/
│   ├── commands/                    # Comandos slash customizados
│   │   ├── generate_title.md
│   │   ├── generate_description.md  # ⚠️ Editar: seus links de redes sociais
│   │   ├── generate_thumb.md        # ⚠️ Editar: sua imagem de referência
│   │   ├── analyze_clips.md
│   │   ├── generate-clips.md
│   │   ├── download-video.md
│   │   └── question.md
│   └── skills/
│       ├── youtube-video-pipeline/  # Skill principal
│       │   ├── SKILL.md
│       │   ├── references/
│       │   └── scripts/
│       │       ├── extract_audio.py
│       │       ├── transcribe_audio.py
│       │       ├── generate_thumbnail.py
│       │       ├── upload_youtube.py
│       │       └── extract_clip.py
│       ├── clip-generator/          # Geração automática de clips
│       ├── video-manager/           # Gerenciamento de status dos vídeos
│       ├── env-linux/               # Acesso SSH remoto (opcional)
│       └── skill-creator/           # Utilitário para criar skills
├── .env.example                     # Exemplo de variáveis de ambiente
├── requirements.txt                 # Dependências Python
├── videos_status.json               # Tracking de status dos vídeos
└── README.md
```

## Idiomas Suportados (Transcrição)

O modelo NVIDIA Parakeet TDT v3 suporta 25 idiomas com detecção automática:

| Código | Idioma | Código | Idioma |
|--------|--------|--------|--------|
| pt | Português | en | Inglês |
| es | Espanhol | fr | Francês |
| de | Alemão | it | Italiano |
| nl | Holandês | pl | Polonês |
| ru | Russo | uk | Ucraniano |
| bg | Búlgaro | hr | Croata |
| cs | Tcheco | da | Dinamarquês |
| et | Estoniano | fi | Finlandês |
| el | Grego | hu | Húngaro |
| lv | Letão | lt | Lituano |
| mt | Maltês | ro | Romeno |
| sk | Eslovaco | sl | Esloveno |
| sv | Sueco | | |

## Dicas de Uso

### Títulos que Convertem

- Máximo 60 caracteres
- Use gatilhos: curiosidade, urgência, números, resultados
- Comece com a palavra mais impactante
- Evite clickbait vazio e muitas maiúsculas

### Thumbnails Virais

- Expressões faciais exageradas
- Máximo 3-4 palavras de texto
- Alto contraste de cores
- Resolução: 1280x720 pixels

### SEO para Descrições

- Primeiros 150 caracteres são cruciais
- 200-500 palavras no total
- Inclua CTAs (inscrição, likes, comentários)
- 3-5 hashtags relevantes

## Solução de Problemas

### Erro: "ffmpeg não encontrado"
Instale o FFmpeg seguindo as instruções na seção de instalação.

### Erro: "CUDA out of memory"
O modelo de transcrição requer GPU com pelo menos 8GB de VRAM. Alternativas:
- Use uma máquina remota com GPU via SSH
- Use um serviço de transcrição em nuvem

### Erro: "API key não encontrada"
Verifique se o arquivo `.env` existe e contém `GOOGLE_API_KEY`.

### Erro de autenticação YouTube
1. Delete o arquivo `token.json`
2. Execute o script de upload novamente
3. Autorize o acesso no navegador

## Contribuindo

Contribuições são bem-vindas! Por favor:

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## Autor

**Eduardo Machado**
- LinkedIn: [eduardo-machado-141835192](https://www.linkedin.com/in/eduardo-machado-141835192/)
- GitHub: [eduwxyz](https://github.com/eduwxyz)

---

Feito com Claude Code e muito cafe
