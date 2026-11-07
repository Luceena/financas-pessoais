"""
Camada de acesso ao banco de dados (SQLite).

Toda a comunicação com o banco passa por aqui. As páginas da interface
nunca escrevem SQL: elas só chamam as funções deste módulo. Assim, se um
dia você trocar o SQLite por outro banco, só este arquivo muda.

As funções devolvem listas de dicionários (ex.: [{"id": 1, "nome": ...}]),
que são fáceis de usar e de transformar em tabelas do pandas.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

# O banco fica na mesma pasta deste arquivo, não importa de onde o app é aberto.
CAMINHO_BANCO = Path(__file__).parent / "financas.db"

ESQUEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE categorias (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    nome   TEXT NOT NULL,
    tipo   TEXT NOT NULL CHECK (tipo IN ('receita', 'despesa')),
    UNIQUE (nome, tipo)
);

CREATE TABLE lancamentos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    data            TEXT    NOT NULL,              -- 'AAAA-MM-DD'
    descricao       TEXT    NOT NULL,
    valor_centavos  INTEGER NOT NULL CHECK (valor_centavos > 0),
    categoria_id    INTEGER NOT NULL
                    REFERENCES categorias(id) ON DELETE RESTRICT,
    criado_em       TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX idx_lancamentos_data ON lancamentos(data);
"""

CATEGORIAS_PADRAO = {
    "receita": ["Salário", "Comissões", "Freelance", "Outros"],
    "despesa": ["Alimentação", "Transporte", "Moradia", "Lazer",
                "Saúde", "Educação", "Outros"],
}


# ---------------------------------------------------------------------------
# Conexão
# ---------------------------------------------------------------------------

def conectar() -> sqlite3.Connection:
    """Abre uma conexão nova, já com as chaves estrangeiras ativadas."""
    con = sqlite3.connect(CAMINHO_BANCO)
    con.row_factory = sqlite3.Row          # permite acessar colunas pelo nome
    con.execute("PRAGMA foreign_keys = ON")  # o SQLite vem com isso DESLIGADO
    return con


@contextmanager
def conexao():
    """
    Uso: `with conexao() as con: ...`

    Se tudo der certo, faz commit; se der erro, desfaz (rollback).
    Em qualquer caso, fecha a conexão no final.
    """
    con = conectar()
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def _para_dicts(linhas) -> list[dict]:
    return [dict(linha) for linha in linhas]


def _intervalo(ano: int, mes: int | None = None) -> tuple[str, str]:
    """
    Devolve as datas de início e fim de um mês (ou do ano inteiro).

    Como as datas são texto ISO, a ordem alfabética é igual à cronológica,
    então podemos usar `data BETWEEN inicio AND fim`, que aproveita o índice.
    Usar dia 31 como fim funciona para qualquer mês ('2026-02-31' é só um
    texto de comparação; nenhuma data real fica de fora).
    """
    if mes is None:
        return f"{ano:04d}-01-01", f"{ano:04d}-12-31"
    return f"{ano:04d}-{mes:02d}-01", f"{ano:04d}-{mes:02d}-31"


def inicializar_banco() -> None:
    """Cria as tabelas e as categorias padrão, se o banco ainda não existir."""
    with conexao() as con:
        existe = con.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'categorias'"
        ).fetchone()
        if existe:
            return
        con.executescript(ESQUEMA)
        for tipo, nomes in CATEGORIAS_PADRAO.items():
            con.executemany(
                "INSERT INTO categorias (nome, tipo) VALUES (?, ?)",
                [(nome, tipo) for nome in nomes],
            )


# ---------------------------------------------------------------------------
# Categorias
# ---------------------------------------------------------------------------

def listar_categorias(tipo: str | None = None) -> list[dict]:
    """
    Lista as categorias (opcionalmente só de um tipo), com a quantidade
    de lançamentos de cada uma na coluna 'qtd'.
    """
    sql = """
        SELECT c.id, c.nome, c.tipo, COUNT(l.id) AS qtd
        FROM categorias c
        LEFT JOIN lancamentos l ON l.categoria_id = c.id
    """
    params: list = []
    if tipo:
        sql += " WHERE c.tipo = ?"
        params.append(tipo)
    sql += " GROUP BY c.id ORDER BY c.tipo, c.nome COLLATE NOCASE"
    with conexao() as con:
        return _para_dicts(con.execute(sql, params))


def criar_categoria(nome: str, tipo: str) -> None:
    nome = nome.strip()
    if not nome:
        raise ValueError("Informe o nome da categoria.")
    try:
        with conexao() as con:
            con.execute("INSERT INTO categorias (nome, tipo) VALUES (?, ?)", (nome, tipo))
    except sqlite3.IntegrityError:
        # A restrição UNIQUE (nome, tipo) impede duplicatas.
        raise ValueError(f"Já existe a categoria '{nome}' do tipo {tipo}.")


def renomear_categoria(categoria_id: int, novo_nome: str) -> None:
    novo_nome = novo_nome.strip()
    if not novo_nome:
        raise ValueError("Informe o novo nome.")
    try:
        with conexao() as con:
            con.execute("UPDATE categorias SET nome = ? WHERE id = ?", (novo_nome, categoria_id))
    except sqlite3.IntegrityError:
        raise ValueError(f"Já existe uma categoria '{novo_nome}' desse tipo.")


