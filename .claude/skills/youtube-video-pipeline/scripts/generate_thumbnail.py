#!/usr/bin/env python3
"""
Script para gerar thumbnails virais para YouTube usando o modelo Gemini 2.5 Flash Image.

O script analisa o título e descrição do vídeo e gera uma thumbnail otimizada
para maximizar CTR (Click-Through Rate) no YouTube, seguindo as melhores práticas
de criadores como MrBeast, Marques Brownlee e Veritasium.

Requer: pip install google-genai pillow python-dotenv
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Carregar variáveis do .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv é opcional, pode usar variáveis de ambiente diretamente

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Erro: google-genai não instalado. Execute: pip install google-genai")
    sys.exit(1)

try:
    from PIL import Image
    import io
except ImportError:
    print("Erro: Pillow não instalado. Execute: pip install pillow")
    sys.exit(1)


# Configurações de thumbnail do YouTube
YOUTUBE_THUMB_WIDTH = 1280
YOUTUBE_THUMB_HEIGHT = 720

# Imagem de referência padrão do criador do canal
SKILL_DIR = Path(__file__).parent.parent
DEFAULT_REFERENCE_IMAGE = SKILL_DIR / "assets" / "eduardo_reference.png"

# Mapeamento de contextos para poses e expressões apropriadas
# Cada contexto tem palavras-chave que ativam poses/expressões específicas
CONTEXT_POSE_MAP = {
    "automacao": {
        "keywords": ["automatizei", "automatizar", "automação", "automático", "pipeline", "workflow", "agente", "bot"],
        "pose": "mãos abertas apresentando algo invisível, como se mostrasse um sistema funcionando sozinho",
        "expression": "confiante/orgulhoso (sorriso de satisfação, olhar determinado)"
    },
    "descoberta": {
        "keywords": ["descobri", "revelado", "segredo", "encontrei", "achei", "novo"],
        "pose": "uma mão apontando para cima com expressão de 'eureka'",
        "expression": "surpreso/animado (olhos arregalados, sorriso de descoberta)"
    },
    "erro_problema": {
        "keywords": ["erro", "bug", "problema", "falha", "quebrou", "não funciona", "cuidado"],
        "pose": "mãos na cabeça em expressão de 'mind blown'/surpresa extrema",
        "expression": "chocado/preocupado (boca aberta, sobrancelhas levantadas)"
    },
    "tutorial_ensino": {
        "keywords": ["como", "tutorial", "aprenda", "passo a passo", "guia", "completo", "explicando"],
        "pose": "dedos contando (mostrando número) ou apontando para texto explicativo",
        "expression": "amigável/didático (sorriso acolhedor, olhar direto para câmera)"
    },
    "resultado_sucesso": {
        "keywords": ["funciona", "consegui", "resultado", "sucesso", "pronto", "feito", "100%"],
        "pose": "polegar para cima com sorriso largo e olhos animados",
        "expression": "animado/vitorioso (sorriso largo, energia alta)"
    },
    "alerta_importante": {
        "keywords": ["nunca", "sempre", "pare", "atenção", "importante", "urgente", "agora"],
        "pose": "uma mão levantada em gesto de 'espera aí' ou apontando para câmera",
        "expression": "sério/intenso (olhar firme, expressão de autoridade)"
    },
    "comparacao_analise": {
        "keywords": ["vs", "versus", "melhor", "pior", "comparando", "qual", "diferença"],
        "pose": "braços cruzados com postura analítica, cabeça levemente inclinada",
        "expression": "pensativo/avaliador (sobrancelha levantada, expressão de análise)"
    },
    "ia_tech": {
        "keywords": ["ia", "ai", "gpt", "claude", "gemini", "modelo", "llm", "inteligência artificial"],
        "pose": "inclinado para frente com expressão de fascínio, como se olhasse algo impressionante",
        "expression": "impressionado/fascinado (olhos brilhantes, expressão de admiração)"
    }
}

# Fallback para quando nenhum contexto específico é detectado
DEFAULT_POSE = "duas mãos apontando para o texto/título com expressão engajada"
DEFAULT_EXPRESSION = "animado/empolgado (sorriso natural, olhar direto para câmera)"


def select_pose_for_context(title: str, description: str) -> tuple[str, str]:
    """
    Seleciona pose e expressão baseadas no contexto do título e descrição.

    Args:
        title: Título do vídeo
        description: Descrição do vídeo

    Returns:
        Tupla (pose, expression) mais apropriada para o contexto
    """
    text = f"{title} {description}".lower()

    # Procura por contextos que combinem com o conteúdo
    matched_contexts = []
    for context_name, context_data in CONTEXT_POSE_MAP.items():
        for keyword in context_data["keywords"]:
            if keyword in text:
                matched_contexts.append((context_name, context_data))
                break

    if matched_contexts:
        # Se múltiplos contextos, prioriza o primeiro encontrado (mais específico)
        # Poderia também combinar ou escolher o com mais keywords matches
        best_match = matched_contexts[0][1]
        return best_match["pose"], best_match["expression"]

    return DEFAULT_POSE, DEFAULT_EXPRESSION


def extract_power_words(title: str) -> str:
    """
    Extrai 1-2 palavras de maior impacto do título para usar como texto overlay.
    Máximo 3-4 palavras para manter legibilidade.
    """
    power_triggers = [
        "segredo", "revelado", "chocante", "inacreditável", "descobri",
        "nunca", "sempre", "melhor", "pior", "primeiro", "último",
        "grátis", "fácil", "rápido", "simples", "definitivo", "completo",
        "erro", "erros", "problema", "solução", "hack", "truque",
        "milhões", "mil", "100%", "10x", "automatico", "auto",
        "ia", "ai", "gpt", "agente", "agentes", "sistema", "construí",
        "funciona", "testei", "provei", "mostro", "real", "sozinho",
        "detecta", "bugs", "bug", "orquestrador"
    ]

    words = title.lower().replace(":", " ").replace("-", " ").replace("(", " ").replace(")", " ").split()

    found_power = []
    for word in words:
        clean_word = ''.join(c for c in word if c.isalnum())
        if clean_word in power_triggers:
            found_power.append(clean_word.upper())

    if found_power:
        return " ".join(found_power[:3])

    significant = [w for w in words if len(w) > 4]
    return " ".join(significant[:2]).upper() if significant else words[0].upper()


def create_viral_prompt(title: str, description: str) -> str:
    """
    Cria um prompt baseado no template do prompt-thumbnail-viral.md
    """

    prompt = f"""YouTube thumbnail,
