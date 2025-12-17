#!/usr/bin/env python3
"""
Script para upload de vídeos no YouTube usando a API v3.
"""

import argparse
import os
from pathlib import Path

from google.oauth2.credentials import Credentials
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


def upload_video(
    video_file: str,
    title: str,
    description: str = '',
    tags: list[str] = None,
    category_id: str = '22',  # 22 = People & Blogs
    privacy_status: str = 'private',
    thumbnail_path: str = None
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

    Returns:
        dict: Resposta da API com informações do vídeo enviado
    """
    if not os.path.exists(video_file):
        raise FileNotFoundError(f"Arquivo não encontrado: {video_file}")

    youtube = get_authenticated_service()

    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags or [],
            'categoryId': category_id
        },
        'status': {
            'privacyStatus': privacy_status,
            'selfDeclaredMadeForKids': False
        }
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
    print(f"\nUpload concluído!")
    print(f"ID do vídeo: {video_id}")
    print(f"URL: https://www.youtube.com/watch?v={video_id}")

    # Upload thumbnail se fornecida
    if thumbnail_path:
        upload_thumbnail(video_id, thumbnail_path)

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
        thumbnail_path=args.thumbnail
    )


if __name__ == '__main__':
    main()
