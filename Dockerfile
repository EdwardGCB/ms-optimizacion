FROM python:3.11-slim

WORKDIR /app
    
# Dependencias de Python con múltiples mirrors
COPY requirements.txt .
RUN pip install --no-cache-dir \
    --index-url https://pypi.org/simple \
    --extra-index-url https://pypi.python.org/simple \
    --trusted-host pypi.org \
    --trusted-host pypi.python.org \
    --trusted-host files.pythonhosted.org \
    -r requirements.txt

# Código de la aplicación
COPY . .

# Puerto (opcional, se puede sobreescribir)
ENV PORT=8000
EXPOSE 8000

# Ejecutar la app
CMD uvicorn --host 0.0.0.0 --port ${PORT:-8000} --factory config:create_app