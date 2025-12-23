#!/usr/bin/env python3
"""
Script para upload de vídeos no YouTube usando a API v3.
Atualiza automaticamente o videos_status.json após upload.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from google.oauth2.credentials import Credentials

# Adiciona o diretório do video-manager ao path
VIDEO_MANAGER_PATH = Path(__file__).parent.parent.parent / 'video-manager' / 'scripts'
sys.path.insert(0, str(VIDEO_MANAGER_PATH))
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Escopos necessários para upload e thumbnails
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube'  # Necessário para thumbnails
]

# Arquivo de credenciais OAuth
CLIENT_SECRETS_FILE = 'client_secret_851594216922-jr9e7d1eaocgpn0mtamsldmmsq7ga5nl.apps.googleusercontent.com.json'
TOKEN_FILE = 'token.json'

# Arquivo de status dos vídeos
STATUS_FILE = Path(__file__).parent.parent.parent.parent.parent / 'videos_status.json'


def update_video_status(video_file: str, youtube_url: str, title: str = None, has_thumbnail: bool = False, scheduled_at: str = None):
    """
    Atualiza o status do vídeo no videos_status.json após upload.

    Args:
        video_file: Caminho do arquivo de vídeo
        youtube_url: URL do vídeo no YouTube
        title: Título do vídeo (opcional)
        has_thumbnail: Se thumbnail foi enviada
        scheduled_at: Data de agendamento (se for upload agendado)
    """
    if not STATUS_FILE.exists():
        print(f"Aviso: Arquivo de status não encontrado: {STATUS_FILE}")
        return

    try:
        with open(STATUS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Procura o vídeo pelo caminho
        video_path = str(video_file)
        found = False

        # Determina status baseado em se é agendado ou não
        is_scheduled = scheduled_at is not None
        status = 'scheduled' if is_scheduled else 'published'

        for video in data['videos']:
            # Compara pelo caminho completo ou relativo
            if video['file_path'] in video_path or video_path.endswith(video['file_path']):
                video['status'] = status
                video['youtube_url'] = youtube_url
                if is_scheduled:
                    # Extrai apenas a data do ISO 8601 (ex: 2025-12-22T10:00:00-03:00 -> 2025-12-22)
                    video['scheduled_at'] = scheduled_at[:10] if len(scheduled_at) >= 10 else scheduled_at
                    video['published_at'] = None
                else:
                    video['published_at'] = datetime.now().strftime("%Y-%m-%d")
                if has_thumbnail:
                    video['has_thumbnail'] = True
                if title:
                    video['title'] = title
                found = True
                print(f"Status atualizado para: {video['id']} ({status})")
                break

        if not found:
            # Adiciona novo registro se não encontrou
            video_name = Path(video_file).stem
            new_video = {
                "id": video_name.lower()[:30],
                "file_path": video_path,
                "title": title or video_name,
                "status": status,
                "has_thumbnail": has_thumbnail,
                "has_transcription": False,
                "has_description": True,
                "published_at": None if is_scheduled else datetime.now().strftime("%Y-%m-%d"),
                "scheduled_at": scheduled_at[:10] if is_scheduled and len(scheduled_at) >= 10 else scheduled_at,
                "youtube_url": youtube_url,
                "notes": "Adicionado automaticamente após upload"
            }
            data['videos'].append(new_video)
            print(f"Novo vídeo adicionado ao tracking: {new_video['id']} ({status})")

        data['last_updated'] = datetime.now().strftime("%Y-%m-%d")

        with open(STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"videos_status.json atualizado!")

    except Exception as e:
        print(f"Aviso: Erro ao atualizar status: {e}")


def get_authenticated_service():
    """Autentica e retorna o serviço do YouTube."""
    credentials = None

    # Verifica se já existe um token salvo
    if os.path.exists(TOKEN_FILE):
        credentials = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # Se não há credenciais válidas, faz o fluxo de autenticação
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            credentials = flow.run_local_server(port=8080)

        # Salva o token para uso futuro
        with open(TOKEN_FILE, 'w') as token:
            token.write(credentials.to_json())

    return build('youtube', 'v3', credentials=credentials)


def upload_thumbnail(video_id: str, thumbnail_path: str):
    """
    Faz upload de uma thumbnail para um vídeo existente.

    Args:
        video_id: ID do vídeo no YouTube
        thumbnail_path: Caminho para o arquivo de imagem da thumbnail

    Returns:
        dict: Resposta da API
    """
    if not os.path.exists(thumbnail_path):
        raise FileNotFoundError(f"Thumbnail não encontrada: {thumbnail_path}")

    youtube = get_authenticated_service()

    print(f"Fazendo upload da thumbnail: {thumbnail_path}")

    media = MediaFileUpload(thumbnail_path, mimetype='image/png')

    response = youtube.thumbnails().set(
        videoId=video_id,
        media_body=media
    ).execute()

    print(f"Thumbnail atualizada com sucesso!")
    return response


def build_description_with_live_info(description: str, live_url: str) -> str:
    """
    Adiciona informações sobre a live original na descrição.

    Args:
        description: Descrição original do vídeo
        live_url: URL da live original no YouTube

    Returns:
        str: Descrição com informações da live adicionadas
    """
    live_section = f"""
