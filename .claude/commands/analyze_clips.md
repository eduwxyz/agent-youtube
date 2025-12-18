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

### Parâmetros:
- Duração máxima por corte: $ARGUMENTS.duracao_max minutos (padrão: 3 minutos)
- Quantidade máxima de cortes: $ARGUMENTS.quantidade (padrão: 5 cortes)

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

Analise agora a transcrição e identifique os melhores cortes.
