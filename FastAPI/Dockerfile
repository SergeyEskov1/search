FROM python:3.9-slim

WORKDIR /app

# Установка зависимостей для PostgreSQL
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "sleep 5 && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"]