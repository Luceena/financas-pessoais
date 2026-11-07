# Finanças Pessoais

Gerenciador de finanças pessoais simples, para rodar localmente.
Feito com **Python 3 + Streamlit + SQLite**.

## Funcionalidades

- **Painel do mês:** total de receitas, despesas e saldo do mês escolhido.
- **Lançamentos:** cadastrar, listar, editar e excluir receitas e despesas; exportar para CSV.
- **Categorias:** criar, renomear e excluir. Se a categoria tiver lançamentos, eles são movidos para outra do mesmo tipo antes da exclusão.
- **Análise:** ranking e gráfico das categorias onde você mais gasta e das que mais trazem dinheiro, no mês e no ano.
- **Evolução:** gráfico de receitas x despesas mês a mês.

## Instalação (Ubuntu)

Precisa do Python 3 e do módulo de ambientes virtuais:

```bash
sudo apt install python3 python3-venv
```

## Como rodar

```bash
./run.sh
```

Na primeira vez, o script cria o ambiente virtual `venv/` e instala as dependências. Depois, abre o app no navegador em <http://localhost:8501>. Para fechar, aperte `Ctrl+C` no terminal.

Se preferir fazer à mão:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

O banco `financas.db` é criado sozinho na primeira execução, já com as categorias padrão.

## Estrutura

```
app.py              Ponto de entrada: menu lateral e escolha da página
db.py               Todo o acesso ao SQLite (as páginas nunca escrevem SQL)
formatos.py         Conversões: R$ <-> centavos, datas ISO <-> dd/mm/aaaa
paginas/
  comum.py          Seletor de mês/ano, cores e avisos usados em várias páginas
  painel.py         Painel do mês
  lancamentos.py    Cadastro, lista, edição, exclusão e exportação CSV
  categorias.py     Gestão de categorias
  analise.py        Ranking por categoria
  evolucao.py       Receitas x despesas mês a mês
.streamlit/
  config.toml       Deixa o app acessível só pelo seu computador
```

## Decisões de projeto

- **Valores em centavos (inteiros).** R$ 12,34 é guardado como `1234`. Assim não há erros de arredondamento de `float`.
- **O tipo vem da categoria.** Um lançamento é receita ou despesa conforme a categoria escolhida.
- **Datas em ISO (`AAAA-MM-DD`) no banco.** Nesse formato, a ordem alfabética é igual à ordem cronológica, o que simplifica os filtros. Na tela, as datas aparecem como dd/mm/aaaa.
- **`PRAGMA foreign_keys = ON` em toda conexão.** O SQLite vem com as chaves estrangeiras desligadas. É isso que faz o `ON DELETE RESTRICT` impedir a exclusão de uma categoria que ainda tem lançamentos.

## CSV exportado

Separador `;`, vírgula decimal e codificação UTF-8 com BOM. O LibreOffice Calc e o Excel em português abrem o arquivo direto, com os valores reconhecidos como números.

## Backup

Seus dados ficam todos no arquivo `financas.db`. Para fazer backup, basta copiá-lo. Ele **não** vai para o Git (está no `.gitignore`).
