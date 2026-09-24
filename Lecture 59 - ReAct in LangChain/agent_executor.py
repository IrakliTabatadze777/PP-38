from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import AgentExecutor, create_react_agent


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


tools = [get_weather, find_conference_city]



from langsmith import Client

client = Client()
prompt = client.pull_prompt("hwchase17/react", dangerously_pull_public_prompt=True)


llm = ChatGoogleGenerativeAI(model='gemini-3.6-flash', stop=['\nObservation', 'Observation'])
agent = create_react_agent(llm, tools, prompt)


agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    max_iterations=5,
    return_intermediate_steps=True,
    verbose=True
)


result = agent_executor.invoke({'input': 'What\'s the weather in the city where our next conference is being held?'})

print(result['output'])

