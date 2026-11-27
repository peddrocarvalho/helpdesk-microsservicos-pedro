FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN useradd --uid 10003 --no-create-home chamados \
    && mkdir -p /dados \
    && chown -R chamados:chamados /app /dados

USER chamados

ENV DATABASE_URL=sqlite:////dados/chamados.db

EXPOSE 8003

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
