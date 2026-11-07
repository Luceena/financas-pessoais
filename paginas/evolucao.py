"""Evolução: receitas x despesas mês a mês ao longo de um ano."""

import altair as alt
import pandas as pd
import streamlit as st

import db
from formatos import MESES_ABREV, centavos_para_reais
from paginas.comum import COR_DESPESA, COR_RECEITA, ROTULO_REAIS, anos_disponiveis


def mostrar() -> None:
    st.header("Evolução mensal")
    ano = st.selectbox("Ano", anos_disponiveis(), key="evolucao_ano")
    meses = db.totais_mensais(ano)

    # Formato "longo" (uma linha por mês e tipo), que é o que o Altair
    # precisa para desenhar barras agrupadas com cores por tipo.
    longo = []
    for m in meses:
        for tipo, rotulo in [("receita", "Receitas"), ("despesa", "Despesas")]:
            longo.append({
                "Mês": MESES_ABREV[m["mes"] - 1],
                "Tipo": rotulo,
                "Reais": m[tipo] / 100,  # só para o desenho
                "Valor": centavos_para_reais(m[tipo]),
            })

    grafico = alt.Chart(pd.DataFrame(longo)).mark_bar().encode(
        x=alt.X("Mês:N", sort=MESES_ABREV, title=None, axis=alt.Axis(labelAngle=0)),
        xOffset=alt.XOffset("Tipo:N", sort=["Receitas", "Despesas"]),  # barras lado a lado
        y=alt.Y("Reais:Q", title="R$", axis=alt.Axis(labelExpr=ROTULO_REAIS)),
        color=alt.Color("Tipo:N",
                        scale=alt.Scale(domain=["Receitas", "Despesas"],
                                        range=[COR_RECEITA, COR_DESPESA]),
                        legend=alt.Legend(title=None, orient="top")),
        tooltip=["Mês", "Tipo", "Valor"],
    )
    st.altair_chart(grafico, use_container_width=True)

    # Tabela com saldo de cada mês e o total do ano.
    linhas = [{
        "Mês": MESES_ABREV[m["mes"] - 1],
        "Receitas": centavos_para_reais(m["receita"]),
        "Despesas": centavos_para_reais(m["despesa"]),
        "Saldo": centavos_para_reais(m["receita"] - m["despesa"]),
    } for m in meses]
    total_rec = sum(m["receita"] for m in meses)
    total_desp = sum(m["despesa"] for m in meses)
    linhas.append({
        "Mês": "Total",
        "Receitas": centavos_para_reais(total_rec),
        "Despesas": centavos_para_reais(total_desp),
        "Saldo": centavos_para_reais(total_rec - total_desp),
    })
    st.dataframe(pd.DataFrame(linhas), hide_index=True, use_container_width=True)
