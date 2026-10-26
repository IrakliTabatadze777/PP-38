import os

API_URL = os.environ.get("SUPPORT_API_URL", "http://localhost:8000").rstrip("/")
STREAM_TIMEOUT = float(os.environ.get("SUPPORT_STREAM_TIMEOUT", "120"))
REQUEST_TIMEOUT = float(os.environ.get("SUPPORT_REQUEST_TIMEOUT", "120"))
THREAD_POLL_SECONDS = 3
QUEUE_POLL_SECONDS = 5
