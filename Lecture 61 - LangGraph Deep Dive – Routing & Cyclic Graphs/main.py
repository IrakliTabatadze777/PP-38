
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import tool
from langchain_core.messages import BaseMessage, ToolMessage, HumanMessage
from langgraph.graph.message import add_messages
from langgraph.graph import START, END, StateGraph
from typing import TypedDict, Annotated



load_dotenv()

CHAT_MODEL = 'gemini-3.6-flash'
def make_model():
    chat = ChatGoogleGenerativeAI(model=CHAT_MODEL)
    return chat


############################################################################
# Conditional Edges
############################################################################

class TripState(TypedDict):
    user_request: str
    destination: str
    response: str


def packing_list_node(state: TripState):
    print('Calling packing_list_node')
    chat = make_model()
    prompt = f'Suggest a concise packing list for a trip to {state["destination"]}.'
    result = chat.invoke(prompt)
    return {'response': result.text}


def day_plan_node(state: TripState):
    print('Calling day_plan_node')
    chat = make_model()
    prompt = f'Suggest a simple one-day plan for a trip to {state["destination"]}.'
    result = chat.invoke(prompt)
    return {'response': result.text}


def route_by_request_type(state: TripState):
    if 'pack' in state['user_request']:
        return 'packing_list'
    else:
        return 'day_plan'



def build_routing_graph():
    builder = StateGraph(TripState)

    builder.add_node('packing_list', packing_list_node)
    builder.add_node('day_plan', day_plan_node)

    builder.add_conditional_edges(
        START,
        route_by_request_type,
        {'packing_list': 'packing_list', 'day_plan': 'day_plan'}
    )

    builder.add_edge('packing_list', END)
    builder.add_edge('day_plan', END)

    return builder.compile()


def main():
    graph = build_routing_graph()

    result = graph.invoke({'user_request': 'What should I see in Tbilisi?', 'destination': 'Tbilisi', 'response': ''})

    print(result)

if __name__ == '__main__':
    main()


# def visualize_graph():
#     graph = build_routing_graph()
#
#     png_bytes = graph.get_graph().draw_mermaid_png()
#     with open('graph.png', 'wb') as f:
#         f.write(png_bytes)
#
# visualize_graph()






############################################################################
# Tools And Cycle Graph
############################################################################
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




def main():
    builder = build_tool_graph()
    result = builder.invoke(
        {
            'messages': [
                HumanMessage('what\'s the weather in Tbilisi and what sighseeng should I see there?')
            ]
        },
        config={'recursion_limit': 10}
    )

    for message in result['messages']:
        print(f'[{message.__class__.__name__}]: {message.content}')



if __name__ == '__main__':
    main()

# def visualize_graph():
#     graph = build_tool_graph()
#
#     png_bytes = graph.get_graph().draw_mermaid_png()
#     with open('tool_graph.png', 'wb') as f:
#         f.write(png_bytes)
#
# visualize_graph()