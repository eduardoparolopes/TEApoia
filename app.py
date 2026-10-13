"""Ponto de entrada da V4.1 web do TEApoia.

Dashboard, criação manual e adaptação convivem com a V3 em Tkinter, mantida em main.py.
"""

from base64 import b64encode
from io import BytesIO
from pathlib import Path

import streamlit as st
from PIL import Image, ImageChops

from adaptacao_web import renderizar_adaptacao
from biblioteca_web import renderizar_biblioteca
from criacao_web import renderizar_criacao


PASTA_PROJETO = Path(__file__).resolve().parent
PASTA_ASSETS = PASTA_PROJETO / "assets"
IDS_PAGINAS = {
    "Início": "inicio", "Criar exercício": "criar", "Adaptar exercício": "adaptar",
    "Meus exercícios": "exercicios", "Modelos": "modelos", "Configurações": "configuracoes",
}


@st.cache_data
def marca_png(arquivo: str, tamanho: tuple[int, int]) -> bytes:
    """Recorta a margem clara das imagens de marca e preserva sua proporção."""
    with Image.open(PASTA_ASSETS / arquivo) as origem:
        imagem = origem.convert("RGBA")
    conteudo = imagem.getchannel("R").point(lambda valor: 255 if valor < 245 else 0)
    area = conteudo.getbbox()
    if area:
        imagem = imagem.crop(area)
    canais = imagem.split()
    branco = ImageChops.darker(ImageChops.darker(canais[0], canais[1]), canais[2])
    imagem.putalpha(branco.point(lambda valor: 0 if valor > 245 else 255))
    imagem.thumbnail(tamanho, Image.Resampling.LANCZOS)
    saida = BytesIO()
    imagem.save(saida, format="PNG")
    return saida.getvalue()


def marca_data_url(arquivo: str, tamanho: tuple[int, int]) -> str:
    """Disponibiliza a marca em um único container HTML flexível na sidebar."""
    conteudo = b64encode(marca_png(arquivo, tamanho)).decode("ascii")
    return f"data:image/png;base64,{conteudo}"


def navegar(pagina: str) -> None:
    """Atualiza somente o conteúdo da aplicação Streamlit na aba atual."""
    st.session_state.pagina = pagina
    if pagina == "Meus exercícios":
        st.session_state.biblioteca_exercicio_id = ""


def botao_pagina(rotulo: str, pagina: str, chave: str) -> None:
    """Controle de navegação interno, sem hyperlinks ou abertura de abas."""
    st.button(rotulo, key=chave, on_click=navegar, args=(pagina,), use_container_width=True)


