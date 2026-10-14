import asyncio
import uuid

from langchain_core.tracers.langchain import wait_for_all_tracers
from langgraph.checkpoint.memory import MemorySaver

from trip_agent import build_supervisor_graph, initial_state

graph = build_supervisor_graph(MemorySaver())

HEAT_QUESTION = "I'm visiting Tbilisi tomorrow. Should I pack for the heat?"


def make_config(**extra) -> dict:
    return {
        "configurable": {"thread_id": str(uuid.uuid4())},
        "recursion_limit": 15,
        "run_name": "trip_chat",
        **extra,
    }


async def heat_question() -> None:
    tags = ["lecture-demo"]
    config = make_config(tags=tags, metadata={"app_version": "0.1.0"})
    result = await graph.ainvoke(initial_state(HEAT_QUESTION), config)
    print(result["tool_agent_result"])


async def two_things_in_one_question() -> None:
    config = make_config(tags=["lecture-demo", "two-tools"])
    result = await graph.ainvoke(initial_state("I have one day in Rome. What's the weather and what should I see?"), config)
    print(result["tool_agent_result"])


async def pause_and_resume() -> None:
    config = make_config(tags=["lecture-demo", "hitl"])
    await graph.ainvoke(initial_state("Plan a 5-day trip to Rome with a budget."), config)
    snapshot = await graph.aget_state(config)
    print("Paused before:", snapshot.next)

    config["run_name"] = "trip_approve"
    result = await graph.ainvoke(None, config)
    print(result["final_note"])


async def conversation_as_thread() -> None:
    config = make_config(tags=["lecture-demo", "thread"])
    for question in ["What is the weather in Tbilisi?", "What are the main sights in Tbilisi?"]:
        result = await graph.ainvoke(initial_state(question), config)
        print(result["tool_agent_result"])


async def main() -> None:
    await heat_question()
    await two_things_in_one_question()
    await pause_and_resume()
    await conversation_as_thread()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        wait_for_all_tracers()
