📦 API DE GERENCIAMENTO DE PRODUTOS

API REST robusta desenvolvida em FastAPI, SQLAlchemy ORM e PostgreSQL, com foco em integridade transacional, rastreabilidade de estoque com auditoria completa (soft delete) e controle rigoroso de concorrência com bloqueio pessimista.

🚀 Tecnologias Utilizadas

Backend: Python 3.12, FastAPI

Banco de Dados & ORM: PostgreSQL, SQLAlchemy

Migrações: Alembic

Autenticação & Criptografia: JWT (OAuth2 Bearer com Refresh Token), Passlib (Bcrypt)

Testes & Cobertura: Pytest, Pytest-Cov (com banco isolado em memória)

Containerização: Docker e Docker Compose

📐 Decisões de Arquitetura e Regras de Negócio

Controle Estrito de Concorrência (Lock Pessimista):

As movimentações de estoque utilizam with_for_update() no PostgreSQL, garantindo que requisições concorrentes não vendam itens além do saldo disponível (race condition).

Auditoria e Soft Delete:

Produtos, fornecedores, categorias e usuários possuem histórico de quem criou (created_by), editou (updated_by) e desativou (deleted_by).

Índices parciais garantem unicidade (SKU, CNPJ, e-mail, nomes) apenas entre itens ativos.

Travas de Integridade Relacional:

Produtos: Não podem ser excluídos caso ainda tenham saldo em estoque.

Categorias e Fornecedores: Não podem ser excluídos se houver produtos ativos associados.

Restauração: Um produto desativado só pode ser reativado se sua categoria e seu fornecedor estiverem ativos.

Padronização de Contratos e Exceções:

Respostas de sucesso envelopadas com APIResponse[T].

Exceções de domínio mapeadas para códigos HTTP semânticos (400, 401, 404, 409, 422).

⚙️ Como Executar o Projeto

Escolha uma das duas opções abaixo para rodar o projeto no seu computador:

Opção 1: Executando via Docker (Recomendado)

Esta opção inicializa a API e o banco de dados PostgreSQL automaticamente sem a necessidade de instalar Python ou Postgres na sua máquina.

Pré-requisitos:

Docker e Docker Compose instalados.

Passo a passo:

Clone o repositório e acesse a pasta raiz:

git clone <URL_DO_REPOSITORIO>
cd <NOME_DA_PASTA>


Crie o arquivo de variáveis de ambiente com base no exemplo:

cp .env.example .env


Suba os containers da aplicação:

docker compose up --build -d


A API estará disponível em: http://localhost:8000

Opção 2: Executando Localmente (Sem Docker)

Pré-requisitos:

Python 3.11+ instalado

PostgreSQL rodando localmente

Passo a passo:

Clone o repositório e crie o ambiente virtual:

python -m venv venv


Ative o ambiente virtual:

Linux / macOS:

source venv/bin/activate


Windows:

.\venv\Scripts\activate


Instale as dependências:

pip install -r requirements.txt


Configure o arquivo .env:

cp .env.example .env


Abra o .env e confirme a string de conexão DATABASE_URL apontando para o seu PostgreSQL local.

Execute as migrações do banco de dados:

alembic upgrade head


Inicie o servidor FastAPI:

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000


Acesse a API em: http://localhost:8000

📖 Documentação Interativa da API (Swagger / OpenAPI)

Com o servidor rodando, abra no navegador para testar os endpoints interativamente:

Swagger UI: http://localhost:8000/docs

ReDoc: http://localhost:8000/redoc

🧪 Como Rodar os Testes Automatizados

A suíte de testes utiliza pytest com banco SQLite transacional em memória, garantindo isolamento total e rapidez sem afetar o banco principal.

Para rodar todos os testes com a medição de cobertura de código no terminal e gerar o relatório gráfico:

pytest


Visualizar o relatório de cobertura detalhado (HTML):

Após rodar o comando acima, uma pasta htmlcov/ será gerada:

Linux:

xdg-open htmlcov/index.html


Windows:

start htmlcov/index.html


📁 Estrutura de Pastas

.
├── alembic/                  # Histórico e scripts de migrações do banco
├── app/
│   ├── dependencies.py       # Injeções de dependência (JWT, Sessão DB, Admin check)
│   ├── error_handlers.py     # Handlers globais de exceções da API
│   ├── exceptions.py         # Hierarquia de exceções de domínio
│   ├── main.py               # Inicialização da aplicação FastAPI e routers
│   ├── models.py             # Modelos SQLAlchemy e mapeamentos relacionais
│   ├── schemas.py            # Schemas Pydantic (validação e serialização)
│   ├── security.py           # Funções de hashing (Bcrypt) e JWT
│   └── routers/              # Endpoints desacoplados por módulo
│       ├── auth_routes.py
│       ├── category_routes.py
│       ├── product_routes.py
│       ├── stock_movements_routes.py
│       ├── supplier_routes.py
│       └── user_routes.py
├── tests/                    # Suíte completa de testes automatizados com Pytest
├── .env.example              # Exemplo de configuração de variáveis de ambiente
├── docker-compose.yml        # Orquestração do app e banco PostgreSQL
├── Dockerfile                # Imagem Docker da aplicação
├── pytest.ini                # Configurações do runner de testes e coverage
├── requirements.txt          # Dependências travadas do projeto
└── README.md                 # Documentação técnica do projeto
