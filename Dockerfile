# Dockerfile (Kapitel 15.2)
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "EngineAI_IPO_Starter.py", "--check"]
