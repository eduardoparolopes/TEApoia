"""Tela Streamlit de criação manual, paralela à interface Tkinter da V3."""

import streamlit as st

from adaptacao_web import GRUPOS, PREFERENCIAS, PREFERENCIAS_SUPORTADAS
from adaptador import adaptar_exercicio
from biblioteca_web import salvar_exercicio_local
from estado import Atividade


def inicializar_estado() -> None:
    valores = {
        "criacao_etapa": "entrada",
        "criacao_conteudo": "",
        "criacao_conteudo_widget": "",
        "criacao_instrucao": "",
        "criacao_instrucao_widget": "",
        "criacao_resultado": "",
        "criacao_realizadas": [],
        "criacao_preferencias": {chave: False for chave in PREFERENCIAS},
        "criacao_salvo": False,
        "criacao_ultimo_salvo_id": "",
    }
    for chave, valor in valores.items():
        st.session_state.setdefault(chave, valor)
    st.session_state.setdefault("criacao_atividade", Atividade())
    atividade = st.session_state.criacao_atividade
    st.session_state.setdefault("criacao_nome", atividade.nome)
    st.session_state.setdefault("criacao_classe", atividade.classe)
    st.session_state.setdefault("criacao_materia", atividade.materia)


def atividade_atual() -> Atividade:
    return st.session_state.criacao_atividade


def salvar_entrada() -> None:
    atividade = atividade_atual()
    for campo in ("nome", "classe", "materia"):
        chave_widget = f"criacao_{campo}_widget"
        if chave_widget in st.session_state:
            st.session_state[f"criacao_{campo}"] = st.session_state[chave_widget]
    atividade.nome = st.session_state.criacao_nome.strip()
    atividade.classe = st.session_state.criacao_classe.strip()
    atividade.materia = st.session_state.criacao_materia.strip()
    if "criacao_conteudo_widget" in st.session_state:
        st.session_state.criacao_conteudo = st.session_state.criacao_conteudo_widget


def preparar_entrada() -> None:
    for campo in ("nome", "classe", "materia"):
        chave_widget = f"criacao_{campo}_widget"
        if chave_widget not in st.session_state:
            st.session_state[chave_widget] = st.session_state[f"criacao_{campo}"]
    st.session_state.criacao_conteudo_widget = st.session_state.criacao_conteudo


def salvar_personalizacao() -> None:
    preferencias = st.session_state.criacao_preferencias
    for chave in PREFERENCIAS:
        chave_widget = f"criacao_pref_{chave}"
        if chave_widget in st.session_state:
            preferencias[chave] = st.session_state[chave_widget]
    if "criacao_instrucao_widget" in st.session_state:
        st.session_state.criacao_instrucao = st.session_state.criacao_instrucao_widget


def preparar_personalizacao() -> None:
    for chave, selecionada in st.session_state.criacao_preferencias.items():
        st.session_state[f"criacao_pref_{chave}"] = selecionada
    st.session_state.criacao_instrucao_widget = st.session_state.criacao_instrucao


def preferencias_selecionadas() -> list[str]:
    return [chave for chave in PREFERENCIAS if st.session_state.criacao_preferencias[chave]]


def continuar_para_personalizacao() -> None:
    salvar_entrada()
    texto = st.session_state.criacao_conteudo.strip()
    if not texto:
        st.warning("Escreva o conteúdo da atividade para continuar.")
        return
    atividade = atividade_atual()
    atividade.texto = texto
    atividade.tema = "Atividade criada"
    st.session_state.criacao_etapa = "personalizacao"


def gerar_exercicio() -> None:
    salvar_personalizacao()
    atividade = atividade_atual()
    selecionadas = preferencias_selecionadas()
    suportadas = [chave for chave in selecionadas if chave in PREFERENCIAS_SUPORTADAS]
    if not selecionadas:
        st.warning("Selecione ao menos uma opção para prosseguir.")
        return
    atividade.instrucao = st.session_state.criacao_instrucao.strip()
    resultado, realizadas = adaptar_exercicio(atividade.texto, suportadas)
    st.session_state.criacao_resultado = resultado
    st.session_state.criacao_realizadas = realizadas
    st.session_state.criacao_ultimo_salvo_id = ""
    st.session_state.criacao_salvo = False
    st.session_state.criacao_etapa = "resultado"


def editar_texto() -> None:
    st.session_state.criacao_conteudo = atividade_atual().texto
    st.session_state.criacao_etapa = "entrada"


def voltar_para_entrada() -> None:
    salvar_personalizacao()
    st.session_state.criacao_etapa = "entrada"


def adaptar_novamente() -> None:
    st.session_state.criacao_etapa = "personalizacao"


def nova_atividade() -> None:
    st.session_state.criacao_atividade = Atividade()
    st.session_state.criacao_etapa = "entrada"
    st.session_state.criacao_conteudo = ""
    st.session_state.criacao_nome = ""
    st.session_state.criacao_classe = ""
    st.session_state.criacao_materia = ""
    st.session_state.criacao_resultado = ""
    st.session_state.criacao_realizadas = []
    st.session_state.criacao_instrucao = ""
    st.session_state.criacao_preferencias = {chave: False for chave in PREFERENCIAS}
    st.session_state.criacao_salvo = False
    st.session_state.criacao_ultimo_salvo_id = ""
    for campo in ("nome", "classe", "materia"):
        st.session_state.pop(f"criacao_{campo}_widget", None)


