"""Tela Streamlit de adaptação, paralela à interface Tkinter da V3."""

from hashlib import sha256
from html import escape
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile

import streamlit as st
from PIL import Image, ImageOps

from adaptador import adaptar_exercicio
from biblioteca_web import botao_copiar, salvar_exercicio_local
from estado import Atividade
from formatacao_exercicio import markdown_com_numeros_destacados
from ia import ErroIA, adaptar_exercicio_com_ia
from ocr import ErroOCR, ler_texto_imagem


PREFERENCIAS = {
    "linguagem_direta": "Linguagem mais direta", "linguagem_simples": "Linguagem mais simples",
    "instrucoes_curtas": "Frases mais curtas", "dividir_etapas": "Dividir em etapas",
    "organizar": "Organizar informações", "reduzir": "Reduzir informações desnecessárias",
    "numeros": "Destacar números importantes", "palavras": "Destacar palavras-chave",
    "destacar_informacoes": "Destacar informações importantes", "pergunta": "Destacar a pergunta principal",
    "apresentar_exemplo": "Adicionar exemplo", "dica": "Adicionar dica", "visual": "Criar apoio visual",
}
GRUPOS = {
    "Linguagem": ["linguagem_direta", "linguagem_simples", "instrucoes_curtas"],
    "Estrutura": ["dividir_etapas", "organizar", "reduzir"],
    "Destaques": ["numeros", "palavras", "destacar_informacoes", "pergunta"],
    "Apoio pedagógico": ["apresentar_exemplo", "dica", "visual"],
}
PREFERENCIAS_SUPORTADAS = {
    "instrucoes_curtas", "dividir_etapas", "destacar_informacoes", "linguagem_direta", "apresentar_exemplo",
}
TAMANHO_MAXIMO_PREVIA = (420, 300)


def extrair_texto_imagem(dados: bytes, nome: str) -> str:
    """Entrega o arquivo recebido ao OCR local existente, sem duplicar sua lógica."""
    sufixo = Path(nome).suffix or ".png"
    with NamedTemporaryFile(suffix=sufixo, delete=False) as arquivo:
        arquivo.write(dados)
        caminho = Path(arquivo.name)
    try:
        return ler_texto_imagem(caminho)
    finally:
        caminho.unlink(missing_ok=True)


def criar_imagem_previa(dados: bytes) -> Image.Image:
    """Cria uma cópia orientada e reduzida exclusivamente para visualização."""
    with Image.open(BytesIO(dados)) as imagem_original:
        imagem_preview = ImageOps.exif_transpose(imagem_original).copy()
    imagem_preview.thumbnail(TAMANHO_MAXIMO_PREVIA, Image.Resampling.LANCZOS)
    return imagem_preview


def nome_arquivo_resumido(nome: str, limite: int = 42) -> str:
    """Mantém o nome do arquivo legível sem aumentar a altura da prévia."""
    arquivo = Path(nome).name
    if len(arquivo) <= limite:
        return arquivo
    extensao = Path(arquivo).suffix
    inicio = max(1, limite - len(extensao) - 1)
    return f"{arquivo[:inicio]}…{extensao}"


def mostrar_previa_imagem(dados: bytes, *, chave: str, legenda: str | None = None) -> None:
    """Exibe uma cópia compacta; os bytes originais continuam destinados ao OCR."""
    imagem_preview = criar_imagem_previa(dados)
    with st.container(key=f"adaptacao_preview_{chave}"):
        st.image(imagem_preview, width=imagem_preview.width)
        if legenda:
            nome_original = Path(legenda).name
            st.markdown(
                f'<div class="adaptacao-preview-caption" title="{escape(nome_original)}">'
                f'{escape(nome_arquivo_resumido(nome_original))}</div>',
                unsafe_allow_html=True,
            )


