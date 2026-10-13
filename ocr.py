"""Leitura local de texto em imagens usando Tesseract OCR."""

import os
import shutil
from pathlib import Path

from PIL import Image, UnidentifiedImageError
import pytesseract


class ErroOCR(Exception):
    """Erro com mensagem apropriada para exibir na interface."""


def _configurar_tesseract() -> None:
    """Localiza o executável do Tesseract, inclusive no caminho comum do macOS."""
    caminho = os.environ.get("TESSERACT_CMD") or shutil.which("tesseract")
    if not caminho:
        for candidato in ("/opt/homebrew/bin/tesseract", "/usr/local/bin/tesseract"):
            if Path(candidato).is_file():
                caminho = candidato
                break

    if not caminho:
        raise ErroOCR(
            "O Tesseract OCR não foi encontrado. Verifique se ele está instalado no computador."
        )

    pytesseract.pytesseract.tesseract_cmd = caminho


def ler_texto_imagem(caminho_imagem: str | Path) -> str:
    """Reconhece texto em português e inglês e retorna o resultado editável.

    O processamento é totalmente local. Erros previstos são convertidos em
    mensagens simples para que a interface não mostre rastreamentos técnicos.
    """
    caminho = Path(caminho_imagem)
    if not caminho.is_file():
        raise ErroOCR("Não foi possível encontrar a imagem selecionada.")

    try:
        _configurar_tesseract()
        idiomas = pytesseract.get_languages(config="")
        faltantes = [idioma for idioma in ("por", "eng") if idioma not in idiomas]
        if faltantes:
            raise ErroOCR(
                "O Tesseract não encontrou o idioma "
                f"{', '.join(faltantes)}. Instale os dados de idioma e tente novamente."
            )

        with Image.open(caminho) as imagem:
            return pytesseract.image_to_string(imagem, lang="por+eng").strip()
    except ErroOCR:
        raise
    except (UnidentifiedImageError, OSError) as erro:
        raise ErroOCR("Não foi possível abrir esta imagem para ler o texto.") from erro
    except pytesseract.TesseractNotFoundError as erro:
        raise ErroOCR("O Tesseract OCR não foi encontrado. Verifique a instalação local.") from erro
    except pytesseract.TesseractError as erro:
        raise ErroOCR("O Tesseract não conseguiu ler esta imagem. Tente outra imagem mais nítida.") from erro
    except Exception as erro:
        raise ErroOCR("Ocorreu um erro ao reconhecer o texto da imagem. Tente novamente.") from erro
