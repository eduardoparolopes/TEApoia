"""Integração isolada com a Responses API da OpenAI para a futura V4.2."""

import os

from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    OpenAI,
    PermissionDeniedError,
    RateLimitError,
)


MODELO_PADRAO = "gpt-6-luna"


REGRAS_PERMANENTES = """1. Preserve o objetivo pedagógico: a versão adaptada deve trabalhar a mesma habilidade, conceito ou conteúdo do exercício original.
2. Preserve corretamente todo conteúdo essencial: fatos, conceitos, números, quantidades, datas relevantes, nomes, dados,
relações entre informações, alternativas e demais elementos necessários para responder. Não invente nem altere informações.
3. Preserve a resposta correta. Em múltipla escolha, mantenha uma única alternativa correta, coerente com a pergunta, sem
torná-la evidente por tamanho, linguagem, estrutura ou destaque exclusivo.
4. Não resolva a atividade pelo estudante nem revele a resposta direta ou indiretamente por explicações excessivas, dicas
que contenham a solução, exemplos quase idênticos ou destaque da alternativa correta.
5. Preserve o nível pedagógico de acordo com matéria e turma/ano. Simplifique a apresentação sem reduzir a dificuldade
conceitual sem necessidade e sem infantilizar vocabulário, exemplos ou instruções.
6. Mantenha a atividade reconhecível como versão do original. Pode reorganizar linguagem, estrutura e apresentação, mas não
descaracterizar o conteúdo nem criar outra atividade.
7. Não aplique adaptações não solicitadas. Use somente as preferências selecionadas e a orientação livre, além de ajustes
mínimos de clareza e correção.
8. A orientação livre é adicional e complementa as preferências. Se conflitar com qualquer regra permanente, esta regra prevalece.
9. Quando "Adicionar exemplo" estiver selecionado, inclua um único exemplo análogo, curto e útil: mesma habilidade, mas outro
contexto ou estrutura, sem copiar a questão com números ou palavras trocados e sem revelar a resposta principal. Nunca repita
a mesma expressão, equação, formato de pergunta ou operação simbólica apenas com valores diferentes. Em álgebra, use uma
situação cotidiana em palavras, com quantidade inicial desconhecida e mudança, sem uma segunda equação simbólica ou resposta.
10. Retorne somente o exercício adaptado, sem explicar o processo ou usar prefácios. Use Markdown padrão apenas quando ajudar
a leitura: títulos simples, listas numeradas para etapas e **negrito** para informações importantes. Evite excesso de formatação
e nunca use HTML."""


DEFINICOES_PREFERENCIAS = {
    "Linguagem mais direta": "Use comandos claros, explicite a ação esperada e retire rodeios ou introduções desnecessárias, sem remover conteúdo importante nem infantilizar a atividade.",
    "Linguagem mais simples": "Reduza complexidade linguística e sintática com equivalentes acessíveis. Preserve termos técnicos essenciais e explique-os somente quando necessário.",
    "Frases mais curtas": "Prefira uma ideia principal por frase, dividindo períodos longos e mantendo a conexão lógica. Não transforme o conteúdo em tópicos apenas por esta preferência.",
    "Dividir em etapas": "Apresente uma sequência de ações cognitivas ou operacionais específicas e úteis para resolver a atividade. Evite etapas vagas como ‘Leia’, ‘Pense’ e ‘Responda’ e não crie etapas para atividade extremamente simples.",
    "Organizar informações": "Produza mudança estrutural perceptível por tópicos, listas, blocos, categorias, pequenas seções ou tabela Markdown quando adequada. Não basta reescrever o mesmo parágrafo. Mesmo com múltipla escolha, mantenha a organização em dados, blocos ou seções além das alternativas.",
    "Reduzir informações desnecessárias": "Retire redundâncias e trechos acessórios, preservando todos os dados necessários para compreensão, resolução e resposta correta. Não deixe a atividade incompleta ou ambígua.",
    "Destacar números importantes": "Mantenha evidentes somente números relevantes para interpretação ou resolução. Não trate como relevantes identificadores estruturais como ‘Exercício 4’, ‘Questão 2’, páginas ou numeração de etapas. A camada visual da plataforma fará o destaque; não use HTML nem códigos de cor.",
    "Destacar palavras-chave": "Destaque seletivamente conceitos centrais, termos essenciais, ações e relações relevantes. Nunca escolha automaticamente títulos, ‘Etapa 1’, ‘Etapa 2’, ‘Leia’, ‘Responda’, numerações ou rótulos estruturais. Não destaque tantas palavras que o recurso perca a função.",
    "Destacar informações importantes": "Dê ênfase seletiva a condições, relações, dados centrais, regras ou frases indispensáveis. Não destaque quase todo o texto, elementos estruturais ou apenas a alternativa correta.",
    "Destacar a pergunta principal": "Torne evidente, sem mudar o sentido, o que o aluno deve responder. Em atividades com várias perguntas, destaque cada pergunta correspondente e não inclua alternativas no destaque sem necessidade.",
    "Adicionar exemplo": "Aplique a regra permanente de exemplo análogo, curto e adequado à turma somente quando esta preferência estiver selecionada.",
    "Adicionar dica": "Forneça uma orientação curta para começar ou localizar uma informação relevante, sem revelar a resposta, executar cálculos ou eliminar o raciocínio esperado.",
    "Criar apoio visual": "Quando ele ajudar, represente dados por tabela, quadro, esquema, sequência ou agrupamento textual em Markdown. Escolha o formato pelo conteúdo e não busque, gere ou descreva imagens externas nem crie apoio artificial.",
}