def salvar_exercicio() -> None:
    if st.session_state.get("criacao_ultimo_salvo_id"):
        return
    atividade = atividade_atual()
    item = salvar_exercicio_local(
        atividade,
        st.session_state.criacao_resultado,
        [PREFERENCIAS[chave] for chave in preferencias_selecionadas()],
        "criado",
    )
    st.session_state.criacao_ultimo_salvo_id = item.identificador
    st.session_state.criacao_salvo = True


def tela_entrada() -> None:
    preparar_entrada()
    st.title("Criar novo exercício")
    st.markdown('<div class="subtitle">Prepare um conteúdo para personalizar. Não há geração por IA nesta versão.</div>', unsafe_allow_html=True)
    st.markdown('<div class="web-section-title">Informações do exercício</div>', unsafe_allow_html=True)
    nome, classe, materia = st.columns(3)
    with nome:
        st.text_input("Nome do exercício", key="criacao_nome_widget", on_change=salvar_entrada)
    with classe:
        st.text_input("Classe/Ano", key="criacao_classe_widget", on_change=salvar_entrada)
    with materia:
        st.text_input("Matéria", key="criacao_materia_widget", on_change=salvar_entrada)
    with st.container(border=True):
        st.markdown('<div class="web-section-title">Enunciado ou conteúdo da atividade</div>', unsafe_allow_html=True)
        st.text_area("Enunciado ou conteúdo da atividade", key="criacao_conteudo_widget", height=300, label_visibility="collapsed", on_change=salvar_entrada)
        st.button("Continuar para personalização →", key="criacao_continuar", on_click=continuar_para_personalizacao, type="primary")


def tela_personalizacao() -> None:
    preparar_personalizacao()
    st.button("← Voltar", key="criacao_voltar_personalizacao", on_click=voltar_para_entrada)
    st.title("Personalização pedagógica")
    st.markdown('<div class="subtitle">Selecione estratégias e registre a sua orientação para a atividade.</div>', unsafe_allow_html=True)
    primeira_linha = st.columns(2, gap="large")
    segunda_linha = st.columns(2, gap="large")
    for coluna, (grupo, chaves) in zip((*primeira_linha, *segunda_linha), GRUPOS.items()):
        with coluna:
            with st.container(key=f"criacao_grupo_{grupo.lower().replace(' ', '_')}"):
                st.markdown(f'<div class="web-section-title">{grupo}</div>', unsafe_allow_html=True)
                for chave in chaves:
                    st.checkbox(PREFERENCIAS[chave], key=f"criacao_pref_{chave}", on_change=salvar_personalizacao)
    st.markdown('<div class="instrucao-livre"><div class="web-section-title">✦ Instrução personalizada</div><div class="muted">Como você gostaria que o exercício fosse adaptado?</div></div>', unsafe_allow_html=True)
    st.text_area("Instrução personalizada", key="criacao_instrucao_widget", height=130, label_visibility="collapsed", placeholder="Ex.: destaque os números importantes em azul.", on_change=salvar_personalizacao)
    st.button("Gerar exercício adaptado →", key="criacao_gerar", on_click=gerar_exercicio, type="primary")


def tela_resultado() -> None:
    atividade = atividade_atual()
    st.button("← Voltar", key="criacao_voltar_resultado", on_click=adaptar_novamente)
    st.title("Exercício adaptado")
    st.markdown('<div class="subtitle">Revise o resultado antes de salvar ou iniciar uma nova atividade.</div>', unsafe_allow_html=True)
    original, adaptado = st.columns([1, 2], gap="large")
    with original:
        st.markdown('<div class="web-section-title">VERSÃO ORIGINAL</div>', unsafe_allow_html=True)
        st.text_area("Versão original", value=atividade.texto, height=250, disabled=True, label_visibility="collapsed", key="criacao_original")
    with adaptado:
        st.markdown('<div class="web-section-title destaque-resultado">EXERCÍCIO ADAPTADO</div>', unsafe_allow_html=True)
        st.text_area("Exercício adaptado", value=st.session_state.criacao_resultado, height=390, disabled=True, label_visibility="collapsed", key="criacao_adaptado")
        st.markdown('<div class="web-section-title">Recursos utilizados na adaptação</div>', unsafe_allow_html=True)
        realizadas = st.session_state.criacao_realizadas
        st.markdown("\n".join(f"✓ {item}" for item in realizadas) if realizadas else "Nenhuma adaptação registrada.")
        if atividade.instrucao:
            st.caption(f"Orientação registrada pelo professor: {atividade.instrucao}")
    nova, editar, novamente, salvar = st.columns(4)
    with nova:
        st.button("← Nova atividade", key="criacao_nova", on_click=nova_atividade)
    with editar:
        st.button("Editar texto", key="criacao_editar", on_click=editar_texto)
    with novamente:
        st.button("Adaptar novamente", key="criacao_novamente", on_click=adaptar_novamente)
    with salvar:
        st.button("Salvar exercício", key="criacao_salvar", on_click=salvar_exercicio, type="primary")
    if st.session_state.criacao_salvo:
        st.success("O exercício foi salvo no histórico local.")


def renderizar_criacao() -> None:
    """Renderiza a criação manual sem afetar o fluxo de adaptação já migrado."""
    inicializar_estado()
    etapa = st.session_state.criacao_etapa
    if etapa == "entrada":
        tela_entrada()
    elif etapa == "personalizacao":
        tela_personalizacao()
    else:
        tela_resultado()
