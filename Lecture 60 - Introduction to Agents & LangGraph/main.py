from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import START, END, StateGraph
from typing import TypedDict


load_dotenv()



CHAT_MODEL = 'gemini-3.6-flash'

RAW_TEXT ='''
         Lorem ipsum   dolor sit amet, consectetur adipiscing elit. 
    Duis non ultrices magna, sed posuere augue. 
    Nulla facilisi. 
    Nullam aliquam aliquam risus sit amet malesuada. 
    Vestibulum ullamcorper orci in efficitur malesuada. 
    In hac habitasse platea dictumst.\n\n Morbi id viverra est. 
    In hac habitasse platea dictumst. \n\n
    Mauris porttitor sapien sit amet bibendum vestibulum. 
    Etiam fringilla non nibh a posuere. Aliquam erat volutpat. 
    Etiam et tellus ut odio sagittis tempor in vel lorem. 
    Nullam consequat fringilla fringilla. 
    Aenean velit felis, convallis ut imperdiet tristique, dapibus ac lectus. 
    Cras quis tempor libero, ut fringilla erat. Sed ultrices sapien quis orci cursus luctus.
'''

class PipelineState(TypedDict):
    raw_text: str
    cleaned_text: str
    summary: str



def clean_node(state: PipelineState):
    cleaned = state['raw_text'].strip().replace('\n', '')
    return {'cleaned_text': cleaned}


def summarize_node(state: PipelineState):
    chat = ChatGoogleGenerativeAI(model=CHAT_MODEL)
    question = f'Summarize this text in one sentence:\n\n{state["cleaned_text"]}'

    response = chat.invoke(question)

    return {'summary': response.text}

def format_node(state: PipelineState):
    formatted = state['summary'].strip()
    return {'summary': f'Summary:\n\n{formatted}'}


# pipeline_state = PipelineState(raw_text=RAW_TEXT)
# cleaned_text = clean_node(pipeline_state)
#
# pipeline_state['cleaned_text'] = cleaned_text['cleaned_text']
#
# summary = summarize_node(pipeline_state)
#
# pipeline_state['summary'] = summary['summary']
#
# formatted_summary = format_node(pipeline_state)
# pipeline_state['summary'] = formatted_summary['summary']
#
# for k, v in pipeline_state.items():
#     print(f'{k}: {v}')


def build_graph():
    builder = StateGraph(PipelineState)

    builder.add_node('clean', clean_node)
    builder.add_node('summary', summarize_node)
    builder.add_node('format', format_node)

    builder.add_edge(START, 'clean')
    builder.add_edge('clean', 'summary')
    builder.add_edge('summary', 'format')
    builder.add_edge('format', END)

    return builder.compile()


def run_graph():
    graph = build_graph()

    result = graph.invoke({'raw_text': RAW_TEXT})

    print(result['summary'])


run_graph()
# def visualize_graph():
#     graph = build_graph()
#
#     png_bytes = graph.get_graph().draw_mermaid_png()
#     with open('graph.png', 'wb') as f:
#         f.write(png_bytes)
#
# visualize_graph()