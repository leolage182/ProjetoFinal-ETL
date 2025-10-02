FROM python:3.11-slim

WORKDIR /app

# instalar dependências de sistema (tempo de build maior)
RUN apt-get update && apt-get install -y build-essential libpq-dev --no-install-recommends && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY etl_com_postgres.py .

# comando padrão (pode ser sobrescrito no docker run)
CMD ["python", "etl_com_postgres.py"]