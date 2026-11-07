"""Análise: ranking das categorias que mais gastam e que mais rendem."""

import altair as alt
import pandas as pd
import streamlit as st

import db
from formatos import MESES, centavos_para_reais
from paginas.comum import COR_DESPESA, COR_RECEITA, ROTULO_REAIS, seletor_mes_ano


def mostrar() -> None:
    st.header("Análise por categoria")
    ano, mes = seletor_mes_ano("analise")

    aba_mes, aba_ano = st.tabs([f"{MESES[mes - 1]} de {ano}", f"Ano de {ano}"])
    with aba_mes:
        _secao(ano, mes)
    with aba_ano:
        _secao(ano, None)


def _secao(ano: int, mes: int | None) -> None:
    col_despesas, col_receitas = st.columns(2)
    with col_despesas:
        _ranking("despesa", ano, mes, "Onde mais gasto", COR_DESPESA)
    with col_receitas:
        _ranking("receita", ano, mes, "De onde vem meu dinheiro", COR_RECEITA)


def _ranking(tipo: str, ano: int, mes: int | None, titulo: str, cor: str) -> None:
    st.subheader(titulo)
    dados = db.total_por_categoria(tipo, ano, mes)  # já vem do maior para o menor
    if not dados:
        st.info("Sem lançamentos no período.")
        return

    total = sum(d["total"] for d in dados)
    tabela = pd.DataFrame({
        "Categoria": [d["categoria"] for d in dados],
        # Reais em float servem só para desenhar o gráfico; os textos
        # exibidos ao usuário saem dos centavos exatos.
        "Reais": [d["total"] / 100 for d in dados],
        "Valor": [centavos_para_reais(d["total"]) for d in dados],
        "% do total": [f"{100 * d['total'] / total:.1f}%".replace(".", ",") for d in dados],
    })

    grafico = alt.Chart(tabela).mark_bar(color=cor).encode(
        x=alt.X("Reais:Q", title="R$", axis=alt.Axis(labelExpr=ROTULO_REAIS)),
        y=alt.Y("Categoria:N", sort="-x", title=None),  # maior barra no topo
        tooltip=["Categoria", "Valor", "% do total"],
    )
    st.altair_chart(grafico, use_container_width=True)

    ranking = tabela.drop(columns="Reais")
    ranking.insert(0, "#", range(1, len(ranking) + 1))
    st.dataframe(ranking, hide_index=True, use_container_width=True)
    st.caption(f"Total: {centavos_para_reais(total)}")
