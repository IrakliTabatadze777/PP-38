from dotenv import load_dotenv
from typing import Union
from langchain_core.tools import tool, render_text_description
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents.output_parsers import ReActSingleInputOutputParser
from langchain_classic.agents.format_scratchpad import format_log_to_str
from langchain_core.agents import AgentAction, AgentFinish

load_dotenv()

@tool
def get_weather(city: str):
    '''Get current weather for a given city'''
    mock_data = {
        'Tbilisi': 'Sunny, 25 Celsius',
        'Berlin': 'Rainy, 20 Celsius'
    }

    return mock_data.get(city, 'Unknown')


@tool
def find_conference_city():
    '''Find the city where the next conference is being held.'''
    return 'Tbilisi'



def find_tool_by_name(tools_list, tool_name):
    for t in tools_list:
        if t.name == tool_name:
            return t

    raise ValueError(f'Tool {tool_name} not found')


tools = [get_weather, find_conference_city]

def run_tool(tool_to_use, tool_input):
    tool_for_run = find_tool_by_name(tools, tool_to_use)

    # print(tool_input)
    if tool_input != '{}\n' and tool_input != '{}':
        tool_result = str(tool_for_run.func(tool_input))
        return tool_result

    return str(tool_for_run.func())



def build_agent(prompt):
    llm = ChatGoogleGenerativeAI(
        model='gemini-3.6-flash',
        temperature=0,
        stop=['Observation', '\nObservation']
    )

    chain = ({
                'input': lambda x: x['input'],
                'agent_scratchpad': lambda x: format_log_to_str(x['agent_scratchpad'])
            }
             | prompt
             | llm
             | ReActSingleInputOutputParser()
    )


    return chain


def main():
    template = """Answer the following questions as best you can. You have access to the following tools:
    
    {tools}
    
    Use the following format:
    
    Question: the input question you must answer
    Thought: you should always think about what to do
    Action: the action to take, should be one of [{tool_names}]
    Action Input: the input to the action
    Observation: the result of the action
    ... (this Thought/Action/Action Input/Observation can repeat N times)
    Thought: I now know the final answer
    Final Answer: the final answer to the original input question
    
    Begin!
    
    Question: {input}
    Thought: {agent_scratchpad}
    """

    question = 'What\'s the weather in the city where our next conference is being held?'
    intermediate_steps = []

    prompt = PromptTemplate.from_template(template=template).partial(
        tools=render_text_description(tools),
        tool_names=', '.join([t.name for t in tools])
    )



    agent = build_agent(prompt)

    max_steps = 5
    for step in range(max_steps):
        agent_step: Union[AgentAction, AgentFinish] = agent.invoke(
            {'input': question, 'agent_scratchpad': intermediate_steps}
        )

        if isinstance(agent_step, AgentFinish):
            return agent_step.return_values['output']


        observation = run_tool(agent_step.tool, agent_step.tool_input)

        intermediate_steps.append((agent_step, observation))



    return 'Stopped after reaching max_steps without a final answer'


if __name__ == '__main__':
    print(main())