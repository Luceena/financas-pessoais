#!/usr/bin/env bash
# Abre o app. Na primeira vez, cria o ambiente virtual e instala as dependências.
set -e

# Vai para a pasta deste script, para funcionar de qualquer lugar.
cd "$(dirname "$0")"

if [ ! -d venv ]; then
    echo "Criando ambiente virtual (só na primeira vez)..."
    python3 -m venv venv
    ./venv/bin/pip install --upgrade pip
    ./venv/bin/pip install -r requirements.txt
fi

source venv/bin/activate
streamlit run app.py
