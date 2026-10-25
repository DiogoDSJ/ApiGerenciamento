FROM python:3.12-slim

# Evita que o Python gere arquivos .pyc e força flush imediato dos prints nos logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instala dependências de compilação essenciais para libs C (ex: compilações de adapters Postgres)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala as dependências antes do código para aproveitar o cache de camadas do Docker
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação e arquivos de migração
COPY ./app ./app
COPY ./alembic ./alembic
COPY ./alembic.ini .

# Porta padrão de execução do Uvicorn
EXPOSE 8000

# Executa migrações do banco com Alembic antes de inicializar o servidor HTTP
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]