class ErroIA(RuntimeError):
    """Erro amigável para a camada de integração com IA."""


def obter_cliente() -> OpenAI:
    """Cria o cliente a partir da variável de ambiente, sem expor a chave."""
    chave = os.getenv("OPENAI_API_KEY")
    if not chave:
        raise ErroIA("A variável de ambiente OPENAI_API_KEY não está configurada.")
    return OpenAI(api_key=chave)


def _traduzir_erro(erro: Exception) -> ErroIA:
    if isinstance(erro, AuthenticationError):
        return ErroIA("Não foi possível autenticar na OpenAI. Verifique a configuração da chave de API.")
    if isinstance(erro, PermissionDeniedError):
        return ErroIA("A chave de API não tem permissão para usar este recurso ou modelo.")
    if isinstance(erro, RateLimitError):
        codigo = getattr(erro, "code", None)
        if codigo == "insufficient_quota":
            return ErroIA("A conta OpenAI não possui créditos disponíveis para esta solicitação.")
        return ErroIA("O limite de uso da OpenAI foi atingido. Tente novamente em instantes.")
    if isinstance(erro, NotFoundError):
        return ErroIA("O modelo solicitado não está disponível para esta conta.")
    if isinstance(erro, BadRequestError):
        mensagem = str(erro).lower()
        if "model" in mensagem:
            return ErroIA("O modelo solicitado não está disponível para esta conta.")
        return ErroIA("A OpenAI recusou a solicitação de adaptação.")
    if isinstance(erro, APITimeoutError):
        return ErroIA("A OpenAI demorou mais do que o esperado para responder. Tente novamente.")
    if isinstance(erro, APIConnectionError):
        return ErroIA("Não foi possível conectar à OpenAI. Verifique a conexão com a internet.")
    if isinstance(erro, APIError):
        return ErroIA("A OpenAI retornou um erro ao processar a solicitação.")
    return ErroIA("Ocorreu um erro inesperado ao comunicar com a OpenAI.")


def testar_conexao() -> str:
    """Envia uma resposta mínima pela Responses API e devolve somente o texto."""
    cliente = obter_cliente()
    try:
        resposta = cliente.responses.create(
            model=MODELO_PADRAO,
            input="Responda apenas: conexão funcionando.",
        )
    except (AuthenticationError, PermissionDeniedError, RateLimitError, NotFoundError, BadRequestError, APIConnectionError, APITimeoutError, APIError) as erro:
        raise _traduzir_erro(erro) from erro

    texto = (resposta.output_text or "").strip()
    if not texto:
        raise ErroIA("A OpenAI respondeu sem texto para o teste de conexão.")
    return texto


