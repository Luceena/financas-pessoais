"""
Funções de conversão e formatação.

Este módulo não conhece o Streamlit nem o banco de dados: só transforma
valores de um formato para outro. Isso facilita testar e reaproveitar.

Convenções do projeto:
- Dinheiro é guardado em CENTAVOS (int). Ex.: R$ 12,34 -> 1234.
  Usamos inteiros para evitar os erros de arredondamento do float
  (em float, 0.1 + 0.2 != 0.3).
- Datas são guardadas em ISO ('AAAA-MM-DD') e exibidas como dd/mm/aaaa.
"""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

MESES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]
MESES_ABREV = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
               "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


# ---------------------------------------------------------------------------
# Dinheiro
# ---------------------------------------------------------------------------

def texto_para_centavos(texto: str) -> int:
    """
    Converte o que o usuário digitou em centavos.

    Aceita: "1.234,56", "1234,56", "R$ 50", "12.5" e "12.50".
    Regra: se tem vírgula, ela é o separador decimal (formato BR) e os
    pontos são separadores de milhar. Sem vírgula, um único ponto seguido
    de 1 ou 2 dígitos é tratado como decimal; senão, os pontos são milhar.

    Lança ValueError com uma mensagem amigável se o valor for inválido.
    """
    t = texto.strip().replace("R$", "").replace(" ", "")
    if not t:
        raise ValueError("Informe um valor.")

    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    elif t.count(".") == 1 and len(t.split(".")[1]) <= 2:
        pass  # "12.5" ou "12.50": o ponto já é o decimal
    else:
        t = t.replace(".", "")  # "1.234" ou "1.234.567": pontos de milhar

    try:
        # Decimal faz a conta exata (sem os problemas do float).
        centavos = int((Decimal(t) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    except (InvalidOperation, ValueError):
        raise ValueError(f"Valor inválido: '{texto}'. Use o formato 1.234,56.")

    if centavos <= 0:
        raise ValueError("O valor deve ser maior que zero.")
    return centavos


def centavos_para_texto(centavos: int) -> str:
    """1234567 -> '12.345,67' (sem o 'R$'). Usado para preencher campos."""
    sinal = "-" if centavos < 0 else ""
    reais, cent = divmod(abs(centavos), 100)
    # f"{reais:,}" usa vírgula como milhar (padrão americano); trocamos por ponto.
    return f"{sinal}{reais:,}".replace(",", ".") + f",{cent:02d}"


def centavos_para_reais(centavos: int) -> str:
    """1234567 -> 'R$ 12.345,67'; -500 -> '-R$ 5,00'."""
    sinal = "-" if centavos < 0 else ""
    return f"{sinal}R$ {centavos_para_texto(abs(centavos))}"


def centavos_para_csv(centavos: int) -> str:
    """1234567 -> '12345,67' (sem milhar, para planilhas lerem como número)."""
    return f"{centavos // 100},{centavos % 100:02d}"


# ---------------------------------------------------------------------------
# Datas
# ---------------------------------------------------------------------------

def iso_para_br(data_iso: str) -> str:
    """'2026-11-07' -> '07/11/2026'."""
    return date.fromisoformat(data_iso).strftime("%d/%m/%Y")


def date_para_iso(d: date) -> str:
    """date(2026, 11, 7) -> '2026-11-07' (formato guardado no banco)."""
    return d.isoformat()
