"""Formatação segura do exercício adaptado para exibição e cópia."""

import re


_NUMERO = re.compile(
    r"R\$\s*(?:\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:[.,]\d+)?)%?"
    r"|(?:\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:[.,]\d+)?)%?"
)
_DATA = re.compile(r"\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b")
_TITULO_ESTRUTURAL = re.compile(
    r"^\s*(?:#+\s*)?(?:exerc[ií]cio|quest[aã]o|atividade|p[aá]gina|cap[ií]tulo)\s*(?:n[ºo.]?\s*)?$",
    re.IGNORECASE,
)
_PALAVRAS_DE_QUANTIDADE = re.compile(
    r"\b(?:tem|tinha|há|possui|comprou|arrecadou|recebeu|vende|custa|divid|some|adicione|retire|total|cada|entre)\w*\b",
    re.IGNORECASE,
)
_PALAVRAS_SEM_UNIDADE = {"de", "do", "da", "dos", "das", "em", "e", "ou", "para", "por", "com", "no", "na"}


def _eh_identificador_estrutural(linha: str, inicio: int, fim: int) -> bool:
    antes = linha[:inicio]
    depois = linha[fim:]
    if _TITULO_ESTRUTURAL.fullmatch(antes):
        return True
    if re.fullmatch(r"\s*", antes) and re.match(r"[.)]\s+", depois):
        return True
    if re.fullmatch(r"\s*[a-zA-Z]", antes) and re.match(r"[.)]\s+", depois):
        return True
    return False


def _tem_unidade_ou_quantidade(linha: str, fim: int) -> bool:
    depois = linha[fim:]
    palavra = re.match(r"\s+([A-Za-zÀ-ÿ]+)", depois)
    if palavra and palavra.group(1).casefold() not in _PALAVRAS_SEM_UNIDADE:
        return True
    return bool(_PALAVRAS_DE_QUANTIDADE.search(linha))


def _esta_em_expressao(linha: str, inicio: int, fim: int) -> bool:
    contexto = linha[max(0, inicio - 4):min(len(linha), fim + 4)]
    return bool(re.search(r"[+−–—×*/=<>]", contexto))


def _expandir_negrito(texto: str, inicio: int, fim: int) -> tuple[int, int]:
    if texto[max(0, inicio - 2):inicio] == "**" and texto[fim:fim + 2] == "**":
        return inicio - 2, fim + 2
    return inicio, fim


def _numeros_relevantes(texto: str) -> list[tuple[int, int, str]]:
    """Seleciona números de conteúdo e evita títulos, questões e etapas estruturais."""
    selecionados: list[tuple[int, int, str]] = []
    deslocamento = 0
    for linha in texto.splitlines(keepends=True):
        sem_quebra = linha.rstrip("\r\n")
        datas = list(_DATA.finditer(sem_quebra))
        for achado in _NUMERO.finditer(sem_quebra):
            inicio, fim = achado.span()
            valor = achado.group()
            if _eh_identificador_estrutural(sem_quebra, inicio, fim):
                continue
            relevante = (
                valor.startswith("R$")
                or valor.endswith("%")
                or any(data.start() <= inicio and fim <= data.end() for data in datas)
                or _esta_em_expressao(sem_quebra, inicio, fim)
                or _tem_unidade_ou_quantidade(sem_quebra, fim)
            )
            if relevante:
                inicio_expandido, fim_expandido = _expandir_negrito(texto, deslocamento + inicio, deslocamento + fim)
                selecionados.append((inicio_expandido, fim_expandido, valor))
        deslocamento += len(linha)
    return selecionados


def markdown_com_numeros_destacados(texto: str) -> str:
    """Acrescenta cor e negrito apenas aos números relevantes, sem interpretar HTML do modelo."""
    resultado = texto
    spans_usados: set[tuple[int, int]] = set()
    for inicio, fim, valor in sorted(_numeros_relevantes(texto), reverse=True):
        if (inicio, fim) in spans_usados:
            continue
        spans_usados.add((inicio, fim))
        resultado = f"{resultado[:inicio]}:blue[**{valor}**]{resultado[fim:]}"
    return resultado


def texto_puro_para_copia(texto: str) -> str:
    """Remove marcação visual, preservando palavras, números e quebras de linha."""
    resultado = re.sub(r"</?[A-Za-z][^>]*>", "", texto)
    resultado = re.sub(r":[A-Za-z_-]+\[([^\]]*)\]", r"\1", resultado)
    resultado = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", resultado)
    resultado = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", resultado)
    resultado = re.sub(r"^\s{0,3}#{1,6}\s+", "", resultado, flags=re.MULTILINE)
    resultado = re.sub(r"^\s*>\s?", "", resultado, flags=re.MULTILINE)
    resultado = re.sub(r"^\s*[-+*]\s+", "", resultado, flags=re.MULTILINE)
    resultado = re.sub(r"\*\*(.*?)\*\*", r"\1", resultado)
    resultado = re.sub(r"__(.*?)__", r"\1", resultado)
    resultado = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"\1", resultado)
    resultado = re.sub(r"(?<!_)_([^_\n]+)_(?!_)", r"\1", resultado)
    return resultado.strip()