---
🤖 **Este vídeo foi gerado e postado automaticamente!**

Este clip foi extraído e publicado de forma 100% automática a partir de uma live usando IA.
O agente identificou os melhores momentos, gerou título, descrição e thumbnail, e fez o upload — tudo sem intervenção humana.

🎬 **Assista a live completa:** {live_url}

---
"""
    return description + "\n" + live_section


def upload_video(
    video_file: str,
    title: str,
    description: str = '',
    tags: list[str] = None,
    category_id: str = '22',  # 22 = People & Blogs
    privacy_status: str = 'private',
    thumbnail_path: str = None,
    publish_at: str = None,
    from_live: str = None
):
    """
    Faz upload de um vídeo para o YouTube.

    Args:
        video_file: Caminho para o arquivo de vídeo
        title: Título do vídeo
        description: Descrição do vídeo
        tags: Lista de tags
        category_id: ID da categoria (22 = People & Blogs)
        privacy_status: 'public', 'private' ou 'unlisted'
        thumbnail_path: Caminho para a thumbnail (opcional)
        publish_at: Data/hora para publicação agendada (formato ISO 8601, ex: 2024-12-22T10:00:00-03:00)
        from_live: URL da live original (se o vídeo foi gerado a partir de um clip de live)

    Returns:
        dict: Resposta da API com informações do vídeo enviado
    """
    if not os.path.exists(video_file):
        raise FileNotFoundError(f"Arquivo não encontrado: {video_file}")

    youtube = get_authenticated_service()

    # Adiciona informações da live na descrição se for um clip
    final_description = description
    if from_live:
        final_description = build_description_with_live_info(description, from_live)
        print(f"Clip de live detectado: {from_live}")

    status_body = {
        'privacyStatus': privacy_status,
        'selfDeclaredMadeForKids': False
    }

    # Se há agendamento, configura publishAt e força private
    if publish_at:
        status_body['privacyStatus'] = 'private'
        status_body['publishAt'] = publish_at
        print(f"Agendado para: {publish_at}")

    body = {
        'snippet': {
            'title': title,
            'description': final_description,
            'tags': tags or [],
            'categoryId': category_id
        },
        'status': status_body
    }

    # Configura o upload com suporte a retomada
    media = MediaFileUpload(
        video_file,
        chunksize=1024*1024,  # 1MB chunks
        resumable=True
    )

    request = youtube.videos().insert(
        part='snippet,status',
        body=body,
        media_body=media
    )

    print(f"Iniciando upload de: {video_file}")
    print(f"Título: {title}")

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload: {int(status.progress() * 100)}%")

    video_id = response['id']
    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"\nUpload concluído!")
    print(f"ID do vídeo: {video_id}")
    print(f"URL: {youtube_url}")

    # Upload thumbnail se fornecida
    if thumbnail_path:
        upload_thumbnail(video_id, thumbnail_path)

    # Atualiza o status no videos_status.json
    update_video_status(
        video_file=video_file,
        youtube_url=youtube_url,
        title=title,
        has_thumbnail=bool(thumbnail_path),
        scheduled_at=publish_at
    )

    return response


def main():
    parser = argparse.ArgumentParser(description='Upload de vídeo para o YouTube')
    parser.add_argument('video', nargs='?', help='Caminho para o arquivo de vídeo')
    parser.add_argument('--title', '-t', help='Título do vídeo')
    parser.add_argument('--description', '-d', default='', help='Descrição do vídeo')
    parser.add_argument('--tags', nargs='+', help='Tags do vídeo')
    parser.add_argument('--category', default='22', help='ID da categoria (padrão: 22)')
    parser.add_argument('--privacy', choices=['public', 'private', 'unlisted'],
                       default='private', help='Status de privacidade')
    parser.add_argument('--thumbnail', help='Caminho para a thumbnail')
    parser.add_argument('--schedule', help='Agendar publicação (formato ISO 8601, ex: 2024-12-22T10:00:00-03:00)')
    parser.add_argument('--from-live', help='URL da live original (para clips gerados automaticamente)')
    parser.add_argument('--set-thumbnail', help='Atualizar thumbnail de vídeo existente (requer --video-id)')
    parser.add_argument('--video-id', help='ID do vídeo para atualizar thumbnail')

    args = parser.parse_args()

    # Modo: atualizar thumbnail de vídeo existente
    if args.set_thumbnail and args.video_id:
        upload_thumbnail(args.video_id, args.set_thumbnail)
        return

    # Modo: upload de vídeo
    if not args.video:
        parser.error('video é obrigatório para upload')
    if not args.title:
        parser.error('--title é obrigatório para upload')

    upload_video(
        video_file=args.video,
        title=args.title,
        description=args.description,
        tags=args.tags,
        category_id=args.category,
        privacy_status=args.privacy,
        thumbnail_path=args.thumbnail,
        publish_at=args.schedule,
        from_live=getattr(args, 'from_live', None)
    )


if __name__ == '__main__':
    main()