Título do vídeo: "{title}"
Resumo do conteúdo: {description}
Tom do canal: educativo tech/IA
Público-alvo: desenvolvedores, entusiastas de tecnologia
Tem pessoa no vídeo: sim (homem jovem brasileiro com óculos)
Estilo visual: clean, fundo escuro, texto grande amarelo

Rosto humano com expressão facial exagerada e autêntica (olhos arregalados, boca aberta, sobrancelhas levantadas),
Cores vibrantes com máximo 3 cores dominantes com alto contraste,
Texto mínimo 3-4 palavras no máximo fonte bold e legível,
high contrast, bold composition,
professional photography style,
16:9 aspect ratio,
hyper detailed, sharp focus,
dramatic lighting,
viral YouTube aesthetic"""

    return prompt


def generate_thumbnail(
    title: str,
    description: str,
    output_path: str = None,
    reference_image: str = None,
    api_key: str = None
) -> str:
    """
    Gera uma thumbnail viral otimizada para YouTube.

    Args:
        title: Título do vídeo
        description: Descrição do vídeo
        output_path: Caminho para salvar a thumbnail (opcional)
        reference_image: Caminho para imagem de referência (para consistência de rosto).
                        Se não fornecido, usa a referência padrão em assets/eduardo_reference.png
        api_key: API key do Google AI (ou usar GOOGLE_API_KEY env var)

    Returns:
        Caminho do arquivo de thumbnail gerado
    """
    # Usar referência padrão se não fornecida e existir
    if reference_image is None and DEFAULT_REFERENCE_IMAGE.exists():
        reference_image = str(DEFAULT_REFERENCE_IMAGE)
        print(f"Usando referência padrão: {reference_image}")

    # Configurar API key
    api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "API key não encontrada. Configure GOOGLE_API_KEY ou GEMINI_API_KEY "
            "ou passe via parâmetro --api-key"
        )

    # Criar cliente
    client = genai.Client(api_key=api_key)

    # Criar prompt viral otimizado
    prompt = create_viral_prompt(title, description)

    print(f"Gerando thumbnail viral para: {title}")
    print(f"Power words: {extract_power_words(title)}")

    # Preparar conteúdo da requisição
    contents = []

    # Adicionar imagem de referência se fornecida
    if reference_image:
        ref_path = Path(reference_image)
        if ref_path.exists():
            print(f"Usando imagem de referência: {reference_image}")
            with open(ref_path, "rb") as f:
                image_bytes = f.read()

            # Detectar tipo MIME
            mime_type = "image/jpeg"
            if ref_path.suffix.lower() == ".png":
                mime_type = "image/png"
            elif ref_path.suffix.lower() == ".webp":
                mime_type = "image/webp"

            contents.append(
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            )

            # Selecionar pose e expressão baseadas no contexto do título/descrição
            selected_pose, selected_expression = select_pose_for_context(title, description)
            print(f"Pose selecionada (contextual): {selected_pose}")
            print(f"Expressão selecionada (contextual): {selected_expression}")

            prompt = f"""REFERÊNCIA OBRIGATÓRIA: Use esta imagem como base para a APARÊNCIA da pessoa (rosto, tom de pele, cabelo).

INSTRUÇÕES CRÍTICAS:
- ROSTO: MANTENHA o rosto IDÊNTICO à referência (formato do rosto, nariz, olhos, sobrancelhas, tom de pele moreno, cabelo curto cacheado)
- ÓCULOS: REMOVA OS ÓCULOS - a pessoa NÃO usa óculos
- ROUPA: MANTENHA a camiseta preta
- ESTILO VISUAL: MANTENHA o fundo azul escuro com circuitos tech, texto amarelo grande
- COMPOSIÇÃO: MANTENHA pessoa à esquerda, texto à direita

