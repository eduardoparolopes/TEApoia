"""Biblioteca local da versão Streamlit, usando o armazenamento da V3."""

import json

import streamlit as st
import streamlit.components.v1 as components

from armazenamento import BibliotecaLocal, ExercicioSalvo
from estado import Atividade
from formatacao_exercicio import texto_puro_para_copia


def salvar_exercicio_local(
    atividade: Atividade,
    resultado: str,
    preferencias: list[str],
    tipo: str,
) -> ExercicioSalvo:
    """Persiste um resultado web no mesmo JSON utilizado pela interface Tkinter."""
    item = ExercicioSalvo(
        nome=atividade.nome or atividade.tema or "Atividade adaptada",
        classe=atividade.classe or "Não informado",
        materia=atividade.materia or "Não informado",
        texto=atividade.texto,
        texto_ocr=atividade.texto_ocr,
        adaptado=resultado,
        preferencias=preferencias,
        instrucao=atividade.instrucao,
        tipo=tipo,
    )
    return BibliotecaLocal().salvar(item, atividade.imagem)


def abrir_exercicio(identificador: str) -> None:
    st.session_state.biblioteca_exercicio_id = identificador


def voltar_para_lista() -> None:
    st.session_state.biblioteca_exercicio_id = ""


def excluir_exercicio(identificador: str) -> None:
    BibliotecaLocal().excluir(identificador)
    if st.session_state.get("biblioteca_exercicio_id") == identificador:
        st.session_state.biblioteca_exercicio_id = ""


def tipo_exibicao(item: ExercicioSalvo) -> str:
    return "Criado" if tipo_normalizado(item) == "criado" else "Adaptado"


def tipo_normalizado(item: ExercicioSalvo) -> str:
    """Mantém a biblioteca aberta mesmo com objetos carregados antes do campo tipo."""
    return "criado" if getattr(item, "tipo", "adaptado") == "criado" else "adaptado"


def botao_copiar(conteudo: str) -> None:
    """Exibe um controle compacto que copia texto sem navegar ou alterar o exercício."""
    texto_json = json.dumps(texto_puro_para_copia(conteudo)).replace("</", "<\\/")
    components.html(
        f"""
        <style>
            html, body {{ margin: 0; background: transparent; font-family: "Source Sans Pro", sans-serif; }}
            button {{
                box-sizing: border-box; width: 100%; height: 36px; padding: .35rem .6rem;
                border: 1px solid #D0D9E8; border-radius: .65rem; background: #FFFFFF;
                color: #344054; font-size: 14px; font-weight: 600; line-height: 1.25; cursor: pointer;
            }}
            button:hover {{ background: #EAF2FF; border-color: #BFDBFE; color: #1D4ED8; }}
            button:focus-visible {{ outline: 2px solid #2563EB; outline-offset: 2px; }}
        </style>
        <button type="button" id="copiar" aria-label="Copiar exercício">Copiar</button>
        <script>
            const conteudo = {texto_json};
            const botao = document.getElementById("copiar");

            function copiarComFallback() {{
                const area = document.createElement("textarea");
                area.value = conteudo;
                area.setAttribute("readonly", "");
                area.style.position = "fixed";
                area.style.opacity = "0";
                document.body.appendChild(area);
                area.select();
                document.execCommand("copy");
                area.remove();
            }}

            botao.addEventListener("click", async () => {{
                try {{
                    if (navigator.clipboard && window.isSecureContext) {{
                        await navigator.clipboard.writeText(conteudo);
                    }} else {{
                        copiarComFallback();
                    }}
                    botao.textContent = "Copiado!";
                    window.setTimeout(() => {{
                        botao.textContent = "Copiar";
                    }}, 1600);
                }} catch (erro) {{
                    copiarComFallback();
                    botao.textContent = "Copiado!";
                    window.setTimeout(() => {{
                        botao.textContent = "Copiar";
                    }}, 1600);
                }}
            }});
        </script>
        """,
        height=36,
        scrolling=False,
    )


