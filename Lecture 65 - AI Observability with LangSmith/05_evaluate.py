import asyncio
import uuid

from langgraph.checkpoint.memory import InMemorySaver
from langsmith import aevaluate
from pydantic import BaseModel, Field

from trip_agent import SUPERVISOR_PROMPT, build_supervisor_graph, initial_state, make_model

DATASET = "trip-supervisor-v1"


def answer_text(values: dict) -> str:
    parts = [values["general_agent_result"], values["tool_agent_result"]]
    plan = values["plan_agent_result"]
    if plan:
        parts.append(
            f"Plan: {plan['destination']}, {plan['duration_days']} days, "
            f"${plan['daily_budget_usd']:.0f}/day. Packing: {', '.join(plan['packing_list'])}"
        )
    return "\n".join(p for p in parts if p)


def make_target(supervisor_prompt: str = SUPERVISOR_PROMPT):
    graph = build_supervisor_graph(InMemorySaver())

    async def target(inputs: dict) -> dict:
        config = {"configurable": {"thread_id": str(uuid.uuid4())}, "recursion_limit": 15}
        values = await graph.ainvoke(initial_state(inputs["question"]), config)
        return {"answer": answer_text(values), "agents_called": values["completed_agents"]}

    return target


def agents_correct(outputs: dict, reference_outputs: dict) -> dict:
    expected = sorted(reference_outputs["expected_agents"])
    actual = sorted(set(outputs["agents_called"]))
    return {"key": "agents_correct", "score": int(expected == actual)}


def concise(outputs: dict) -> dict:
    words = len(outputs["answer"].split())
    return {"key": "under_120_words", "score": int(words <= 120), "comment": f"{words} words"}


class Verdict(BaseModel):
    score: int = Field(description="Integer from 1 (bad) to 5 (excellent)")
    reasoning: str = Field(description="One or two sentences justifying the score")


judge = make_model().with_structured_output(Verdict)

JUDGE_PROMPT = """You are grading a trip assistant's answer.

User question: {question}
Assistant answer: {answer}
Agents that acted: {agents}

Score 1-5 for helpfulness and factual caution:
- 5: directly answers the question, uses units for any temperature, no invented facts.
- 3: partially answers or leaves out important details.
- 1: wrong, misleading, or ignores the question.
"""


async def helpfulness(inputs: dict, outputs: dict) -> dict:
    verdict = await judge.ainvoke(
        JUDGE_PROMPT.format(
            question=inputs["question"],
            answer=outputs["answer"],
            agents=outputs["agents_called"],
        )
    )
    return {"key": "helpfulness", "score": verdict.score / 5, "comment": verdict.reasoning}


PROMPT_V2 = SUPERVISOR_PROMPT + (
    "\n\nRules: weather and sightseeing questions always go to tool_agent. "
    "Plan, budget and packing list requests always go to plan_agent. "
    "Everything else goes to general_agent."
)


async def main() -> None:
    await aevaluate(
        make_target(),
        data=DATASET,
        evaluators=[agents_correct, concise, helpfulness],
        experiment_prefix="baseline",
        max_concurrency=2,
        metadata={"model": "gemini-3.6-flash", "prompt_version": "v1"},
    )

    await aevaluate(
        make_target(PROMPT_V2),
        data=DATASET,
        evaluators=[agents_correct, concise, helpfulness],
        experiment_prefix="stricter-routing",
        max_concurrency=2,
        metadata={"model": "gemini-3.6-flash", "prompt_version": "v2"},
    )


if __name__ == "__main__":
    asyncio.run(main())
