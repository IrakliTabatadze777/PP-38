import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langgraph.checkpoint.memory import InMemorySaver

from app.graph.build import build_graph


class DrawingOnlyModel:
    def bind_tools(self, tools: object) -> DrawingOnlyModel:
        return self


def mermaid() -> str:
    graph = build_graph(
        model=DrawingOnlyModel(),
        session_factory=None,
        kb=None,
        checkpointer=InMemorySaver(),
        max_steps=8,
    )
    return graph.get_graph().draw_mermaid()


if __name__ == "__main__":
    print(mermaid())