def tela_lista() -> None:
    st.title("Meus exercícios")
    st.markdown('<div class="subtitle">Histórico local dos exercícios salvos no TEApoia.</div>', unsafe_allow_html=True)
    itens = BibliotecaLocal().listar()
    if not itens:
        st.markdown('<div class="info-card"><div class="muted">Nenhum exercício salvo ainda.</div></div>', unsafe_allow_html=True)
        return
    for item in itens:
        with st.container(border=True):
            informacoes, copiar, abrir, excluir = st.columns([5, 1, 1, .42], vertical_alignment="center")
            with informacoes:
                st.markdown(f'<div class="card-title">{item.nome}</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="muted">{item.materia} · {item.classe} · {tipo_exibicao(item)}<br>{item.atualizado_em}</div>',
                    unsafe_allow_html=True,
                )
            with copiar:
                botao_copiar(item.adaptado)
            with abrir:
                st.button("Abrir", key=f"biblioteca_abrir_{item.identificador}", on_click=abrir_exercicio, args=(item.identificador,), use_container_width=True)
            with excluir:
                st.button(
                    "✕",
                    key=f"biblioteca_excluir_{item.identificador}",
                    on_click=excluir_exercicio,
                    args=(item.identificador,),
                    help="Excluir exercício",
                    use_container_width=True,
                )


def tela_detalhe(item: ExercicioSalvo) -> None:
    st.button("← Voltar", key="biblioteca_voltar", on_click=voltar_para_lista)
    cabecalho, copiar = st.columns([6, 1], vertical_alignment="center")
    with cabecalho:
        st.title(item.nome)
        st.markdown(
            f'<div class="subtitle">{item.materia} · {item.classe} · {tipo_exibicao(item)} · salvo em {item.atualizado_em}</div>',
            unsafe_allow_html=True,
        )
    with copiar:
        botao_copiar(item.adaptado)
    if tipo_normalizado(item) == "criado":
        st.markdown('<div class="web-section-title">CONTEÚDO CRIADO</div>', unsafe_allow_html=True)
        st.text_area("Conteúdo criado", value=item.adaptado, height=380, disabled=True, label_visibility="collapsed", key=f"biblioteca_criado_{item.identificador}")
    else:
        original, adaptado = st.columns([1, 2], gap="large")
        with original:
            st.markdown('<div class="web-section-title">VERSÃO ORIGINAL</div>', unsafe_allow_html=True)
            st.text_area("Versão original", value=item.texto, height=260, disabled=True, label_visibility="collapsed", key=f"biblioteca_original_{item.identificador}")
        with adaptado:
            st.markdown('<div class="web-section-title destaque-resultado">EXERCÍCIO ADAPTADO</div>', unsafe_allow_html=True)
            st.text_area("Exercício adaptado", value=item.adaptado, height=380, disabled=True, label_visibility="collapsed", key=f"biblioteca_adaptado_{item.identificador}")
    st.markdown('<div class="web-section-title">Personalização utilizada</div>', unsafe_allow_html=True)
    st.markdown("\n".join(f"✓ {valor}" for valor in item.preferencias) if item.preferencias else "Nenhuma preferência registrada.")
    st.caption(f"Instrução personalizada: {item.instrucao or 'Não informada.'}")


def renderizar_biblioteca() -> None:
    """Mantém apenas a seleção temporária na sessão; os dados permanecem no JSON local."""
    st.session_state.setdefault("biblioteca_exercicio_id", "")
    identificador = st.session_state.biblioteca_exercicio_id
    if not identificador:
        tela_lista()
        return
    item = BibliotecaLocal().buscar(identificador)
    if item is None:
        voltar_para_lista()
        st.warning("O exercício selecionado não foi encontrado.")
        tela_lista()
        return
    tela_detalhe(item)
