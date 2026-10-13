"""Regras simples de adaptação usadas pelo protótipo TEApoio.

Não há inteligência artificial neste módulo. Na V2, ele recebe o texto real
reconhecido pelo OCR (e revisado pela pessoa usuária) e aplica regras locais.
"""

import re

EXERCICIO_ORIGINAL = (
    "João foi ao mercado e comprou 3 caixas de lápis. Cada caixa possui 12 lápis. "
    "Quantos lápis João comprou ao todo?"
)


def adaptar_exercicio(texto: str, preferencias: list[str]) -> tuple[str, list[str]]:
    """Adapta ``texto`` usando regras simples conforme as preferências.

    Esta é uma adaptação baseada em regras, sem IA. O texto de entrada é sempre
    preservado para que a atividade original não seja alterada silenciosamente.
    """
    texto = " ".join(texto.split())
    partes: list[str] = []
    adaptacoes: list[str] = []

    if "instrucoes_curtas" in preferencias:
        frases = [frase.strip() for frase in re.split(r"(?<=[.!?])\s+", texto) if frase.strip()]
        partes.append("INSTRUÇÕES CURTAS\n" + "\n".join(f"• {frase}" for frase in frases))
        adaptacoes.append("Instruções mais curtas")

    if "linguagem_direta" in preferencias:
        partes.append("LINGUAGEM DIRETA\nLeia a atividade e responda ao que é pedido:\n" + texto)
        adaptacoes.append("Linguagem mais direta")

    if "destacar_informacoes" in preferencias:
        numeros = re.findall(r"\d+(?:[.,]\d+)?", texto)
        destaque = "• Números encontrados: " + ", ".join(numeros) if numeros else "• Leia com atenção o que a pergunta solicita."
        partes.append("INFORMAÇÕES IMPORTANTES\n" + destaque)
        adaptacoes.append("Informações importantes destacadas")

    if "dividir_etapas" in preferencias:
        partes.append(
            "ETAPA 1\nLeia a atividade com calma.\n\n"
            "ETAPA 2\nIdentifique as informações importantes e a pergunta.\n\n"
            "ETAPA 3\nResolva e escreva sua resposta."
        )
        adaptacoes.append("Atividade dividida em etapas")

    if "apresentar_exemplo" in preferencias:
        partes.append(
            "EXEMPLO\nSe a pergunta pedir um total, organize os dados antes de calcular.\n"
            "Exemplo: 2 grupos com 5 itens cada = 2 × 5 = 10 itens."
        )
        adaptacoes.append("Exemplo de multiplicação apresentado")

    if not partes:
        partes.append(texto)

    return "\n\n".join(partes), adaptacoes
