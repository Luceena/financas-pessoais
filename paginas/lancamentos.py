"""Página de lançamentos: cadastrar, listar, editar, excluir e exportar CSV."""

from datetime import date

import pandas as pd
import streamlit as st

import db
from formatos import (centavos_para_csv, centavos_para_reais, centavos_para_texto,
                      date_para_iso, iso_para_br, texto_para_centavos)
from paginas.comum import avisar, mostrar_aviso, seletor_mes_ano


def mostrar() -> None:
    st.header("Lançamentos")
    mostrar_aviso()
    _formulario_novo()
    st.divider()
    lancamentos = _lista()
    st.divider()
    _editar_excluir(lancamentos)


def _validar(descricao: str, valor_texto: str) -> int:
    """Confere os campos e devolve o valor em centavos (ou lança ValueError)."""
    if not descricao.strip():
        raise ValueError("Informe a descrição.")
    return texto_para_centavos(valor_texto)


# ---------------------------------------------------------------------------
# Cadastro
# ---------------------------------------------------------------------------

def _formulario_novo() -> None:
    st.subheader("Novo lançamento")

    # Depois de salvar, limpamos os campos. Isso precisa acontecer ANTES de
    # os widgets serem criados, por isso usamos uma "bandeira" no session_state.
    if st.session_state.pop("_limpar_novo", False):
        st.session_state["novo_descricao"] = ""
        st.session_state["novo_valor"] = ""

    # O tipo fica fora do formulário para a lista de categorias mudar na hora.
    tipo = st.radio("Tipo", ["despesa", "receita"], format_func=str.capitalize,
                    horizontal=True, key="novo_tipo")
    categorias = db.listar_categorias(tipo)
    if not categorias:
        st.warning(f"Crie uma categoria de {tipo} na página Categorias primeiro.")
        return
    nomes = {c["id"]: c["nome"] for c in categorias}

    with st.form("form_novo"):
        col1, col2 = st.columns(2)
        data = col1.date_input("Data", value=date.today(), format="DD/MM/YYYY")
        valor_texto = col2.text_input("Valor (R$)", placeholder="1.234,56", key="novo_valor")
        descricao = st.text_input("Descrição", key="novo_descricao")
        categoria_id = st.selectbox("Categoria", list(nomes), format_func=nomes.get)

        if st.form_submit_button("Salvar", type="primary"):
            try:
                centavos = _validar(descricao, valor_texto)
            except ValueError as erro:
                st.error(str(erro))
                return
            db.inserir_lancamento(date_para_iso(data), descricao, centavos, categoria_id)
            st.session_state["_limpar_novo"] = True
            avisar(f"{tipo.capitalize()} de {centavos_para_reais(centavos)} salva.")
            st.rerun()


# ---------------------------------------------------------------------------
# Lista e exportação
# ---------------------------------------------------------------------------

def _lista() -> list[dict]:
    st.subheader("Lista")
    ano, mes = seletor_mes_ano("lista", permitir_todos=True)
    lancamentos = db.listar_lancamentos(ano, mes)

    if not lancamentos:
        st.info("Nenhum lançamento nesse período.")
        return lancamentos

    tabela = pd.DataFrame([{
        "Data": iso_para_br(l["data"]),
        "Descrição": l["descricao"],
        "Categoria": l["categoria"],
        "Tipo": l["tipo"].capitalize(),
        "Valor": centavos_para_reais(l["valor_centavos"]),
    } for l in lancamentos])
    st.dataframe(tabela, hide_index=True, use_container_width=True)
    st.caption(f"{len(lancamentos)} lançamento(s).")

    # O arquivo é gerado em memória e baixado pelo navegador (vai para a
    # sua pasta de Downloads), então nada é salvo dentro do projeto.
    if ano is None:
        nome_arquivo = "lancamentos_todos.csv"
    elif mes is None:
        nome_arquivo = f"lancamentos_{ano}.csv"
    else:
        nome_arquivo = f"lancamentos_{ano}-{mes:02d}.csv"
    st.download_button("Exportar CSV", data=_gerar_csv(lancamentos),
                       file_name=nome_arquivo, mime="text/csv")
    return lancamentos


def _gerar_csv(lancamentos: list[dict]) -> bytes:
    """
    CSV no padrão brasileiro: separador ';' e vírgula decimal, para o
    LibreOffice/Excel em português abrirem os valores como números.
    'utf-8-sig' coloca uma marca no início que faz o Excel ler os acentos.
    """
    tabela = pd.DataFrame([{
        "data": iso_para_br(l["data"]),
        "descricao": l["descricao"],
        "categoria": l["categoria"],
        "tipo": l["tipo"],
        "valor": centavos_para_csv(l["valor_centavos"]),
    } for l in lancamentos])
    return tabela.to_csv(sep=";", index=False).encode("utf-8-sig")


# ---------------------------------------------------------------------------
# Edição e exclusão
# ---------------------------------------------------------------------------

def _editar_excluir(lancamentos: list[dict]) -> None:
    st.subheader("Editar ou excluir")
    if not lancamentos:
        st.caption("Escolha um período com lançamentos na lista acima.")
        return

    por_id = {l["id"]: l for l in lancamentos}
    escolhido = st.selectbox(
        "Lançamento", list(por_id),
        format_func=lambda i: (f"{iso_para_br(por_id[i]['data'])} · {por_id[i]['descricao']}"
                               f" · {centavos_para_reais(por_id[i]['valor_centavos'])}"),
        key="editar_escolhido",
    )
    lanc = por_id[escolhido]

    todas = db.listar_categorias()
    nomes = {c["id"]: f"{c['nome']} ({c['tipo']})" for c in todas}
    ids = list(nomes)

    # As chaves dos campos incluem o id do lançamento: assim, ao trocar de
    # lançamento, os campos são recriados já com os valores do novo.
    sufixo = lanc["id"]
    with st.form(f"form_editar_{sufixo}"):
        col1, col2 = st.columns(2)
        data = col1.date_input("Data", value=date.fromisoformat(lanc["data"]),
                               format="DD/MM/YYYY", key=f"ed_data_{sufixo}")
        valor_texto = col2.text_input("Valor (R$)", value=centavos_para_texto(lanc["valor_centavos"]),
                                      key=f"ed_valor_{sufixo}")
        descricao = st.text_input("Descrição", value=lanc["descricao"], key=f"ed_desc_{sufixo}")
        categoria_id = st.selectbox("Categoria", ids, index=ids.index(lanc["categoria_id"]),
                                    format_func=nomes.get, key=f"ed_cat_{sufixo}")
        confirmar = st.checkbox("Confirmo que quero excluir este lançamento", key=f"ed_conf_{sufixo}")

        col_salvar, col_excluir = st.columns(2)
        salvar = col_salvar.form_submit_button("Salvar alterações", type="primary")
        excluir = col_excluir.form_submit_button("Excluir")

    if salvar:
        try:
            centavos = _validar(descricao, valor_texto)
        except ValueError as erro:
            st.error(str(erro))
            return
        db.atualizar_lancamento(lanc["id"], date_para_iso(data), descricao, centavos, categoria_id)
        avisar("Lançamento atualizado.")
        st.rerun()

    if excluir:
        if not confirmar:
            st.error("Marque a confirmação antes de excluir.")
            return
        db.excluir_lancamento(lanc["id"])
        avisar("Lançamento excluído.")
        st.rerun()