def excluir_categoria(categoria_id: int, mover_para_id: int | None = None) -> None:
    """
    Exclui uma categoria.

    Se `mover_para_id` for informado, os lançamentos dela são movidos para
    essa outra categoria antes da exclusão. As duas operações acontecem na
    mesma transação: ou as duas dão certo, ou nenhuma acontece.
    """
    with conexao() as con:
        if mover_para_id is not None:
            tipos = con.execute(
                "SELECT id, tipo FROM categorias WHERE id IN (?, ?)",
                (categoria_id, mover_para_id),
            ).fetchall()
            if mover_para_id == categoria_id or len({t["tipo"] for t in tipos}) != 1 or len(tipos) != 2:
                raise ValueError("A categoria de destino deve ser outra, do mesmo tipo.")
            con.execute(
                "UPDATE lancamentos SET categoria_id = ? WHERE categoria_id = ?",
                (mover_para_id, categoria_id),
            )
        try:
            con.execute("DELETE FROM categorias WHERE id = ?", (categoria_id,))
        except sqlite3.IntegrityError:
            # ON DELETE RESTRICT: o banco recusa apagar categoria com lançamentos.
            raise ValueError("Essa categoria ainda tem lançamentos. Mova-os antes de excluir.")


# ---------------------------------------------------------------------------
# Lançamentos
# ---------------------------------------------------------------------------

def inserir_lancamento(data_iso: str, descricao: str, valor_centavos: int, categoria_id: int) -> None:
    with conexao() as con:
        con.execute(
            """INSERT INTO lancamentos (data, descricao, valor_centavos, categoria_id)
               VALUES (?, ?, ?, ?)""",
            (data_iso, descricao.strip(), valor_centavos, categoria_id),
        )


def atualizar_lancamento(lancamento_id: int, data_iso: str, descricao: str,
                         valor_centavos: int, categoria_id: int) -> None:
    with conexao() as con:
        con.execute(
            """UPDATE lancamentos
               SET data = ?, descricao = ?, valor_centavos = ?, categoria_id = ?
               WHERE id = ?""",
            (data_iso, descricao.strip(), valor_centavos, categoria_id, lancamento_id),
        )


def excluir_lancamento(lancamento_id: int) -> None:
    with conexao() as con:
        con.execute("DELETE FROM lancamentos WHERE id = ?", (lancamento_id,))


def listar_lancamentos(ano: int | None = None, mes: int | None = None) -> list[dict]:
    """
    Lista lançamentos (mais recentes primeiro), já com o nome e o tipo da
    categoria. Sem `ano`, lista tudo; com `ano` e sem `mes`, o ano inteiro.
    """
    sql = """
        SELECT l.id, l.data, l.descricao, l.valor_centavos, l.categoria_id,
               c.nome AS categoria, c.tipo
        FROM lancamentos l
        JOIN categorias c ON c.id = l.categoria_id
    """
    params: list = []
    if ano is not None:
        sql += " WHERE l.data BETWEEN ? AND ?"
        params.extend(_intervalo(ano, mes))
    sql += " ORDER BY l.data DESC, l.id DESC"
    with conexao() as con:
        return _para_dicts(con.execute(sql, params))


# ---------------------------------------------------------------------------
# Relatórios (somas)
# ---------------------------------------------------------------------------

def totais_periodo(ano: int, mes: int | None = None) -> dict:
    """Devolve {'receita': centavos, 'despesa': centavos} do mês ou do ano."""
    with conexao() as con:
        linhas = con.execute(
            """SELECT c.tipo, SUM(l.valor_centavos) AS total
               FROM lancamentos l JOIN categorias c ON c.id = l.categoria_id
               WHERE l.data BETWEEN ? AND ?
               GROUP BY c.tipo""",
            _intervalo(ano, mes),
        ).fetchall()
    totais = {"receita": 0, "despesa": 0}
    for linha in linhas:
        totais[linha["tipo"]] = linha["total"]
    return totais


def total_por_categoria(tipo: str, ano: int, mes: int | None = None) -> list[dict]:
    """Soma por categoria de um tipo, do maior para o menor: [{'categoria', 'total'}]."""
    with conexao() as con:
        return _para_dicts(con.execute(
            """SELECT c.nome AS categoria, SUM(l.valor_centavos) AS total
               FROM lancamentos l JOIN categorias c ON c.id = l.categoria_id
               WHERE c.tipo = ? AND l.data BETWEEN ? AND ?
               GROUP BY c.id
               ORDER BY total DESC""",
            (tipo, *_intervalo(ano, mes)),
        ))


def totais_mensais(ano: int) -> list[dict]:
    """
    Receitas e despesas de cada mês do ano. Sempre devolve os 12 meses
    (meses sem lançamentos aparecem com zero).
    """
    meses = {m: {"mes": m, "receita": 0, "despesa": 0} for m in range(1, 13)}
    with conexao() as con:
        linhas = con.execute(
            """SELECT CAST(substr(l.data, 6, 2) AS INTEGER) AS mes,
                      c.tipo, SUM(l.valor_centavos) AS total
               FROM lancamentos l JOIN categorias c ON c.id = l.categoria_id
               WHERE l.data BETWEEN ? AND ?
               GROUP BY mes, c.tipo""",
            _intervalo(ano),
        ).fetchall()
    for linha in linhas:
        meses[linha["mes"]][linha["tipo"]] = linha["total"]
    return list(meses.values())


def anos_com_lancamentos() -> list[int]:
    """Anos que têm pelo menos um lançamento, do mais recente ao mais antigo."""
    with conexao() as con:
        linhas = con.execute(
            "SELECT DISTINCT CAST(substr(data, 1, 4) AS INTEGER) AS ano "
            "FROM lancamentos ORDER BY ano DESC"
        ).fetchall()
    return [linha["ano"] for linha in linhas]
