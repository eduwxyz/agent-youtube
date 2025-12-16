#!/bin/bash

# Script para extrair os primeiros 30 segundos de um arquivo de áudio
# Usando ffmpeg

INPUT_FILE="/Users/eduardo/Documents/youtube/agent-youtube/Agentic.mp3"
OUTPUT_FILE="/Users/eduardo/Documents/youtube/agent-youtube/Agentic_30s.mp3"

ffmpeg -i "$INPUT_FILE" -t 30 -c copy "$OUTPUT_FILE"

echo "Arquivo criado: $OUTPUT_FILE"
