# Multi-stage build para otimização de produção
FROM python:3.11-slim as builder

# Instalar dependências de build
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Criar ambiente virtual
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copiar e instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Estágio de produção
FROM python:3.11-slim as production

# Criar usuário não-root para segurança
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Instalar apenas dependências de runtime
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copiar ambiente virtual do estágio builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Definir diretório de trabalho
WORKDIR /app

# Copiar código da aplicação
COPY --chown=appuser:appuser . .

# Criar diretório para dados
RUN mkdir -p data && chown -R appuser:appuser /app

# Mudar para usuário não-root
USER appuser

# Configurar variáveis de ambiente para produção
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/', timeout=5)" || exit 1

# Expor porta da aplicação
EXPOSE 5000

# Comando para executar a aplicação
CMD ["python", "app.py"]