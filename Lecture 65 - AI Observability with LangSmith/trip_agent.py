from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langchain_core.exceptions import OutputParserException
from langchain_core.tools import tool
from langchain_core.messages import ToolMessage, BaseMessage, HumanMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field, ValidationError
from typing import Literal, TypedDict, Annotated


load_dotenv()

SUPERVISOR_PROMPT = ('you are coordinating a trip-planning system with two specialist agent\n'
        '- tool_agent: handles weather and sightseens questions\n'
        '- plan_agent: produces a structured trip budget and packing list\n'
        '- general_agent: answers general questions\n\n'
        'User request: {user_request}\n'
        'Work completed so far: {completed_agents}\n\n'
        'Decide which agent should act next')

def initial_state(message):
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

CHAT_MODEL = 'gemini-3.6-flash'
def make_model():
    chat = ChatGoogleGenerativeAI(model=CHAT_MODEL)
    return chat


class TripPlan(BaseModel):
    destination: str
    duration_days: int = Field(gt=0, le=20, description='Trip length in days')
    daily_budget_usd: float = Field(gt=0, description='Daily budget in USD')
    packing_list: list[str] = Field(min_length=3, description='Packing list')


class TripPlanState(TypedDict):
    user_request: str
    error_message: str
    attempts: int
    plan: dict


def generate_plan(state: TripPlanState):
    attempts = state['attempts'] + 1

    prompt = f'Produce a trip plan for this request: {state["user_request"]}'

    if state['error_message']:
        prompt += (f'\n\n Your previous attempt failed validation with this error:'
                   f'\n{state["error_message"]}\nPlease fix the issue and try again.')


    planner_model = make_model().with_structured_output(TripPlan)

    try:
        result = planner_model.invoke(prompt)
        print(f'Valid Plan, Attempts: {attempts}')
        return {'plan': result.model_dump(), 'error_message': '', 'attempts': attempts}
    except (ValidationError, OutputParserException) as e:
        print(f'Invalid Plan, Attempts: {attempts}, Error: {e}')
        return {'error_message': str(e), 'attempts': attempts}


def check_validation(state: TripPlanState):
    if not state['error_message']:
        return END

    if state['attempts'] >= 5:
        return END

    return 'generate_plan'



def build_plan_graph():
    builder = StateGraph(TripPlanState)

    builder.add_node('generate_plan', generate_plan)

    builder.add_edge(START, 'generate_plan')

    builder.add_conditional_edges(
        'generate_plan', check_validation, {'generate_plan': 'generate_plan', END: END}
    )

    return builder.compile()


# def visualize_graph():
#     graph = build_plan_graph()
#
#     png_bytes = graph.get_graph().draw_mermaid_png()
#     with open('plan_graph.png', 'wb') as f:
#         f.write(png_bytes)
#
# visualize_graph()


def run_plan_graph():
    graph = build_plan_graph()

    result = graph.invoke(
        {
            'user_request': 'Budget plan for a 30-day trip to Tbilisi',
            'error_message': '',
            'attempts': 0,
            'plan': {}
        }
    )


    print(f'Finished after {result['attempts']} attempts')
    print(f'Destination: {result['plan']['destination']}')
    print(f'Duration Days: {result['plan']['duration_days']}')
    print(f'Daily Budget USD: {result['plan']['daily_budget_usd']}')
    print(f'Packing List: {result['plan']['packing_list']}')


# run_plan_graph()



###############################################################
# Supervisor
###############################################################


class AssistantState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


@tool
def get_weather(city: str):
    '''Get current weather for given city'''
    fake_data = {'Tbilisi': 'Sunny, 25C', 'London': 'Rainy, 20C', 'Rome': 'Sunny, 30C'}
    city = city.lower().capitalize()
    return fake_data.get(city, 'Unknown')

@tool
def find_sightseengs(city: str):
    '''Find popular sightseengs for given city'''
    fake_data = {
        'Tbilisi': 'Narikala Fortress, Abanotubani Sulfur Baths, Sameba Cathedral, Bridge of Peace, and the Dry Bridge Market.',
        'London': 'Big Ben, the Tower of London, Buckingham Palace, the British Museum, and the London Eye.',
        'Rome': 'The Colosseum, the Vatican Museums & Sistine Chapel, the Pantheon, Trevi Fountain, and the Roman Forum.',
    }

    city = city.lower().capitalize()
    return fake_data.get(city, 'Unknown')


TOOL_FUNCTIONS = {'get_weather': get_weather, 'find_sightseengs': find_sightseengs}


def call_tools(state: AssistantState):
    last_message = state['messages'][-1]

    tool_messages = []
    for tool_call in last_message.tool_calls:
        tool_function = TOOL_FUNCTIONS[tool_call['name']]
        result = tool_function.invoke(tool_call['args'])

        tool_messages.append(ToolMessage(content=str(result), tool_call_id=tool_call['id']))


    return {'messages': tool_messages}