def inicializar_estado() -> None:
    valores = {
        "adaptacao_etapa": "entrada",
        "adaptacao_modo": "imagem",
        "adaptacao_modo_selecionado": "imagem",
        "adaptacao_texto_manual": "",
        "adaptacao_texto_revisado": "",
        "adaptacao_imagem_bytes": None,
        "adaptacao_imagem_nome": "",
        "adaptacao_upload_token": "",
        "adaptacao_upload_versao": 0,
        "adaptacao_resultado": "",
        "adaptacao_realizadas": [],
        "adaptacao_origem_resultado": "",
        "adaptacao_salvo": False,
        "adaptacao_ultimo_salvo_id": "",
        "adaptacao_instrucao": "",
        "adaptacao_instrucao_texto": "",
        "adaptacao_ocr_erro": "",
    }
    for chave, valor in valores.items():
        st.session_state.setdefault(chave, valor)
    if "adaptacao_atividade" not in st.session_state:
        st.session_state.adaptacao_atividade = Atividade()
    atividade = st.session_state.adaptacao_atividade
    st.session_state.setdefault("adaptacao_nome", atividade.nome)
    st.session_state.setdefault("adaptacao_classe", atividade.classe)
    st.session_state.setdefault("adaptacao_materia", atividade.materia)
    st.session_state.setdefault("adaptacao_preferencias", {chave: False for chave in PREFERENCIAS})
    for chave in PREFERENCIAS:
        st.session_state.setdefault(f"adaptacao_pref_{chave}", False)


def atividade_atual() -> Atividade:
    return st.session_state.adaptacao_atividade


def sincronizar_informacoes() -> None:
    atividade = atividade_atual()
    atividade.nome = st.session_state.adaptacao_nome.strip()
    atividade.classe = st.session_state.adaptacao_classe.strip()
    atividade.materia = st.session_state.adaptacao_materia.strip()


def salvar_texto_manual() -> None:
    """Mantém os valores dos widgets de entrada entre etapas e reruns."""
    if "adaptacao_modo" in st.session_state:
        st.session_state.adaptacao_modo_selecionado = st.session_state.adaptacao_modo
    if "adaptacao_texto_manual_widget" in st.session_state:
        st.session_state.adaptacao_texto_manual = st.session_state.adaptacao_texto_manual_widget


def modo_entrada() -> str:
    """Retorna a escolha persistente, sem depender da chave temporária do radio."""
    return st.session_state.adaptacao_modo_selecionado


def salvar_personalizacao() -> None:
    """Copia widgets efêmeros para o estado que atravessa as etapas."""
    preferencias = st.session_state.adaptacao_preferencias
    for chave in PREFERENCIAS:
        chave_widget = f"adaptacao_pref_{chave}"
        if chave_widget in st.session_state:
            preferencias[chave] = st.session_state[chave_widget]
    if "adaptacao_instrucao" in st.session_state:
        st.session_state.adaptacao_instrucao_texto = st.session_state.adaptacao_instrucao


def salvar_texto_revisado() -> None:
    if "adaptacao_revisao_texto" in st.session_state:
        texto = st.session_state.adaptacao_revisao_texto
        st.session_state.adaptacao_texto_revisado = texto
        atividade_atual().texto = texto


def preparar_revisao() -> None:
    st.session_state.adaptacao_revisao_texto = st.session_state.adaptacao_texto_revisado


def preparar_personalizacao() -> None:
    """Restaura os widgets com os valores que o professor já havia escolhido."""
    preferencias = st.session_state.adaptacao_preferencias
    for chave in PREFERENCIAS:
        st.session_state[f"adaptacao_pref_{chave}"] = preferencias[chave]
    st.session_state.adaptacao_instrucao = st.session_state.adaptacao_instrucao_texto


def mudar_etapa(etapa: str) -> None:
    st.session_state.adaptacao_etapa = etapa


def voltar_para_entrada() -> None:
    """Retorna à entrada mantendo inclusive uma revisão ainda não confirmada."""
    salvar_texto_revisado()
    texto_revisado = st.session_state.adaptacao_texto_revisado.strip()
    if texto_revisado:
        atividade = atividade_atual()
        atividade.texto = texto_revisado
        if modo_entrada() == "texto":
            st.session_state.adaptacao_texto_manual = texto_revisado
            st.session_state.adaptacao_texto_manual_widget = texto_revisado
        else:
            atividade.texto_ocr = texto_revisado
    mudar_etapa("entrada")


def voltar_para_revisao() -> None:
    salvar_personalizacao()
    mudar_etapa("revisao")


def processar_upload(upload) -> None:
    dados = upload.getvalue()
    token = sha256(dados).hexdigest()
    if token == st.session_state.adaptacao_upload_token:
        return
    st.session_state.adaptacao_upload_token = token
    st.session_state.adaptacao_imagem_bytes = dados
    st.session_state.adaptacao_imagem_nome = upload.name
    st.session_state.adaptacao_ocr_erro = ""
    try:
        with st.spinner("Lendo texto da imagem..."):
            texto = extrair_texto_imagem(dados, upload.name)
    except ErroOCR as erro:
        atividade_atual().texto_ocr = ""
        atividade_atual().texto = ""
        st.session_state.adaptacao_ocr_erro = str(erro)
    else:
        atividade_atual().texto_ocr = texto
        atividade_atual().texto = texto


