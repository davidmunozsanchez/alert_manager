FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de configuración
COPY pyproject.toml ./

# Instalar Poetry
RUN pip install --no-cache-dir poetry==1.7.1

# Configurar Poetry para no crear virtualenv
RUN poetry config virtualenvs.create false

# Instalar dependencias del proyecto
RUN poetry install --no-interaction --no-ansi --no-root

# Copiar código fuente
COPY src/ ./src/

# Configurar PYTHONPATH
ENV PYTHONPATH=/app/src

# Exponer puerto
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/alerts/health || exit 1

# Comando por defecto
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
