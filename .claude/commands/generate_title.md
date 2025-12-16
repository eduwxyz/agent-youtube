---
description: Gera um título chamativo para vídeo do YouTube
arguments:
  - name: arquivo
    description: Caminho para o arquivo txt com o conteúdo/roteiro do vídeo
    required: true
---

Leia o arquivo $ARGUMENTS.arquivo e analise seu conteúdo.

Com base no conteúdo, gere APENAS 1 título para um vídeo do YouTube seguindo estas regras:

## Regras para títulos chamativos:

1. **Máximo de 60 caracteres** - Títulos muito longos são cortados
2. **Use gatilhos mentais**:
   - Curiosidade: "O que ninguém te conta sobre..."
   - Urgência: "Antes que seja tarde..."
   - Exclusividade: "O segredo que..."
   - Números: "5 formas de...", "Em 10 minutos..."
   - Resultados: "Como eu consegui..."

3. **Evite**:
   - Clickbait vazio (promessas que o vídeo não entrega)
   - Títulos genéricos
   - Muitas maiúsculas (parece spam)

4. **Técnicas eficazes**:
   - Comece com a palavra mais impactante
   - Use parênteses para adicionar contexto: "... (funciona mesmo)"
   - Mencione o benefício principal
   - Crie tensão ou conflito

## Formato de saída:

Mostre apenas:
- O título final escolhido
- Breve explicação de por que ele funciona