def avancar_para_revisao() -> None:
    sincronizar_informacoes()
    salvar_texto_manual()
    atividade = atividade_atual()
    if modo_entrada() == "imagem":
        if not st.session_state.adaptacao_imagem_bytes:
            st.warning("Selecione uma imagem para continuar.")
            return
        if not atividade.texto_ocr:
            st.warning("Não foi possível identificar texto na imagem. Selecione outra imagem ou digite o exercício.")
            return
        atividade.texto = atividade.texto_ocr
    else:
        texto = st.session_state.adaptacao_texto_manual.strip()
        if not texto:
            st.warning("Digite ou cole um exercício para continuar.")
            return
        atividade.imagem = None
        atividade.texto_ocr = ""
        atividade.texto = texto
    st.session_state.adaptacao_texto_revisado = atividade.texto
    mudar_etapa("revisao")


def salvar_revisao() -> None:
    salvar_texto_revisado()
    texto = st.session_state.adaptacao_texto_revisado.strip()
    if not texto:
        st.warning("Digite ou corrija o texto antes de continuar.")
        return
    atividade_atual().texto = texto
    mudar_etapa("personalizacao")


def preferencias_selecionadas() -> list[str]:
    return [chave for chave in PREFERENCIAS if st.session_state.adaptacao_preferencias[chave]]


def gerar_adaptacao() -> None:
    salvar_personalizacao()
    atividade = atividade_atual()
    atividade.instrucao = st.session_state.adaptacao_instrucao_texto.strip()
    selecionadas = preferencias_selecionadas()
    suportadas = [chave for chave in selecionadas if chave in PREFERENCIAS_SUPORTADAS]
    if not atividade.texto.strip():
        st.warning("Não há texto válido para adaptar.")
        return
    if not selecionadas:
        st.warning("Selecione ao menos uma opção para prosseguir.")
        return
    preferencias_ia = [PREFERENCIAS[chave] for chave in selecionadas]
    try:
        resultado = adaptar_exercicio_com_ia(
            texto_original=atividade.texto,
            preferencias=preferencias_ia,
            instrucao_livre=atividade.instrucao,
            nome_exercicio=atividade.nome,
            materia=atividade.materia,
            turma_ano=atividade.classe,
        )
        realizadas = preferencias_ia
        st.session_state.adaptacao_origem_resultado = "ia"
    except ErroIA:
        resultado, realizadas = adaptar_exercicio(atividade.texto, suportadas)
        st.session_state.adaptacao_origem_resultado = "local"
    st.session_state.adaptacao_resultado = resultado
    st.session_state.adaptacao_realizadas = realizadas
    st.session_state.adaptacao_salvo = False
    st.session_state.adaptacao_ultimo_salvo_id = ""
    mudar_etapa("resultado")


def salvar_exercicio() -> None:
    if st.session_state.adaptacao_ultimo_salvo_id:
        return
    atividade = atividade_atual()
    item = salvar_exercicio_local(
        atividade,
        st.session_state.adaptacao_resultado,
        [PREFERENCIAS[chave] for chave in preferencias_selecionadas()],
        "adaptado",
    )
    st.session_state.adaptacao_ultimo_salvo_id = item.identificador
    st.session_state.adaptacao_salvo = True


def nova_adaptacao() -> None:
    st.session_state.adaptacao_atividade = Atividade()
    st.session_state.adaptacao_etapa = "entrada"
    st.session_state.adaptacao_modo = "imagem"
    st.session_state.adaptacao_modo_selecionado = "imagem"
    st.session_state.adaptacao_texto_manual = ""
    st.session_state.adaptacao_texto_revisado = ""
    st.session_state.adaptacao_imagem_bytes = None
    st.session_state.adaptacao_imagem_nome = ""
    st.session_state.adaptacao_upload_token = ""
    st.session_state.adaptacao_upload_versao += 1
    st.session_state.adaptacao_resultado = ""
    st.session_state.adaptacao_realizadas = []
    st.session_state.adaptacao_origem_resultado = ""
    st.session_state.adaptacao_salvo = False
    st.session_state.adaptacao_ultimo_salvo_id = ""
    st.session_state.adaptacao_instrucao = ""
    st.session_state.adaptacao_instrucao_texto = ""
    st.session_state.adaptacao_ocr_erro = ""
    st.session_state.adaptacao_nome = ""
    st.session_state.adaptacao_classe = ""
    st.session_state.adaptacao_materia = ""
    st.session_state.pop("adaptacao_texto_manual_widget", None)
    st.session_state.pop("adaptacao_revisao_texto", None)
    for chave in PREFERENCIAS:
        st.session_state[f"adaptacao_pref_{chave}"] = False
    st.session_state.adaptacao_preferencias = {chave: False for chave in PREFERENCIAS}


