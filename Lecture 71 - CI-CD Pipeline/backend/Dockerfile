FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY alembic.ini ./
COPY app ./app
COPY data ./data
COPY scripts ./scripts
COPY docker/entrypoint.sh ./docker/entrypoint.sh

RUN useradd --create-home appuser && chmod +x docker/entrypoint.sh
USER appuser

EXPOSE 8000
ENTRYPOINT ["docker/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
