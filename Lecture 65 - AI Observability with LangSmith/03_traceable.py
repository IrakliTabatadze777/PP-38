import asyncio
import uuid

import langsmith as ls
from google import genai
from langchain_core.tracers.langchain import wait_for_all_tracers
from langgraph.checkpoint.memory import MemorySaver
from langsmith import traceable

from trip_agent import build_supervisor_graph, initial_state, make_model

graph = build_supervisor_graph(MemorySaver())


@traceable
def clean_question(text: str) -> str:
    return " ".join(text.split()).strip()


@traceable(name="Trip Pipeline")
async def answer_trip_question(text: str) -> str:
    question = clean_question(text)
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    result = await graph.ainvoke(initial_state(question), config)
    return result["general_agent_result"] or result["tool_agent_result"] or "(a plan is waiting for approval)"


genai_client = genai.Client()


@traceable(
    run_type="llm",
    name="gemini_raw",
    metadata={"ls_provider": "google", "ls_model_name": "gemini-3.6-flash"},
)
def call_gemini(prompt: str) -> dict:
    response = genai_client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
    )
    usage = response.usage_metadata
    return {
        "content": response.text,
        "usage_metadata": {
            "input_tokens": usage.prompt_token_count,
            "output_tokens": usage.candidates_token_count,
            "total_tokens": usage.total_token_count,
        },
    }


DOCS = [
    "Prometheus Cave near Kutaisi is open 10:00-18:00 and closed on Mondays.",
    "Sulphur Baths in Tbilisi offer private rooms, booking recommended.",
    "Batumi Botanical Garden is best visited in spring when the azaleas bloom.",
]


@traceable(run_type="retriever", name="search_travel_notes")
def search_notes(query: str) -> list[dict]:
    words = set(query.lower().split())
    scored = [(len(words & set(doc.lower().split())), doc) for doc in DOCS]
    top = [doc for score, doc in sorted(scored, reverse=True)[:2] if score > 0]
    return [{"page_content": doc, "type": "Document", "metadata": {"source": "notes"}} for doc in top]


@traceable(name="Trip RAG")
def answer_with_notes(question: str) -> str:
    docs = search_notes(question)
    context = "\n".join(d["page_content"] for d in docs)
    reply = make_model().invoke(f"Answer using only this context:\n{context}\n\nQuestion: {question}")
    return reply.text


@traceable(tags=["rag"], metadata={"component": "retrieval"})
def retrieve(query: str) -> list[str]:
    return [d["page_content"] for d in search_notes(query)]


@traceable(name="Trip Pipeline v2")
def pipeline(question: str) -> str:
    run = ls.get_current_run_tree()
    if run:
        run.metadata["question_length"] = len(question)
        if len(question) > 200:
            run.tags.append("long-question")
    return answer_with_notes(question)


async def main() -> None:
    print(await answer_trip_question("  What   is the weather   in Rome?  "))
    print(call_gemini("Name one dish from Imereti.")["content"])
    print(answer_with_notes("When is Prometheus Cave open?"))
    print(retrieve("Sulphur Baths"))

    answer_with_notes(
        "When is Prometheus Cave open?",
        langsmith_extra={"tags": ["from-mobile"], "metadata": {"user_id": "u-42"}},
    )

    with ls.tracing_context(metadata={"experiment": "prompt-b"}):
        pipeline("When is Prometheus Cave open?")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        wait_for_all_tracers()
