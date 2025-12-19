---
description: Analisa transcrição de live/vídeo longo e identifica cortes potenciais
arguments:
  - name: arquivo
    description: Caminho para o arquivo txt com a transcrição (com timestamps)
    required: true
  - name: duracao_max
    description: Duração máxima de cada corte em minutos (padrão 3)
    required: false
  - name: quantidade
    description: Quantidade máxima de cortes a identificar (padrão 5)
    required: false
---

Leia o arquivo $ARGUMENTS.arquivo que contém a transcrição de um vídeo longo (live, podcast, etc.) COM TIMESTAMPS.

O formato esperado dos timestamps é:
```
[texto da transcrição]

--- Timestamps ---
0.00s - 5.23s : texto do segmento
5.23s - 12.45s : texto do segmento
...
```

## Sua tarefa:

Analise a transcrição e identifique os **melhores momentos para cortes** que funcionariam como vídeos independentes no YouTube (shorts ou vídeos curtos).

### Critérios para identificar bons cortes:

1. **Completude narrativa** - O trecho deve ter início, meio e fim. Deve fazer sentido isoladamente.

2. **Gatilhos de engajamento**:
   - Histórias pessoais com lição
   - Momentos de humor/ironia
   - Revelações surpreendentes ("plot twists")
   - Dicas práticas e acionáveis
   - Opiniões controversas ou polêmicas
   - Momentos emocionais intensos
   - Explicações de conceitos complexos de forma simples

3. **Potencial viral**:
   - Frases de efeito ("quotables")
   - Momentos que geram identificação
   - Conteúdo que provoca reação (concordância ou discordância)
   - Informações exclusivas ou pouco conhecidas

4. **Qualidade técnica**:
   - Evite cortes que começam ou terminam no meio de uma frase
   - Prefira transições naturais
   - O corte deve ser auto-contido (não precisa de contexto anterior)

5. **SEM LIMITE DE DURAÇÃO**:
   - O clip pode ter 30 segundos ou 15 minutos
   - O que importa é o conteúdo fazer sentido COMPLETO
   - Se uma explicação/história leva 10 minutos, inclua os 10 minutos
   - Não corte conteúdo valioso só para caber em um tempo arbitrário

### Parâmetros:
- Quantidade máxima de cortes: $ARGUMENTS.quantidade (padrão: 10 cortes)

## Formato de saída OBRIGATÓRIO:

Para cada corte identificado, retorne no formato JSON:

```json
{
  "cortes": [
    {
      "numero": 1,
      "inicio_segundos": 125.5,
      "fim_segundos": 245.8,
      "duracao_estimada": "2:00",
      "titulo_sugerido": "Título chamativo para o corte",
      "gancho": "Primeira frase impactante que prende a atenção",
      "resumo": "Breve descrição do que acontece no corte",
      "potencial_viral": "alto|medio|baixo",
      "justificativa": "Por que este corte funcionaria bem",
      "tags": ["tag1", "tag2", "tag3"]
    }
  ],
  "total_cortes": 5,
  "observacoes": "Observações gerais sobre o conteúdo e potencial de cortes"
}
```

## Regras importantes:

1. **SEMPRE** use os timestamps exatos da transcrição
2. Ajuste início/fim para não cortar falas no meio
3. Priorize qualidade sobre quantidade - se houver poucos bons momentos, retorne menos cortes
4. O título sugerido deve seguir as mesmas regras de títulos virais (max 60 chars, gatilhos mentais)
5. Ordene os cortes do MELHOR para o pior (por potencial viral)

## Após a análise:

1. **Salve o JSON** em `clips.json` na raiz do projeto
2. **Extraia os clips** automaticamente usando:
   ```bash
   # Linux:
   ./venv/bin/python .claude/skills/youtube-video-pipeline/scripts/extract_clip.py VIDEO.mp4 --clips clips.json

   # macOS:
   python .claude/skills/youtube-video-pipeline/scripts/extract_clip.py VIDEO.mp4 --clips clips.json
   ```
   (substitua VIDEO.mp4 pelo arquivo de vídeo correspondente à transcrição)

**IMPORTANTE:** O Claude Code faz a análise diretamente. NÃO use o script analyze_clips.py (que usa Gemini).

Analise agora a transcrição e identifique os melhores cortes.
