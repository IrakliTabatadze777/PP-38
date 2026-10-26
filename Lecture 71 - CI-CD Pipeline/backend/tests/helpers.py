import json

import httpx

JWT_SECRET = "test-secret-of-at-least-32-characters"
REVIEWER_EMAIL = "reviewer@example.com"
ADMIN_EMAIL = "admin@example.com"
OTHER_CUSTOMER_EMAIL = "sam@example.com"


def plain_url(sqlalchemy_url: str) -> str:
    return sqlalchemy_url.replace("postgresql+psycopg://", "postgresql://")


def parse_sse(body: str) -> list[tuple[str, dict]]:
    events = []
    for block in body.replace("\r\n", "\n").strip().split("\n\n"):
        fields = dict(line.split(": ", 1) for line in block.splitlines() if ": " in line)
        if "event" in fields:
            events.append((fields["event"], json.loads(fields["data"])))
    return events


async def chat(
    client: httpx.AsyncClient,
    message: str,
    thread_id: str | None = None,
):
    body = {"message": message}
    if thread_id:
        body["thread_id"] = thread_id
    response = await client.post("/chat", json=body)
    return response, parse_sse(response.text)
