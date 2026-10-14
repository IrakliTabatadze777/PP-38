from typing import Any

from dotenv import load_dotenv
from langsmith import Client, traceable
from langsmith.anonymizer import create_anonymizer

load_dotenv()


def safe_inputs(inputs: dict) -> dict:
    return {"question_length": len(inputs.get("question", ""))}


def safe_outputs(output: Any) -> dict:
    return {"answer_length": len(str(output))}


@traceable(process_inputs=safe_inputs, process_outputs=safe_outputs)
def private_step(question: str) -> str:
    return "Your booking for Anna Smith is confirmed."


anonymizer = create_anonymizer([
    {"pattern": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "replace": "<email>"},
    {"pattern": r"\+?\d[\d\s-]{8,}\d", "replace": "<phone>"},
])

safe_client = Client(anonymizer=anonymizer)


@traceable(client=safe_client)
def ask_with_contact(text: str) -> str:
    return f"We will call you back: {text}"


if __name__ == "__main__":
    private_step(question="My name is Anna Smith, book a hotel in Batumi.")
    ask_with_contact("Reach me at anna@example.com or +995 555 123 456")
    safe_client.flush()
