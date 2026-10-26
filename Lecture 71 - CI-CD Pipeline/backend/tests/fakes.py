import hashlib
import json
import math
import re
import uuid
from collections.abc import Callable
from typing import Any

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import Field

DIMENSIONS = 256


class HashEmbeddings(Embeddings):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        vector = [0.0] * DIMENSIONS
        for word in re.findall(r"[a-z0-9]+", text.lower()):
            digest = hashlib.md5(word.encode()).digest()
            vector[int.from_bytes(digest[:4]) % DIMENSIONS] += 1.0
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]


Step = AIMessage | Callable[[list[BaseMessage]], AIMessage]


def tool_call(name: str, **args: Any) -> dict[str, Any]:
    return {"name": name, "args": args, "id": f"call_{uuid.uuid4().hex[:8]}", "type": "tool_call"}


def ai(content: str = "", *calls: dict[str, Any]) -> AIMessage:
    return AIMessage(content=content, tool_calls=list(calls))


def last_tool_result(messages: list[BaseMessage]) -> Any:
    tool_messages = [m for m in messages if isinstance(m, ToolMessage)]
    return json.loads(tool_messages[-1].text)


class ScriptedChatModel(BaseChatModel):
    steps: list[Any]
    then: Any = None
    seen: list[list[BaseMessage]] = Field(default_factory=list)

    @property
    def _llm_type(self) -> str:
        return "scripted"

    def bind_tools(self, tools: Any, **_: Any) -> ScriptedChatModel:
        return self

    def _generate(self, messages: list[BaseMessage], *_: Any, **__: Any) -> ChatResult:
        index = len(self.seen)
        self.seen.append(list(messages))
        if index < len(self.steps):
            step = self.steps[index]
        elif self.then is not None:
            step = self.then
        else:
            raise AssertionError(f"The script ran out: model call #{index + 1}")
        reply = step(messages) if callable(step) else step
        return ChatResult(generations=[ChatGeneration(message=reply.model_copy())])

    @property
    def calls(self) -> int:
        return len(self.seen)