def aplicar_estilos(pagina_atual: str) -> None:
    estilos_navegacao = "\n".join(
        f'.st-key-nav_{identificador} button {{ background: {"#EAF2FF" if pagina == pagina_atual else "#F8FAFC"} !important; '
        f'color: {"#1D4ED8" if pagina == pagina_atual else "#111827"} !important; }}'
        for pagina, identificador in IDS_PAGINAS.items()
    )
    st.markdown(
        """
        <style>
            :root {
                --azul: #2563EB; --verde: #14B8A6; --lilas: #7C3AED;
                --superficie: #FFFFFF; --superficie-suave: #F7F9FC;
                --campo-fundo: #FFFFFF; --campo-texto: #16213A; --campo-label: #344054;
                --campo-placeholder: #667085; --campo-borda: #D0D9E8; --campo-foco: #2563EB;
                color-scheme: light;
            }
            #MainMenu, footer { visibility: hidden; }
            header { background: transparent !important; }
            [data-testid="stSidebarCollapsedControl"] {
                display: flex !important; visibility: visible !important;
            }
            [data-testid="stSidebarCollapsedControl"] button {
                background: #FFFFFF !important; color: #344054 !important;
                border: 1px solid #D0D9E8 !important; border-radius: .6rem !important;
            }
            /* A versão web permanece exclusivamente no modo claro nesta etapa. */
            html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
                background: #F7F9FC !important; color: #16213A !important; color-scheme: light !important;
            }
            [data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid #E3E8F0; }
            [data-testid="stSidebar"] > div:first-child { padding: 1.25rem .75rem; overflow-x: hidden; }
            .brand-row {
                display: flex; align-items: center; gap: .55rem; width: 100%; min-width: 0;
                padding: .1rem .2rem .45rem; box-sizing: border-box; overflow: visible;
            }
            .brand-logo { width: 38px; height: auto; flex: 0 0 38px; display: block; }
            .brand-wordmark { width: 102px; max-width: calc(100% - 47px); height: auto; object-fit: contain;
                              object-position: left center; flex: 0 1 auto; display: block; }
            .brand-space { height: .35rem; }
            [data-testid="stSidebar"] .stButton { margin: .22rem 0; }
            [data-testid="stSidebar"] .stButton button {
                display: flex; align-items: center; justify-content: flex-start; width: 100%; min-height: 44px;
                box-sizing: border-box; padding: .7rem .85rem; border: 0; border-radius: .75rem;
                color: #111827 !important; background: #F8FAFC; font-weight: 600; cursor: pointer;
                transition: background-color .16s ease, color .16s ease, transform .16s ease;
            }
            [data-testid="stSidebar"] .stButton button:hover { background: #EAF2FF !important; color: #1D4ED8 !important; transform: translateX(2px); }
            [data-testid="stSidebar"] .stButton button:focus-visible { outline: 3px solid #BFDBFE; outline-offset: 2px; }
            {estilos_navegacao}
            .sidebar-bottom { margin-top: 2.25rem; }
            [data-testid="stMainBlockContainer"] { max-width: 1200px; padding: 2rem 2.35rem 3rem; }
            .subtitle { color: #667085; font-size: 1rem; margin: -.2rem 0 1.65rem; }
            .greeting { font-size: 1.45rem; font-weight: 700; margin: 0; color: #16213A; }
            .greeting-support { color: #667085; margin: .2rem 0 1.25rem; }
            .home-card, .info-card, .temporary-card {
                background: #FFFFFF; border: 1px solid #DDE4EF; border-radius: 1rem; padding: 1.15rem;
                min-height: 210px; box-sizing: border-box;
            }
            .st-key-card_blue, .st-key-card_green, .st-key-card_lilac {
                background: #FFFFFF; border: 1px solid #DDE4EF; border-radius: 1rem; padding: 1.15rem;
                min-height: 210px; box-sizing: border-box;
            }
            .accent-icon {
                width: 2.55rem; height: 2.55rem; border-radius: .72rem; display: flex;
                align-items: center; justify-content: center; color: white; font-size: 1.35rem; font-weight: 700;
                margin-bottom: .9rem;
            }
            .accent-blue { background: var(--azul); }
            .accent-green { background: var(--verde); color: #FFFFFF; }
            .accent-lilac { background: var(--lilas); }
            .card-title { font-size: 1.05rem; font-weight: 700; color: #16213A; margin-bottom: .4rem; }
            .card-description { color: #667085; min-height: 2.7rem; margin-bottom: 1.1rem; }
            .action-button {
                display: inline-block; border-radius: .7rem; padding: .62rem 1rem; font-weight: 700;
                text-decoration: none; margin-top: .15rem;
            }
            .button-blue, .button-blue:visited { background: var(--azul); color: white !important; }
            .button-green, .button-green:visited { background: var(--verde); color: white !important; }
            .button-lilac, .button-lilac:visited { background: var(--lilas); color: white !important; }
            .button-blue:hover, .button-blue:active, .button-blue:focus { background: #1D4ED8; color: white !important; }
            .button-green:hover, .button-green:active, .button-green:focus { background: #10A99E; color: white !important; }
            .button-lilac:hover, .button-lilac:active, .button-lilac:focus { background: #6D28D9; color: white !important; }
            .action-button:focus-visible { outline: 3px solid #BFDBFE; outline-offset: 2px; }
            .st-key-acao_blue button, .st-key-acao_blue button:hover, .st-key-acao_blue button:active { background: var(--azul) !important; color: white !important; border: 0; }
            .st-key-acao_green button, .st-key-acao_green button:hover, .st-key-acao_green button:active { background: var(--verde) !important; color: white !important; border: 0; }
            .st-key-acao_lilac button, .st-key-acao_lilac button:hover, .st-key-acao_lilac button:active { background: var(--lilas) !important; color: white !important; border: 0; }
            .st-key-acao_blue button, .st-key-acao_green button, .st-key-acao_lilac button { border-radius: .7rem; font-weight: 700; }
            .section-title { font-size: 1rem; font-weight: 700; color: #16213A; margin: 1.5rem 0 .15rem; }
            .web-section-title { font-size: 1rem; font-weight: 700; color: #16213A; margin: 1rem 0 .6rem; }
            .destaque-resultado { color: #0F766E; font-size: 1.1rem; }
            .instrucao-livre { background: #EAF2FF; border-radius: 1rem; padding: 1rem 1.1rem; margin-top: 1.4rem; }
            /* Base visual reutilizável para widgets nativos do Streamlit/BaseWeb. */
            [data-testid="stMain"] label, [data-testid="stMain"] label p,
            [data-testid="stMain"] [data-testid="stWidgetLabel"] p {
                color: var(--campo-label) !important; opacity: 1 !important;
            }
            [data-testid="stTextInput"] [data-baseweb="input"] > div,
            [data-testid="stNumberInput"] [data-baseweb="input"] > div,
            [data-testid="stDateInput"] [data-baseweb="input"] > div,
            [data-testid="stTimeInput"] [data-baseweb="input"] > div,
            [data-testid="stTextArea"] textarea,
            [data-testid="stSelectbox"] [data-baseweb="select"] > div,
            [data-testid="stMultiSelect"] [data-baseweb="select"] > div {
                background: var(--campo-fundo) !important; border: 1px solid var(--campo-borda) !important;
                border-radius: .75rem !important; box-shadow: none !important;
            }
            [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,
            [data-testid="stDateInput"] input, [data-testid="stTimeInput"] input,
            [data-testid="stTextArea"] textarea,
            [data-testid="stSelectbox"] [data-baseweb="select"],
            [data-testid="stMultiSelect"] [data-baseweb="select"] {
                color: var(--campo-texto) !important; caret-color: var(--campo-texto) !important;
                -webkit-text-fill-color: var(--campo-texto) !important;
            }
            [data-testid="stTextInput"] input::placeholder,
            [data-testid="stNumberInput"] input::placeholder,
            [data-testid="stTextArea"] textarea::placeholder {
                color: var(--campo-placeholder) !important; opacity: 1 !important;
                -webkit-text-fill-color: var(--campo-placeholder) !important;
            }
            [data-testid="stTextInput"] [data-baseweb="input"] > div:focus-within,
            [data-testid="stNumberInput"] [data-baseweb="input"] > div:focus-within,
            [data-testid="stTextArea"] textarea:focus,
            [data-testid="stSelectbox"] [data-baseweb="select"] > div:focus-within,
            [data-testid="stMultiSelect"] [data-baseweb="select"] > div:focus-within {
                border-color: var(--campo-foco) !important; box-shadow: 0 0 0 2px #BFDBFE !important;
            }
            [data-testid="stFileUploaderDropzone"] {
                background: var(--campo-fundo) !important; border-color: var(--campo-borda) !important;
                color: var(--campo-texto) !important; border-radius: .75rem !important;
            }
            [data-testid="stCheckbox"] label, [data-testid="stCheckbox"] p,
            [data-testid="stRadio"] label, [data-testid="stRadio"] p {
                color: var(--campo-label) !important;
            }
            [data-testid="stCheckbox"] input, [data-testid="stRadio"] input { accent-color: var(--azul); }
            [data-baseweb="menu"], [role="listbox"], [role="option"] {
                background: var(--superficie) !important; color: var(--campo-texto) !important;
            }
            [data-testid="stExpander"], [data-testid="stExpander"] details,
            [data-testid="stVerticalBlockBorderWrapper"], [data-testid="stAlert"] {
                background: var(--superficie) !important; color: var(--campo-texto) !important;
                border-color: var(--campo-borda) !important;
            }
            [data-testid="stAlert"] p, [data-testid="stAlert"] div { color: var(--campo-texto) !important; }
            [data-testid="stPopoverBody"], [data-testid="stTooltipHoverTarget"] {
                background: var(--superficie) !important; color: var(--campo-texto) !important;
            }
            .adaptacao-preview-caption {
                width: min(100%, 420px); margin: .3rem auto 0; overflow: hidden;
                color: #667085; font-size: .8rem; text-align: center;
                text-overflow: ellipsis; white-space: nowrap;
            }
            .st-key-adaptacao_avancar button, .st-key-adaptacao_salvar_revisao button { background: var(--azul) !important; color: white !important; border: 0; border-radius: .7rem; font-weight: 700; }
            .st-key-adaptacao_gerar button { background: var(--lilas) !important; color: white !important; border: 0; border-radius: .7rem; font-weight: 700; }
            .st-key-criacao_continuar button, .st-key-criacao_salvar button { background: var(--azul) !important; color: white !important; border: 0; border-radius: .7rem; font-weight: 700; }
            .st-key-criacao_gerar button { background: var(--lilas) !important; color: white !important; border: 0; border-radius: .7rem; font-weight: 700; }
            [class*="st-key-adaptacao_voltar_"] button, [class*="st-key-criacao_voltar_"] button, .st-key-biblioteca_voltar button {
                min-height: 34px; padding: .32rem .72rem; background: #FFFFFF !important;
                color: #344054 !important; border: 1px solid #D0D9E8 !important;
                border-radius: .65rem !important; font-weight: 600;
            }
            [class*="st-key-adaptacao_voltar_"] button:hover, [class*="st-key-criacao_voltar_"] button:hover, .st-key-biblioteca_voltar button:hover {
                background: #EAF2FF !important; color: #1D4ED8 !important; border-color: #BFDBFE !important;
            }
            [class*="st-key-biblioteca_abrir_"] button {
                min-height: 36px; height: 36px; box-sizing: border-box; padding: .35rem .6rem;
                border: 1px solid #D0D9E8; border-radius: .65rem; color: #344054;
                background: #FFFFFF; font-size: 14px; font-weight: 600; line-height: 1.25;
            }
            [class*="st-key-biblioteca_abrir_"] button:hover {
                background: #EAF2FF; border-color: #BFDBFE; color: #1D4ED8;
            }
            [class*="st-key-biblioteca_excluir_"] button {
                min-height: 36px; height: 36px; padding: 0; border: 1px solid transparent !important;
                border-radius: .65rem !important; background: #F8FAFC !important; color: #667085 !important;
                font-size: 1rem; font-weight: 600; overflow: hidden;
            }
            [class*="st-key-biblioteca_excluir_"] button:hover {
                background: #FEF2F2 !important; border-color: #FEE4E2 !important; color: #B42318 !important;
            }
            .info-card { min-height: auto; margin-top: .8rem; }
            .muted { color: #667085; white-space: pre-line; line-height: 1.55; }
            .temporary-card { max-width: 650px; margin-top: 1.5rem; min-height: auto; }
            @media (max-width: 760px) {
                [data-testid="stMainBlockContainer"] { padding: 1.25rem 1rem 2rem; }
                .home-card { margin-bottom: .75rem; min-height: auto; }
            }
        </style>
        """.replace("{estilos_navegacao}", estilos_navegacao),
        unsafe_allow_html=True,
    )


