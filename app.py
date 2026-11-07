"""
Ponto de entrada do app. Rode com:  streamlit run app.py  (ou ./run.sh)

Como o Streamlit funciona: a cada clique ou digitação, ESTE ARQUIVO
INTEIRO é executado de novo, de cima para baixo. Por isso não há
"eventos" como em outros frameworks: o código simplesmente lê o valor
atual de cada widget e desenha a tela de acordo.
"""

import streamlit as st

import db
from paginas import analise, categorias, evolucao, lancamentos, painel

st.set_page_config(page_title="Finanças Pessoais", page_icon="💰", layout="wide")

# Cria o banco e as categorias padrão na primeira execução (depois não faz nada).
db.inicializar_banco()

# Nome no menu -> função que desenha a página.
PAGINAS = {
    "Painel do mês": painel.mostrar,
    "Lançamentos": lancamentos.mostrar,
    "Categorias": categorias.mostrar,
    "Análise": analise.mostrar,
    "Evolução": evolucao.mostrar,
}

st.sidebar.title("💰 Finanças")
escolha = st.sidebar.radio("Menu", list(PAGINAS), label_visibility="collapsed")
PAGINAS[escolha]()
