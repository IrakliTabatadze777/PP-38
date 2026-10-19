FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1


WORKDIR /app

COPY requirements-ui.txt .
RUN pip install --no-cache-dir -r requirements-ui.txt


COPY ui.py .

CMD ["streamlit", "run", "ui.py", "--server.port=8501", "--server.address=0.0.0.0"]