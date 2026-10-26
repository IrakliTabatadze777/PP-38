FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /ui

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py client.py config.py ui.py ./
COPY views ./views

RUN useradd --create-home appuser
USER appuser

EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
