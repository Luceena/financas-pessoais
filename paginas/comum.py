"""Peças de interface usadas por mais de uma página."""

from datetime import date

import streamlit as st

import db
from formatos import MESES

# Cores dos gráficos (verde = entra dinheiro, vermelho = sai dinheiro).
COR_RECEITA = "#2e9e5b"
COR_DESPESA = "#d9534f"

# Expressão do Vega (biblioteca usada pelo Altair) que formata os rótulos
# do eixo no padrão brasileiro: 12345 -> "12.345".
ROTULO_REAIS = "replace(format(datum.value, ',.0f'), regexp(',', 'g'), '.')"


def anos_disponiveis() -> list[int]:
    """Anos com lançamentos, sempre incluindo o ano atual."""
    return sorted(set(db.anos_com_lancamentos()) | {date.today().year}, reverse=True)


def seletor_mes_ano(chave: str, permitir_todos: bool = False) -> tuple:
    """
    Mostra dois seletores lado a lado (Mês e Ano) e devolve (ano, mes).

    Com `permitir_todos=True`, aparece a opção "Todos" em ambos:
    - ano=None  -> todos os lançamentos
    - mes=None  -> o ano inteiro
    `chave` diferencia os seletores de páginas diferentes.
    """
    hoje = date.today()
    col_mes, col_ano = st.columns(2)

    anos: list = anos_disponiveis()
    if permitir_todos:
        anos = [None] + anos
    ano = col_ano.selectbox(
        "Ano", anos, index=anos.index(hoje.year),
        format_func=lambda a: "Todos" if a is None else str(a),
        key=f"{chave}_ano",
    )

    meses: list = list(range(1, 13))
    if permitir_todos:
        meses = [None] + meses
    mes = col_mes.selectbox(
        "Mês", meses, index=meses.index(hoje.month),
        format_func=lambda m: "Todos" if m is None else MESES[m - 1],
        key=f"{chave}_mes",
        disabled=ano is None,  # sem ano escolhido, o mês não faz sentido
    )
    return ano, (None if ano is None else mes)


# Mensagens de sucesso que sobrevivem ao st.rerun().
# Quando salvamos algo, chamamos st.rerun() para a tela recarregar com os
# dados novos; mas o rerun apagaria um st.success() mostrado antes dele.
# Por isso guardamos a mensagem no session_state e mostramos na próxima execução.

def avisar(mensagem: str) -> None:
    st.session_state["_aviso"] = mensagem


def mostrar_aviso() -> None:
    mensagem = st.session_state.pop("_aviso", None)
    if mensagem:
        st.success(mensagem)
