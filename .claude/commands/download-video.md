---
description: Baixa um vídeo do YouTube na melhor qualidade
arguments:
  - name: url
    description: URL do vídeo do YouTube
    required: true
---

Execute o script Python para baixar o vídeo do YouTube.

## Tarefa

1. Execute o comando:

**No Linux** (use o venv existente):
```bash
./venv/bin/python download_video.py "$ARGUMENTS.url"
```

**No macOS**:
```bash
python download_video.py "$ARGUMENTS.url"
```

2. Aguarde o download completar e informe ao usuário:
   - Se foi bem sucedido, mostre o nome do arquivo baixado
   - Se falhou, mostre o erro

3. O vídeo será salvo no diretório atual do projeto com o título original do YouTube.