POSE E EXPRESSÃO (DIFERENTE DA REFERÊNCIA):
- POSE: {selected_pose}
- EXPRESSÃO FACIAL: {selected_expression}

IMPORTANTE: A pose e expressão devem ser DIFERENTES da imagem de referência. Use a referência apenas para manter a identidade visual da pessoa (rosto, tom de pele, cabelo), mas MUDE a pose e expressão conforme especificado acima.

Estilo: foto realista profissional com elementos gráficos
NÃO faça cartoon/ilustração - mantenha o estilo FOTOREALISTA.

{prompt}"""
        else:
            print(f"Aviso: Imagem de referência não encontrada: {reference_image}")

    contents.append(prompt)

    # Gerar imagem
    print("Enviando requisição para o modelo Gemini 3 Pro Image...")

    try:
        response = client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["image", "text"],
                temperature=1.0,
            )
        )
    except Exception as e:
        raise RuntimeError(f"Erro ao gerar imagem: {e}")

    # Extrair imagem da resposta
    image_data = None
    for part in response.candidates[0].content.parts:
        if hasattr(part, "inline_data") and part.inline_data:
            image_data = part.inline_data.data
            break

    if not image_data:
        # Tentar extrair texto de erro ou resposta
        text_response = ""
        for part in response.candidates[0].content.parts:
            if hasattr(part, "text"):
                text_response += part.text
        raise RuntimeError(f"Nenhuma imagem gerada. Resposta do modelo: {text_response}")

    # Decodificar e processar imagem
    image = Image.open(io.BytesIO(image_data))

    # Redimensionar para tamanho correto do YouTube se necessário
    if image.size != (YOUTUBE_THUMB_WIDTH, YOUTUBE_THUMB_HEIGHT):
        print(f"Redimensionando de {image.size} para {YOUTUBE_THUMB_WIDTH}x{YOUTUBE_THUMB_HEIGHT}")
        image = image.resize(
            (YOUTUBE_THUMB_WIDTH, YOUTUBE_THUMB_HEIGHT),
            Image.Resampling.LANCZOS
        )

    # Definir caminho de saída
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c if c.isalnum() else "_" for c in title[:30])
        output_path = f"thumbnail_{safe_title}_{timestamp}.png"

    output_path = Path(output_path)

    # Salvar imagem
    # Converter para RGB se necessário (para salvar como JPG)
    if output_path.suffix.lower() in (".jpg", ".jpeg"):
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        image.save(output_path, "JPEG", quality=95)
    else:
        image.save(output_path, "PNG")

    print(f"Thumbnail salva em: {output_path}")
    print(f"Tamanho: {image.size[0]}x{image.size[1]} pixels")

    return str(output_path)


def main():
    if len(sys.argv) < 2:
        print("Uso: python generate_thumbnail.py <título> [opções]")
        print()
        print("Gera thumbnails virais otimizadas para YouTube seguindo as melhores")
        print("práticas de criadores como MrBeast, Marques Brownlee e Veritasium.")
        print()
        print("Argumentos:")
        print("  <título>                    Título do vídeo (obrigatório)")
        print()
        print("Opções:")
        print("  -d, --description <texto>   Descrição do vídeo")
        print("  -o, --output <arquivo>      Caminho para salvar a thumbnail")
        print("  -r, --reference <imagem>    Imagem de referência (para consistência de rosto)")
        print("  -k, --api-key <key>         API key do Google AI")
        print()
        print("Exemplos:")
        print('  python generate_thumbnail.py "Como ganhar dinheiro com IA"')
        print('  python generate_thumbnail.py "Tutorial Python" -d "Aprenda Python do zero"')
        print('  python generate_thumbnail.py "React em 2025" -r minha_foto.jpg -o thumb.png')
        print()
        print("Variáveis de ambiente:")
        print("  GOOGLE_API_KEY ou GEMINI_API_KEY - API key do Google AI")
        sys.exit(1)

    title = sys.argv[1]
    description = ""
    output_path = None
    reference_image = None
    api_key = None

    # Parse argumentos
    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] in ("-d", "--description"):
            description = args[i + 1]
            i += 2
        elif args[i] in ("-o", "--output"):
            output_path = args[i + 1]
            i += 2
        elif args[i] in ("-r", "--reference"):
            reference_image = args[i + 1]
            i += 2
        elif args[i] in ("-k", "--api-key"):
            api_key = args[i + 1]
            i += 2
        else:
            # Se não for uma flag, pode ser parte da descrição
            if not description:
                description = args[i]
            i += 1

    try:
        output_file = generate_thumbnail(
            title=title,
            description=description,
            output_path=output_path,
            reference_image=reference_image,
            api_key=api_key
        )
        print(f"\nThumbnail viral gerada com sucesso!")
        print(f"Arquivo: {output_file}")
    except ValueError as e:
        print(f"Erro de configuração: {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"Erro ao gerar: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Erro inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
