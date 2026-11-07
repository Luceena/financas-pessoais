"""Página de categorias: criar, renomear e excluir (movendo lançamentos)."""

import pandas as pd
import streamlit as st

import db
from paginas.comum import avisar, mostrar_aviso


def mostrar() -> None:
    st.header("Categorias")
    mostrar_aviso()

    categorias = db.listar_categorias()
    _tabelas(categorias)
    st.divider()

    aba_criar, aba_renomear, aba_excluir = st.tabs(["Criar", "Renomear", "Excluir"])
    with aba_criar:
        _criar()
    with aba_renomear:
        _renomear(categorias)
    with aba_excluir:
        _excluir(categorias)


def _rotulo(c: dict) -> str:
    return f"{c['nome']} ({c['tipo']})"


def _tabelas(categorias: list[dict]) -> None:
    """Mostra receitas e despesas lado a lado, com a contagem de lançamentos."""
    colunas = st.columns(2)
    for coluna, tipo, titulo in zip(colunas, ["receita", "despesa"], ["Receitas", "Despesas"]):
        with coluna:
            st.subheader(titulo)
            linhas = [{"Categoria": c["nome"], "Lançamentos": c["qtd"]}
                      for c in categorias if c["tipo"] == tipo]
            st.dataframe(pd.DataFrame(linhas), hide_index=True, use_container_width=True)


def _criar() -> None:
    with st.form("form_criar_categoria", clear_on_submit=True):
        nome = st.text_input("Nome")
        tipo = st.radio("Tipo", ["despesa", "receita"], format_func=str.capitalize, horizontal=True)
        if st.form_submit_button("Criar", type="primary"):
            try:
                db.criar_categoria(nome, tipo)
            except ValueError as erro:
                st.error(str(erro))
                return
            avisar(f"Categoria '{nome.strip()}' criada.")
            st.rerun()


def _renomear(categorias: list[dict]) -> None:
    por_id = {c["id"]: c for c in categorias}
    with st.form("form_renomear_categoria"):
        categoria_id = st.selectbox("Categoria", list(por_id),
                                    format_func=lambda i: _rotulo(por_id[i]))
        novo_nome = st.text_input("Novo nome")
        if st.form_submit_button("Renomear", type="primary"):
            try:
                db.renomear_categoria(categoria_id, novo_nome)
            except ValueError as erro:
                st.error(str(erro))
                return
            avisar(f"'{por_id[categoria_id]['nome']}' agora se chama '{novo_nome.strip()}'.")
            st.rerun()


def _excluir(categorias: list[dict]) -> None:
    """
    Sem lançamentos: exclui direto (com confirmação).
    Com lançamentos: pede uma categoria de destino do mesmo tipo, move os
    lançamentos para ela e então exclui. O banco (ON DELETE RESTRICT)
    impediria excluir sem mover, então esse passo é obrigatório.
    """
    por_id = {c["id"]: c for c in categorias}
    categoria_id = st.selectbox("Categoria a excluir", list(por_id),
                                format_func=lambda i: _rotulo(por_id[i]), key="excluir_cat")
    cat = por_id[categoria_id]
    destino_id = None

    if cat["qtd"] > 0:
        st.warning(f"'{cat['nome']}' tem {cat['qtd']} lançamento(s). "
                   "Escolha para onde movê-los antes de excluir.")
        opcoes = {c["id"]: c["nome"] for c in categorias
                  if c["tipo"] == cat["tipo"] and c["id"] != cat["id"]}
        if not opcoes:
            st.info(f"Não há outra categoria de {cat['tipo']}. Crie uma na aba 'Criar' primeiro.")
            return
        destino_id = st.selectbox("Mover lançamentos para", list(opcoes),
                                  format_func=opcoes.get, key="excluir_destino")

    confirmar = st.checkbox(f"Confirmo que quero excluir '{cat['nome']}'",
                            key=f"excluir_conf_{categoria_id}")
    texto_botao = "Mover lançamentos e excluir" if destino_id else "Excluir"
    if st.button(texto_botao, disabled=not confirmar, key="excluir_botao"):
        try:
            db.excluir_categoria(categoria_id, mover_para_id=destino_id)
        except ValueError as erro:
            st.error(str(erro))
            return
        avisar(f"Categoria '{cat['nome']}' excluída.")
        st.rerun()
