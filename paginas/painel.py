"""Painel do mês: totais de receitas, despesas e saldo."""

import pandas as pd
import streamlit as st

import db
from formatos import MESES, centavos_para_reais, iso_para_br
from paginas.comum import seletor_mes_ano


def mostrar() -> None:
    st.header("Painel do mês")
    ano, mes = seletor_mes_ano("painel")

    totais = db.totais_periodo(ano, mes)
    receitas, despesas = totais["receita"], totais["despesa"]
    saldo = receitas - despesas

    col1, col2, col3 = st.columns(3)
    col1.metric("Receitas", centavos_para_reais(receitas))
    col2.metric("Despesas", centavos_para_reais(despesas))
    col3.metric("Saldo", centavos_para_reais(saldo))

    if saldo < 0:
        st.warning("Neste mês você gastou mais do que recebeu.")

    st.subheader(f"Lançamentos de {MESES[mes - 1]} de {ano}")
    lancamentos = db.listar_lancamentos(ano, mes)
    if not lancamentos:
        st.info("Nenhum lançamento neste mês.")
        return
    tabela = pd.DataFrame([{
        "Data": iso_para_br(l["data"]),
        "Descrição": l["descricao"],
        "Categoria": l["categoria"],
        "Tipo": l["tipo"].capitalize(),
        "Valor": centavos_para_reais(l["valor_centavos"]),
    } for l in lancamentos])
    st.dataframe(tabela, hide_index=True, use_container_width=True)