def construir_prompt_adaptacao(
    texto_original: str,
    preferencias: list[str],
    instrucao_livre: str = "",
    nome_exercicio: str = "",
    materia: str = "",
    turma_ano: str = "",
) -> str:
    """Monta um prompt com regras permanentes e somente preferências ativas."""
    preferencias_ativas = [preferencia for preferencia in preferencias if preferencia in DEFINICOES_PREFERENCIAS]
    contexto = []
    if nome_exercicio:
        contexto.append(f"Nome do exercício: {nome_exercicio}")
    if materia:
        contexto.append(f"Matéria: {materia}")
    if turma_ano:
        contexto.append(f"Turma/ano: {turma_ano}")
    metadados = "\n".join(contexto) or "Sem informações adicionais."

    requisitos = [f"{indice}. {preferencia}." for indice, preferencia in enumerate(preferencias_ativas, start=1)]
    orientacao = instrucao_livre.strip()
    if orientacao:
        requisitos.append(f"{len(requisitos) + 1}. {orientacao}")
    requisitos_formatados = "\n".join(requisitos) or "Nenhuma adaptação adicional solicitada."

    definicoes_ativas = "\n".join(
        f"- {preferencia}: {DEFINICOES_PREFERENCIAS[preferencia]}" for preferencia in preferencias_ativas
    ) or "Nenhuma preferência nativa selecionada."
    secao_orientacao = f"\nINSTRUÇÃO PERSONALIZADA DO PROFESSOR:\n{orientacao}\n" if orientacao else ""

    return f"""PAPEL:
Você adapta atividades pedagógicas para professores no TEApoia.

REGRAS PERMANENTES — obedecidas em toda adaptação, acima de preferências e orientação livre:
{REGRAS_PERMANENTES}

DADOS DO EXERCÍCIO:
{metadados}

Exercício original:
---
{texto_original.strip()}
---

REQUISITOS DESTA ADAPTAÇÃO:
Todos os requisitos abaixo são obrigatórios. Não escolha entre eles e não substitua um pelo outro.
Cada preferência selecionada deve produzir seu próprio efeito; a instrução personalizada é adicional.
{requisitos_formatados}

DEFINIÇÕES DAS PREFERÊNCIAS ATIVAS:
{definicoes_ativas}
{secao_orientacao}
VERIFICAÇÃO FINAL SILENCIOSA:
Antes de responder, confirme internamente que preservou objetivo, dados e resposta correta; cumpriu TODOS os requisitos;
aplicou cada preferência dentro de sua própria função; obedeceu à instrução personalizada sem anular outra instrução;
não removeu algo necessário; não revelou a resposta; e não acrescentou adaptações não solicitadas. Não mostre essa
verificação, justificativas ou raciocínio ao usuário.

SAÍDA:
Retorne somente o exercício adaptado em Markdown. Não explique o processo, não inclua comentários e não use prefácios."""


def adaptar_exercicio_com_ia(
    texto_original: str,
    preferencias: list[str],
    instrucao_livre: str = "",
    nome_exercicio: str = "",
    materia: str = "",
    turma_ano: str = "",
) -> str:
    """Gera a versão adaptada usando somente a Responses API da OpenAI."""
    prompt = construir_prompt_adaptacao(
        texto_original=texto_original,
        preferencias=preferencias,
        instrucao_livre=instrucao_livre,
        nome_exercicio=nome_exercicio,
        materia=materia,
        turma_ano=turma_ano,
    )

    cliente = obter_cliente()
    try:
        resposta = cliente.responses.create(model=MODELO_PADRAO, input=prompt)
    except (AuthenticationError, PermissionDeniedError, RateLimitError, NotFoundError, BadRequestError, APIConnectionError, APITimeoutError, APIError) as erro:
        raise _traduzir_erro(erro) from erro

    texto_adaptado = (resposta.output_text or "").strip()
    if not texto_adaptado:
        raise ErroIA("A OpenAI respondeu sem conteúdo para a adaptação.")
    return texto_adaptado


if __name__ == "__main__":
    try:
        print(testar_conexao())
    except ErroIA as erro:
        print(f"Não foi possível testar a conexão com a OpenAI: {erro}")
