GEMINI = "google_genai"


def qualified_model_name(model: str) -> str:
    if ":" not in model and model.startswith("gemini-"):
        return f"{GEMINI}:{model}"
    return model


def is_gemini(qualified_model: str) -> bool:
    return qualified_model.startswith(f"{GEMINI}:")