def should_continue(state: AssistantState):
    last_message = state['messages'][-1]
    if last_message.tool_calls:
        return 'call_tools'
    else:
        return END


def call_model(state: AssistantState):
    chat = make_model().bind_tools([get_weather, find_sightseengs])
    response = chat.invoke(state['messages'])

    return {'messages': response}



def build_tool_graph():
    builder = StateGraph(AssistantState)

    builder.add_node('call_model', call_model)
    builder.add_node('call_tools', call_tools)

    builder.add_edge(START, 'call_model')
    builder.add_conditional_edges('call_model', should_continue, {'call_tools': 'call_tools', END: END})

    builder.add_edge('call_tools', 'call_model')


    return builder.compile()


class SupervisorDecision(BaseModel):
    next_agent: Literal['general_agent', 'tool_agent', 'plan_agent', 'finish']
    reasoning: str


class SupervisorState(TypedDict):
    user_request: str
    next_agent: str
    reasoning: str
    completed_agents: list[str]
    tool_agent_result: str
    plan_agent_result: dict
    general_agent_result: str
    final_note: str


def run_tool_graph(state: SupervisorState):
    builder = build_tool_graph()
    result = builder.invoke(
        {
            'messages': [
                HumanMessage(state['user_request'])
            ]
        },
        config={'recursion_limit': 10}
    )

    # for message in result['messages']:
    #     print(f'[{message.__class__.__name__}]: {message.content}')


    return {
        'tool_agent_result': result['messages'][-1].text,
        'completed_agents': state['completed_agents'] + ['tool_agent'],
    }


def run_plan_graph_in_supervisor(state: SupervisorState):
    graph = build_plan_graph()

    result = graph.invoke(
        {
            'user_request': 'Budget plan for a 30-day trip to Tbilisi',
            'error_message': '',
            'attempts': 0,
            'plan': {}
        }
    )


    # print(f'Finished after {result['attempts']} attempts')
    # print(f'Destination: {result['plan']['destination']}')
    # print(f'Duration Days: {result['plan']['duration_days']}')
    # print(f'Daily Budget USD: {result['plan']['daily_budget_usd']}')
    # print(f'Packing List: {result['plan']['packing_list']}')
    return {
        'plan_agent_result': result['plan'],
        'completed_agents': state['completed_agents'] + ['plan_agent'],
    }



def supervisor_node(state: SupervisorState):
    supervisor_model = make_model().with_structured_output(SupervisorDecision)
    decision = supervisor_model.invoke(
        'you are coordinating a trip-planning system with two specialist agent\n'
        '- tool_agent: handles weather and sightseens questions\n'
        '- plan_agent: produces a structured trip budget and packing list\n'
        '- general_agent: answers general questions\n\n'
        f'User request: {state["user_request"]}\n'
        f'Work completed so far: {state["completed_agents"]}\n\n'
        f'Decide which agent should act next'
    )


    next_agent = decision.next_agent
    reasoning = decision.reasoning

    print(f'Next Agent: {next_agent}')
    print(f'Reasoning: {reasoning}')

    if next_agent in state['completed_agents'] or next_agent == 'finish':
        next_agent = 'finish'
    return {'next_agent': next_agent, 'reasoning': reasoning}


def route_supervisor(state: SupervisorState):
    return state['next_agent']


def finalize_plan(state: SupervisorState):
    return {'final_note': 'Plan Finalized'}

def run_general_agent(state: SupervisorState):
    response = make_model().invoke(state['user_request'])

    return {
        'general_agent_result': response.text,
        'completed_agents': state['completed_agents'] + ['general_agent'],
    }


def build_supervisor_graph(checkpointer, ):

    builder = StateGraph(SupervisorState)

    builder.add_node('supervisor', supervisor_node)
    builder.add_node('general_agent', run_general_agent)
    builder.add_node('tool_agent', run_tool_graph)
    builder.add_node('plan_agent', run_plan_graph_in_supervisor)
    builder.add_node('finalize_plan', finalize_plan)

    builder.add_edge(START, 'supervisor')
    builder.add_conditional_edges(
        'supervisor',
        route_supervisor,
        {'general_agent': 'general_agent', 'tool_agent': 'tool_agent', 'plan_agent': 'plan_agent', 'finish': END},
    )

    builder.add_edge('general_agent', 'supervisor')
    builder.add_edge('tool_agent', 'supervisor')

    builder.add_edge('plan_agent', 'finalize_plan')
    builder.add_edge('finalize_plan', 'supervisor')

    return builder.compile(checkpointer=checkpointer, interrupt_before=['finalize_plan'])


def revise_plan(user_request, new_budget):
    plan_graph = build_plan_graph()
    new_plan = plan_graph.invoke(
        {
            'user_request': f'{user_request}'
                            f'The daily budget in USD must be {new_budget}'
                            f'Adjust the packing list and duration days to fit it',
            'error_message': '',
            'attempts': 0,
            'plan': {}
        }
    )

    final_plan = new_plan['plan']


    return {**final_plan, 'daily_budget_usd': new_budget}