def campos_informacoes() -> None:
    st.markdown('<div class="web-section-title">Informações do exercício</div>', unsafe_allow_html=True)
    nome, classe, materia = st.columns(3)
    with nome:
        st.text_input("Nome do exercício", key="adaptacao_nome")
    with classe:
        st.text_input("Classe/Ano", key="adaptacao_classe")
    with materia:
        st.text_input("Matéria", key="adaptacao_materia")


def tela_entrada() -> None:
    st.title("Adaptar exercício")
    st.markdown('<div class="subtitle">1. Envie a atividade · 2. Revise o texto · 3. Personalize · 4. Revise o resultado</div>', unsafe_allow_html=True)
    campos_informacoes()
    st.markdown('<div class="web-section-title">Enviar atividade</div>', unsafe_allow_html=True)
    # A chave do radio pode sobreviver a um rerun com o valor anterior. Antes
    # de desenhá-lo, ela é sempre sincronizada com a escolha persistente.
    st.session_state.adaptacao_modo = modo_entrada()
    st.radio("Forma de entrada", ("imagem", "texto"), format_func=lambda valor: "Selecionar imagem" if valor == "imagem" else "Digitar exercício", horizontal=True, key="adaptacao_modo", label_visibility="collapsed", on_change=salvar_texto_manual)
    esquerda, direita = st.columns(2, gap="large")
    with esquerda:
        if modo_entrada() == "imagem":
            upload = st.file_uploader("Selecionar imagem", type=["png", "jpg", "jpeg", "gif", "bmp"], key=f"adaptacao_upload_{st.session_state.adaptacao_upload_versao}")
            if upload:
                processar_upload(upload)
                st.caption(upload.name)
                if st.session_state.adaptacao_ocr_erro:
                    st.error(st.session_state.adaptacao_ocr_erro)
                elif atividade_atual().texto_ocr:
                    st.success("Texto reconhecido. Revise-o antes de continuar.")
            else:
                st.caption("O OCR usa Tesseract localmente.")
        else:
            if "adaptacao_texto_manual_widget" not in st.session_state:
                st.session_state.adaptacao_texto_manual_widget = st.session_state.adaptacao_texto_manual
            st.text_area("Digite ou cole aqui o exercício que deseja adaptar.", key="adaptacao_texto_manual_widget", height=260, on_change=salvar_texto_manual)
    with direita:
        st.markdown('<div class="web-section-title">Pré-visualização</div>', unsafe_allow_html=True)
        if modo_entrada() == "imagem" and st.session_state.adaptacao_imagem_bytes:
            mostrar_previa_imagem(
                st.session_state.adaptacao_imagem_bytes,
                chave="upload",
                legenda=st.session_state.adaptacao_imagem_nome,
            )
        elif modo_entrada() == "texto":
            st.info("O conteúdo será aberto para revisão antes da personalização.")
        else:
            st.info("A imagem aparecerá aqui.")
    st.button("Próximo: revisar texto →", key="adaptacao_avancar", on_click=avancar_para_revisao, type="primary")


def tela_revisao() -> None:
    manual = modo_entrada() == "texto"
    st.button("← Voltar", key="adaptacao_voltar_revisao", on_click=voltar_para_entrada)
    st.title("Revisar exercício" if manual else "Texto reconhecido")
    st.markdown('<div class="subtitle">Revise o texto antes de continuar. A sua edição será usada na adaptação.</div>', unsafe_allow_html=True)
    preparar_revisao()
    esquerda, direita = st.columns([1, 3], gap="large")
    with esquerda:
        st.markdown(f'<div class="web-section-title">{"Entrada manual" if manual else "Imagem original"}</div>', unsafe_allow_html=True)
        if manual:
            st.info("O exercício foi inserido diretamente.")
        elif st.session_state.adaptacao_imagem_bytes:
            mostrar_previa_imagem(st.session_state.adaptacao_imagem_bytes, chave="revisao")
        else:
            st.info("Sem imagem disponível.")
    with direita:
        st.markdown(f'<div class="web-section-title">{"Texto do exercício" if manual else "Texto reconhecido"}</div>', unsafe_allow_html=True)
        st.text_area("Texto revisado", key="adaptacao_revisao_texto", height=360, label_visibility="collapsed", on_change=salvar_texto_revisado)
    st.button("Próximo: personalizar →", key="adaptacao_salvar_revisao", on_click=salvar_revisao, type="primary")


