FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN useradd --system --uid 10002 inventario \
    && mkdir -p /dados \
    && chown -R inventario:inventario /app /dados

ENV DATABASE_URL=sqlite:////dados/inventario.db
ENV PYTHONUNBUFFERED=1

USER inventario

EXPOSE 8002

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
