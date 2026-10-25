<div align="center">

# 📦 ERP de Gestão de Estoque & Auditoria

**API REST de alta integridade transacional, rastreabilidade física de estoque e auditoria com soft delete.**

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Pytest](https://img.shields.io/badge/Pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)
![Coverage](https://img.shields.io/badge/Coverage-80%25%2B-brightgreen?style=for-the-badge)

</div>

---

## 🧭 Visão Geral

Backend desenvolvido para atender operações de controle de estoque com rigor contábil e auditoria completa. A arquitetura foi projetada para mitigar concorrência destrutiva, garantir integridade referencial antes de qualquer desativação lógica e manter o registro de quem executou cada ação no sistema.

> [!IMPORTANT]
> **Concorrência Atômica:** Operações de saída, perda e ajuste físico de estoque utilizam lock pessimista no banco de dados (`SELECT ... FOR UPDATE`), eliminando cenários de *race condition* e vendas a descoberto.

---

## 🛠️ Stack Tecnológica

| Componente | Tecnologia | Finalidade |
| :--- | :--- | :--- |
| **Linguagem** | Python 3.12 | Base da aplicação |
| **Framework Web** | FastAPI | Roteamento assíncrono e documentação OpenAPI nativa |
| **ORM / Banco** | SQLAlchemy & PostgreSQL | Persistência relacional com constraints e partial indexes |
| **Migrações** | Alembic | Versionamento do schema |
| **Segurança** | OAuth2 Bearer, JWT, Passlib (Bcrypt) | Autenticação, rotação com refresh tokens e hashing seguro |
| **Testes** | Pytest, Pytest-Cov | Testes de integração, concorrência e auditoria |
| **Containerização** | Docker & Docker Compose | Ambientes efêmeros e reprodutibilidade imediata |

---

## 🏛️ Regras de Negócio e Decisões de Arquitetura

<details>
<summary><b>1. Rastreabilidade e Auditoria (Soft Delete)</b></summary>

* Nenhuma entidade crítica (`Product`, `Category`, `Supplier`, `User`) é excluída fisicamente do banco de dados.
* Campos auditáveis: `created_by`, `created_at`, `updated_by`, `updated_at`, `deleted_by` e `deleted_at`.
* **Partial Indexes:** Unicidade de regras de negócio (como `SKU`, `CNPJ` e `E-mail`) é restrita a registros ativos (`WHERE deleted_at IS NULL`), viabilizando reaproveitamento de códigos após exclusão lógica.
</details>

<details>
<summary><b>2. Travas Relacionais de Exclusão</b></summary>

* **Produtos:** Bloqueio estrito de desativação enquanto houver saldo físico positivo (`stock_quantity > 0`).
* **Categorias e Fornecedores:** Bloqueio estrito de desativação se houver qualquer produto ativo associado.
* **Restauração Segura:** Um produto só pode ser restaurado se sua categoria e seu fornecedor vinculados estiverem ativos.
</details>

<details>
<summary><b>3. Padronização de Contratos HTTP</b></summary>

Todas as respostas de sucesso utilizam um envelope uniforme:

```json
{
  "success": true,
  "message": "Operação realizada com sucesso.",
  "data": { ... },
  "timestamp": "2026-10-25T15:30:00Z"
}
```

Erros de negócio e validações de esquema retornam status HTTP semânticos (400, 401, 404, 409, 422) acompanhados do identificador estruturado `error_code`.
</details>

---

## ⚡ Como Executar o Projeto

Escolha abaixo a forma mais conveniente para inicializar a aplicação no seu ambiente:

<details open>
<summary><b>🐳 Opção 1: Via Docker & Docker Compose (Recomendado — Zero Setup)</b></summary>
<br>

Esta abordagem configura automaticamente a API FastAPI, o PostgreSQL e executa as migrações sem a necessidade de instalar Python ou banco de dados localmente.

> [!TIP]
> **Pré-requisito único:** Ter o [Docker](https://www.docker.com/) e o Docker Compose instalados e em execução.

#### 1. Clonar o repositório e acessar a pasta raiz:
```bash
git clone <URL_DO_REPOSITORIO>
cd <NOME_DA_PASTA>
```

#### 2. Configurar variáveis de ambiente:
```bash
cp .env.example .env
```

#### 3. Construir e inicializar os containers:
```bash
docker compose up --build -d
```

> [!NOTE]
> O container da API aguarda o PostgreSQL atingir o estado `healthy` antes de subir e aplica automaticamente as migrações do banco (`alembic upgrade head`).

#### Status dos Serviços:
| Serviço | Endpoint Local | Descrição |
| :--- | :--- | :--- |
| **FastAPI Backend** | `http://localhost:8000` | Servidor da aplicação |
| **Documentação Swagger** | `http://localhost:8000/docs` | Interface OpenAPI interativa |
| **PostgreSQL Database** | `localhost:5432` | Instância persistente do banco |

Para acompanhar os logs da API em tempo real:
```bash
docker compose logs -f api
```

Para desligar o ambiente:
```bash
docker compose down
```

</details>

<details>
<summary><b>💻 Opção 2: Execução Local Tradicional (Sem Docker)</b></summary>
<br>

Indicado para desenvolvimento direto ou depuração da aplicação.

> [!TIP]
> **Pré-requisitos:** Python 3.11+ e uma instância ativa do PostgreSQL rodando localmente.

#### 1. Clonar o repositório e criar o ambiente virtual:
```bash
git clone <URL_DO_REPOSITORIO>
cd <NOME_DA_PASTA>

# Criar ambiente virtual
python -m venv venv
```

#### 2. Ativar o ambiente virtual:
* **Linux / macOS:**
  ```bash
  source venv/bin/activate
  ```
* **Windows (PowerShell):**
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
* **Windows (CMD):**
  ```cmd
  .\venv\Scripts\activate.bat
  ```

#### 3. Instalar as dependências:
```bash
pip install -r requirements.txt
```

#### 4. Configurar variáveis de ambiente:
```bash
cp .env.example .env
```
*Abra o `.env` e confirme a string de conexão `DATABASE_URL` apontando para o seu PostgreSQL local.*

#### 5. Executar as migrações do banco de dados:
```bash
alembic upgrade head
```

#### 6. Inicializar o servidor Uvicorn:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

</details>

---

## 📖 Documentação Interativa da API

Com a aplicação rodando, acesse no navegador para visualizar e testar os contratos com exemplos pré-carregados:

* **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧪 Suíte de Testes Automatizados e Cobertura

Os testes executam contra SQLite transacional em memória (`StaticPool`), permitindo validação ágil, isolamento entre execuções e independência de banco externo.

Para executar toda a suíte de testes e calcular a cobertura:

```bash
pytest
```

### Visualizar o relatório de cobertura em HTML:

O Pytest gerará a pasta interativa `htmlcov/`:

* **Linux:**
  ```bash
  xdg-open htmlcov/index.html
  ```
* **Windows:**
  ```cmd
  start htmlcov/index.html
  ```

---

## 📁 Estrutura do Projeto

```text
├── alembic/                  # Histórico e scripts de versionamento do banco
├── app/
│   ├── dependencies.py       # Injeções de dependência (banco, JWT, admin guard)
│   ├── error_handlers.py     # Handlers globais de interceptação de erros HTTP
│   ├── exceptions.py         # Hierarquia de exceções de domínio
│   ├── main.py               # Inicialização da aplicação FastAPI e routers
│   ├── models.py             # Modelos SQLAlchemy e mapeamentos relacionais
│   ├── schemas.py            # Schemas Pydantic V2 (validação e serialização)
│   ├── security.py           # Utilitários criptográficos (Bcrypt e JWT)
│   └── routers/              # Endpoints modularizados por domínio
│       ├── auth_routes.py
│       ├── category_routes.py
│       ├── product_routes.py
│       ├── stock_movements_routes.py
│       ├── supplier_routes.py
│       └── user_routes.py
├── tests/                    # Suíte completa de testes automatizados com Pytest
├── .env.example              # Modelo das variáveis de ambiente necessárias
├── docker-compose.yml        # Orquestração da API e do banco PostgreSQL
├── Dockerfile                # Configuração da imagem de container
├── pytest.ini                # Configurações do runner de testes e coverage
├── requirements.txt          # Dependências travadas do projeto
└── README.md                 # Documentação técnica do projeto
```