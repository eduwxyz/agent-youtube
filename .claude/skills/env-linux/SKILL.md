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

## Casos de uso

- Pipeline de transcrição com NVIDIA Parakeet (GPU)
- Processamento de vídeo/áudio pesado
- Tarefas que se beneficiam de hardware mais potente
