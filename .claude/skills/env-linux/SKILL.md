---
name: env-linux
description: Acesso remoto ao PC Linux via SSH para tarefas que exigem mais poder de processamento. Use esta skill quando precisar executar comandos no ambiente Linux, especialmente para o pipeline de transcrição com NVIDIA Parakeet ou outras tarefas de processamento pesado. O acesso é feito via `ssh linux`.
---

# Ambiente Linux Remoto

## Acesso SSH

Para executar comandos no Linux:

```bash
ssh linux "<comando>"
```

Exemplo:
```bash
ssh linux "cd /caminho/do/projeto && python script.py"
```

## Sessão interativa

Para múltiplos comandos, abra uma sessão:

```bash
ssh linux
```

## Ambiente Virtual (venv)

O projeto possui um venv configurado em `./venv`. Use-o para executar scripts Python:

```bash
# Usar Python do venv diretamente:
./venv/bin/python script.py

# Ou ativar o venv:
source venv/bin/activate
python script.py
```

## Casos de uso

- Pipeline de transcrição com NVIDIA Parakeet (GPU)
- Processamento de vídeo/áudio pesado
- Tarefas que se beneficiam de hardware mais potente
