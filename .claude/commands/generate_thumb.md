---
description: Gera uma thumbnail viral otimizada para YouTube usando IA
arguments:
  - name: titulo
    description: Título do vídeo (será usado para gerar a thumbnail)
    required: true
  - name: descricao
    description: Descrição ou resumo do conteúdo do vídeo
    required: false
---

Gere uma thumbnail viral otimizada para YouTube com base no título fornecido.

**Título do vídeo:** $ARGUMENTS.titulo

**Descrição:** $ARGUMENTS.descricao

**Imagem de referência para o rosto:** Sempre use `thumbnail_sem_oculos.png` (localizada na raiz do projeto)

## Sua tarefa:

Execute o script `generate_thumbnail.py` para gerar a thumbnail:

```bash
python generate_thumbnail.py "$ARGUMENTS.titulo" -d "$ARGUMENTS.descricao" -r "thumbnail_sem_oculos.png"
```

Ajuste os parâmetros conforme necessário:
- Se não houver descrição, omita o parâmetro `-d`
- **SEMPRE** inclua o parâmetro `-r "thumbnail_sem_oculos.png"` para referência do rosto

## Após a execução:

1. Informe o caminho do arquivo de thumbnail gerado
2. Se houver erros, analise e sugira soluções (ex: API key não configurada, dependências faltando)

## Dicas para thumbnails virais:

- Use expressões faciais exageradas (surpresa, alegria, choque)
- Texto grande e legível (3-4 palavras máximo)
- Alto contraste de cores
- Composição clara com ponto focal definido
- Resolução: 1280x720 pixels (16:9)