def montar_barra_lateral() -> None:
    with st.sidebar:
        logo = marca_data_url("logo_teapoia.png", (42, 42))
        nome = marca_data_url("nome_teapoia.png", (112, 30))
        st.markdown(
            f'<div class="brand-row"><img class="brand-logo" src="{logo}" alt="Logo TEApoia">'
            f'<img class="brand-wordmark" src="{nome}" alt="TEApoia"></div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="brand-space"></div>', unsafe_allow_html=True)
        for icone, pagina in (("⌂", "Início"), ("＋", "Criar exercício"), ("↗", "Adaptar exercício"),
                              ("▣", "Meus exercícios"), ("▤", "Modelos")):
            botao_pagina(f"{icone}  {pagina}", pagina, f"nav_{IDS_PAGINAS[pagina]}")
        st.markdown('<div class="sidebar-bottom"></div>', unsafe_allow_html=True)
        botao_pagina("⚙  Configurações", "Configurações", "nav_configuracoes")


def card_principal(icone: str, titulo: str, descricao: str, pagina: str, classe: str) -> None:
    with st.container(key=f"card_{classe}"):
        st.markdown(
            f"""
            <div class="accent-icon accent-{classe}">{icone}</div>
            <div class="card-title">{titulo}</div>
            <div class="card-description">{descricao}</div>
            """,
            unsafe_allow_html=True,
        )
        botao_pagina("Começar →", pagina, f"acao_{classe}")


