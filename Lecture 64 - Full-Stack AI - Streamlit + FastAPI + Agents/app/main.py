from fastapi import FastAPI, Request, Depends
from fastapi.responses import StreamingResponse
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.errors import GraphRecursionError
from contextlib import asynccontextmanager
from .config import settings
from .agent import build_supervisor_graph
from .sessions import describe, thread_config, apply_decision
from .schemas import ChatRequest, Decision
import json

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncPostgresSaver.from_conn_string(settings.DATABASE_URL) as checkpointer:
        await checkpointer.setup()
        app.state.graph = build_supervisor_graph(checkpointer)
        yield

app = FastAPI(lifespan=lifespan)


STREAM_HEADERS = {'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}

def get_graph(request: Request):
    graph = request.app.state.graph
    return graph


def sse(event: dict):
    return f'data: {json.dumps(event)}'

async def stream_run(graph, config, graph_input):
    try:
        async for update in graph.astream(graph_input, config, stream_mode='update'):
            for node_name in update:
                if not node_name.startswith('__'):
                    yield sse({'type': 'step', 'node': node_name})

        final = describe(await graph.aget_state(config))
        yield sse({'type': 'final', **final.model_dump()})

    except GraphRecursionError as e:
        yield sse({'type': 'error', 'detail': 'The agent could not finish within limit'})



def new_request_input(message: str):
    return {
        'user_request': message,
        'next_agent': '',
        'reasoning': '',
        'completed_agents': [],
        'tool_agent_result': '',
        'plan_agent_result': {},
        'general_agent_result': '',
        'final_note': '',
    }

@app.post('/chat/stream')
async def chat_stream(request: ChatRequest, graph=Depends(get_graph)):
    config = thread_config(request.session_id)
    return StreamingResponse(
        stream_run(graph, config, new_request_input(request.message)),
        media_type='text/event-stream',
        headers=STREAM_HEADERS
    )


@app.post('/approve/stream')
async def approve_stream(decision: Decision, graph=Depends(get_graph)):
    config = thread_config(decision.session_id)
    await apply_decision(graph, config, decision)
    return StreamingResponse(
        stream_run(graph, config, None),
        media_type='text/event-stream',
        headers=STREAM_HEADERS
    )