from fastapi import FastAPI, Depends, Request, HTTPException, status
from agent import build_supervisor_graph
from contextlib import asynccontextmanager
from schemas import ChatRequest, ChatResponse
from langgraph.errors import GraphRecursionError
import asyncio


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.graph = build_supervisor_graph()
    yield


app = FastAPI(lifespan=lifespan)


def get_graph(request: Request):
    graph = request.app.state.graph
    return graph

def new_request_input(message: str):
    return {
        'user_request': message,
        'next_agent': '',
        'reasoning': '',
        'completed_agents': [],
        'tool_agent_result': '',
        'plan_agent_result': {},
        'final_note': '',
    }

def format_answer(values: dict):
    parts = []

    if values['tool_agent_result']:
        parts.append(values['tool_agent_result'])

    if values['plan_agent_result']:
        plan = values['plan_agent_result']
        plan_agent_str = (f'Plan agent result for {plan['destination']}'
                          f'Duration Days: {plan["duration_days"]}'
                          f'Daily Budget: {plan["daily_budget_usd"]}'
                          f'Packing List: {", ".join(plan["packing_list"])}')

        parts.append(plan_agent_str)


    final_answer = '\n\n'.join(parts) or values['reasoning']
    return final_answer


def to_http_error(e: Exception):
    if isinstance(e, GraphRecursionError):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail='The agent exceed recursion limit')

    if isinstance(e, TimeoutError):
        return HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail='The agent took longer that 30 second')

    return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail='Agent failed, Please try again later')


@app.post('/chat', response_model=ChatResponse)
async def chat(body: ChatRequest, graph=Depends(get_graph)):

    try:
        new_state = new_request_input(body.message)

        async with asyncio.timeout(30):
            result = await graph.ainvoke(new_state)

        formatted_answer = format_answer(result)

    except Exception as e:
        raise to_http_error(e)

    return ChatResponse(answer=formatted_answer)