def tela_personalizacao() -> None:
    st.button("← Voltar", key="adaptacao_voltar_personalizacao", on_click=voltar_para_revisao)
    st.title("Personalização pedagógica")
    st.markdown('<div class="subtitle">Selecione estratégias e registre a sua orientação para a atividade.</div>', unsafe_allow_html=True)
    preparar_personalizacao()
    primeira_linha = st.columns(2, gap="large")
    segunda_linha = st.columns(2, gap="large")
    for coluna, (grupo, chaves) in zip((*primeira_linha, *segunda_linha), GRUPOS.items()):
        with coluna:
            with st.container(key=f"grupo_{grupo.lower().replace(' ', '_')}"):
                st.markdown(f'<div class="web-section-title">{grupo}</div>', unsafe_allow_html=True)
                for chave in chaves:
                    st.checkbox(PREFERENCIAS[chave], key=f"adaptacao_pref_{chave}", on_change=salvar_personalizacao)
    st.markdown('<div class="instrucao-livre"><div class="web-section-title">✦ Instrução personalizada</div><div class="muted">Como você gostaria que o exercício fosse adaptado?</div></div>', unsafe_allow_html=True)
    st.text_area("Instrução personalizada", key="adaptacao_instrucao", height=130, label_visibility="collapsed", placeholder="Ex.: destaque os números importantes em azul.", on_change=salvar_personalizacao)
    st.button("Gerar exercício adaptado →", key="adaptacao_gerar", on_click=gerar_adaptacao, type="primary")


def tela_resultado() -> None:
    atividade = atividade_atual()
    st.button("← Voltar", key="adaptacao_voltar_resultado", on_click=mudar_etapa, args=("personalizacao",))
    st.title("Exercício adaptado")
    st.markdown('<div class="subtitle">Revise o resultado antes de iniciar uma nova atividade.</div>', unsafe_allow_html=True)
    original, adaptado = st.columns([1, 2], gap="large")
    with original:
        st.markdown('<div class="web-section-title">VERSÃO ORIGINAL</div>', unsafe_allow_html=True)
        st.text_area("Versão original", value=atividade.texto, height=250, disabled=True, label_visibility="collapsed")
    with adaptado:
        titulo_adaptado, copiar = st.columns([4, 1], vertical_alignment="center")
        with titulo_adaptado:
            st.markdown('<div class="web-section-title destaque-resultado">EXERCÍCIO ADAPTADO</div>', unsafe_allow_html=True)
        with copiar:
            botao_copiar(st.session_state.adaptacao_resultado)
        with st.container(border=True):
            st.markdown(markdown_com_numeros_destacados(st.session_state.adaptacao_resultado))
        st.markdown('<div class="web-section-title">Recursos utilizados na adaptação</div>', unsafe_allow_html=True)
        realizadas = st.session_state.adaptacao_realizadas
        st.markdown("\n".join(f"✓ {item}" for item in realizadas) if realizadas else "Nenhuma adaptação registrada.")
        if atividade.instrucao:
            st.caption(f"Orientação registrada pelo professor: {atividade.instrucao}")
        if st.session_state.adaptacao_origem_resultado == "local":
            st.caption("A IA não esteve disponível; o resultado foi gerado no modo local.")
    editar, adaptar_novamente, nova, salvar = st.columns(4)
    with editar:
        st.button("Editar texto", key="adaptacao_editar", on_click=mudar_etapa, args=("revisao",))
    with adaptar_novamente:
        st.button("Adaptar novamente", key="adaptacao_novamente", on_click=mudar_etapa, args=("personalizacao",))
    with nova:
        st.button("← Nova atividade", key="adaptacao_nova", on_click=nova_adaptacao)
    with salvar:
        st.button("Salvar exercício", key="adaptacao_salvar", on_click=salvar_exercicio, type="primary")
    if st.session_state.adaptacao_salvo:
        st.success("O exercício foi salvo no histórico local.")


def renderizar_adaptacao() -> None:
    """Renderiza uma etapa e mantém os dados em sessão entre todos os reruns."""
    inicializar_estado()
    etapa = st.session_state.adaptacao_etapa
    if etapa == "entrada":
        tela_entrada()
    elif etapa == "revisao":
        tela_revisao()
    elif etapa == "personalizacao":
        tela_personalizacao()
    else:
        tela_resultado()