def dashboard() -> None:
    st.image(marca_png("nome_teapoia.png", (280, 70)), width=245)
    st.markdown('<div class="subtitle">Mais inclusão na prática pedagógica.</div>', unsafe_allow_html=True)
    st.markdown('<p class="greeting">Olá, professor!</p>', unsafe_allow_html=True)
    st.markdown('<p class="greeting-support">Como podemos ajudar você hoje?</p>', unsafe_allow_html=True)

    criar, adaptar, modelos = st.columns(3, gap="medium")
    with criar:
        card_principal("＋", "Criar novo exercício", "Defina o conteúdo da atividade.", "Criar exercício", "blue")
    with adaptar:
        card_principal("↗", "Adaptar exercício", "Envie uma atividade e torne-a mais acessível.", "Adaptar exercício", "green")
    with modelos:
        card_principal("◈", "Explorar modelos", "Use referências como ponto de partida.", "Modelos", "lilac")

    st.markdown('<div class="section-title">Exercícios recentes</div>', unsafe_allow_html=True)
    st.markdown('<div class="info-card"><div class="muted">Nenhum exercício salvo nesta sessão.</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Modelos utilizados recentemente</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="info-card"><div class="muted">Matemática · Problemas com quantidades\nPortuguês · Leitura e interpretação\nCiências · Observação e investigação</div></div>',
        unsafe_allow_html=True,
    )


def pagina_temporaria(pagina: str) -> None:
    st.title(pagina)
    st.markdown(
        '<div class="temporary-card"><div class="card-title">Migração em andamento</div>'
        '<div class="muted">Esta tela será migrada na próxima etapa.</div></div>',
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="TEApoia", page_icon="📘", layout="wide", initial_sidebar_state="expanded")
    if "pagina" not in st.session_state:
        st.session_state.pagina = "Início"

    aplicar_estilos(st.session_state.pagina)
    montar_barra_lateral()
    if st.session_state.pagina == "Início":
        dashboard()
    elif st.session_state.pagina == "Criar exercício":
        renderizar_criacao()
    elif st.session_state.pagina == "Adaptar exercício":
        renderizar_adaptacao()
    elif st.session_state.pagina == "Meus exercícios":
        renderizar_biblioteca()
    else:
        pagina_temporaria(st.session_state.pagina)


if __name__ == "__main__":
    main()
