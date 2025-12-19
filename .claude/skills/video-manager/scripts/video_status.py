#!/usr/bin/env python3
"""
Script para gerenciar o status dos vídeos do canal YouTube.
Manipula o arquivo videos_status.json na raiz do projeto.
"""

import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path

# Caminho do arquivo de status (relativo à raiz do projeto)
STATUS_FILE = Path(__file__).parent.parent.parent.parent.parent / 'videos_status.json'


def load_status() -> dict:
    """Carrega o arquivo de status."""
    if not STATUS_FILE.exists():
        return {
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "videos": [],
            "status_legend": {
                "draft": "Vídeo bruto, sem processamento",
                "processing": "Em processo de transcrição/thumbnail/descrição",
                "ready": "Pronto para publicar (pode faltar alguns assets)",
                "scheduled": "Agendado para publicação",
                "published": "Já publicado no YouTube"
            }
        }

    with open(STATUS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_status(data: dict):
    """Salva o arquivo de status."""
    data['last_updated'] = datetime.now().strftime("%Y-%m-%d")
    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Status salvo em: {STATUS_FILE}")


def generate_id(file_path: str) -> str:
    """Gera um ID baseado no caminho do arquivo."""
    name = Path(file_path).stem
    # Remove caracteres especiais e limita o tamanho
    clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', name)[:30]
    return clean_name.lower()


def find_video(data: dict, video_id: str) -> tuple[int, dict] | tuple[None, None]:
    """Encontra um vídeo pelo ID."""
    for i, video in enumerate(data['videos']):
        if video['id'] == video_id:
            return i, video
    return None, None


def cmd_list(args):
    """Lista vídeos, opcionalmente filtrados por status."""
    data = load_status()
    videos = data['videos']

    if args.status:
        videos = [v for v in videos if v['status'] == args.status]

    if not videos:
        print(f"Nenhum vídeo encontrado" + (f" com status '{args.status}'" if args.status else ""))
        return

    # Agrupa por status
    by_status = {}
    for v in videos:
        status = v['status']
        if status not in by_status:
            by_status[status] = []
        by_status[status].append(v)

    status_order = ['published', 'scheduled', 'ready', 'processing', 'draft']

    for status in status_order:
        if status not in by_status:
            continue

        print(f"\n{'='*60}")
        print(f" {status.upper()} ({len(by_status[status])} vídeos)")
        print(f"{'='*60}")

        for v in by_status[status]:
            assets = []
            if v.get('has_thumbnail'): assets.append('thumb')
            if v.get('has_transcription'): assets.append('transcr')
            if v.get('has_description'): assets.append('desc')

            assets_str = f" [{', '.join(assets)}]" if assets else ""
            url_str = f" -> {v['youtube_url']}" if v.get('youtube_url') else ""
            scheduled_str = f" (agendado: {v['scheduled_at']})" if v.get('scheduled_at') else ""

            print(f"  [{v['id']}] {v['title'][:50]}{assets_str}{url_str}{scheduled_str}")


def cmd_add(args):
    """Adiciona um novo vídeo ao tracking."""
    data = load_status()

    video_id = args.id or generate_id(args.file)

    # Verifica se já existe
    if find_video(data, video_id)[0] is not None:
        print(f"Erro: Vídeo com ID '{video_id}' já existe")
        return

    new_video = {
        "id": video_id,
        "file_path": args.file,
        "title": args.title or Path(args.file).stem,
        "status": args.status or "draft",
        "has_thumbnail": False,
        "has_transcription": False,
        "has_description": False,
        "published_at": None,
        "scheduled_at": None,
        "youtube_url": None,
        "notes": args.notes or ""
    }

    data['videos'].append(new_video)
    save_status(data)
    print(f"Vídeo adicionado: {video_id}")


def cmd_update(args):
    """Atualiza um vídeo existente."""
    data = load_status()

    idx, video = find_video(data, args.video_id)
    if idx is None:
        print(f"Erro: Vídeo '{args.video_id}' não encontrado")
        return

    # Atualiza campos fornecidos
    if args.status:
        video['status'] = args.status
    if args.title:
        video['title'] = args.title
    if args.youtube_url:
        video['youtube_url'] = args.youtube_url
    if args.published_at:
        video['published_at'] = args.published_at
    if args.scheduled_at:
        video['scheduled_at'] = args.scheduled_at
    if args.notes:
        video['notes'] = args.notes

    # Flags de assets
    if args.has_thumbnail is not None:
        video['has_thumbnail'] = args.has_thumbnail.lower() == 'true'
    if args.has_transcription is not None:
        video['has_transcription'] = args.has_transcription.lower() == 'true'
    if args.has_description is not None:
        video['has_description'] = args.has_description.lower() == 'true'

    data['videos'][idx] = video
    save_status(data)
    print(f"Vídeo atualizado: {args.video_id}")


def cmd_remove(args):
    """Remove um vídeo do tracking."""
    data = load_status()

    idx, video = find_video(data, args.video_id)
    if idx is None:
        print(f"Erro: Vídeo '{args.video_id}' não encontrado")
        return

    data['videos'].pop(idx)
    save_status(data)
    print(f"Vídeo removido: {args.video_id}")


def cmd_summary(args):
    """Mostra resumo do status dos vídeos."""
    data = load_status()
    videos = data['videos']

    # Conta por status
    counts = {}
    for v in videos:
        status = v['status']
        counts[status] = counts.get(status, 0) + 1

    print("\n" + "="*50)
    print(" RESUMO DO CANAL")
    print("="*50)
    print(f" Última atualização: {data.get('last_updated', 'N/A')}")
    print(f" Total de vídeos: {len(videos)}")
    print("-"*50)

    status_order = ['published', 'scheduled', 'ready', 'processing', 'draft']
    status_emoji = {
        'published': 'OK',
        'scheduled': 'AGENDADO',
        'ready': 'PRONTO',
        'processing': 'PROCESSANDO',
        'draft': 'RASCUNHO'
    }

    for status in status_order:
        count = counts.get(status, 0)
        if count > 0:
            print(f" {status_emoji.get(status, status):12} : {count}")

    print("-"*50)

    # Próximos passos sugeridos
    ready = [v for v in videos if v['status'] == 'ready']
    draft = [v for v in videos if v['status'] == 'draft']

    if ready:
        print(f"\n Prontos para publicar:")
        for v in ready[:3]:
            print(f"   - {v['title'][:45]}")

    if draft:
        print(f"\n Precisam de processamento:")
        for v in draft[:3]:
            print(f"   - {v['title'][:45]}")

    print()


def main():
    parser = argparse.ArgumentParser(description='Gerenciador de status de vídeos YouTube')
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponíveis')

    # Comando: list
    list_parser = subparsers.add_parser('list', help='Lista vídeos')
    list_parser.add_argument('--status', '-s',
                            choices=['draft', 'processing', 'ready', 'scheduled', 'published'],
                            help='Filtrar por status')

    # Comando: add
    add_parser = subparsers.add_parser('add', help='Adiciona novo vídeo')
    add_parser.add_argument('--file', '-f', required=True, help='Caminho do arquivo de vídeo')
    add_parser.add_argument('--title', '-t', help='Título do vídeo')
    add_parser.add_argument('--id', help='ID personalizado (gerado automaticamente se omitido)')
    add_parser.add_argument('--status', '-s', default='draft',
                           choices=['draft', 'processing', 'ready', 'scheduled', 'published'],
                           help='Status inicial')
    add_parser.add_argument('--notes', '-n', help='Notas adicionais')

    # Comando: update
    update_parser = subparsers.add_parser('update', help='Atualiza vídeo existente')
    update_parser.add_argument('video_id', help='ID do vídeo')
    update_parser.add_argument('--status', '-s',
                              choices=['draft', 'processing', 'ready', 'scheduled', 'published'],
                              help='Novo status')
    update_parser.add_argument('--title', '-t', help='Novo título')
    update_parser.add_argument('--youtube-url', help='URL do YouTube')
    update_parser.add_argument('--published-at', help='Data de publicação (YYYY-MM-DD)')
    update_parser.add_argument('--scheduled-at', help='Data agendada (YYYY-MM-DD)')
    update_parser.add_argument('--has-thumbnail', help='Tem thumbnail (true/false)')
    update_parser.add_argument('--has-transcription', help='Tem transcrição (true/false)')
    update_parser.add_argument('--has-description', help='Tem descrição (true/false)')
    update_parser.add_argument('--notes', '-n', help='Notas adicionais')

    # Comando: remove
    remove_parser = subparsers.add_parser('remove', help='Remove vídeo do tracking')
    remove_parser.add_argument('video_id', help='ID do vídeo')

    # Comando: summary
    subparsers.add_parser('summary', help='Mostra resumo geral')

    args = parser.parse_args()

    if args.command == 'list':
        cmd_list(args)
    elif args.command == 'add':
        cmd_add(args)
    elif args.command == 'update':
        cmd_update(args)
    elif args.command == 'remove':
        cmd_remove(args)
    elif args.command == 'summary':
        cmd_summary(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
