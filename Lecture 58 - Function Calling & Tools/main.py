
from dotenv import load_dotenv
from google.genai import Client
from google.genai import types
from tools import get_weather, search_news, weather_tool_schema, news_tool_schema


load_dotenv()


MODEL = 'gemini-3.6-flash'



TOOL_REGISTRY ={
    'get_weather': lambda kwargs: get_weather(**kwargs),
    'search_news': lambda kwargs: search_news(**kwargs),
}


weather_tool = types.Tool(function_declarations=[weather_tool_schema])
news_tool = types.Tool(function_declarations=[news_tool_schema])

weather_config = types.GenerateContentConfig(tools=[weather_tool, news_tool])


client = Client()
# question = 'what is the weather in Tbilisi and New-York?'
# question = 'what is 2*2?'
question = 'Recent news about AI development, use only my tools'

response = client.models.generate_content(
    model=MODEL,
    contents=question,
    config=weather_config
)

# parts = response.parts[0]

# args = {'city': 'Tbilisi'}

function_responses = []
for parts in response.parts:
    if parts.function_call:
        call = parts.function_call
        result = TOOL_REGISTRY[call.name](call.args)

        function_response_part = types.Part.from_function_response(
            name=call.name, response={'result': result}
        )

        function_responses.append(function_response_part)


    else:
        print(parts.text)


follow_up = client.models.generate_content(
        model=MODEL,
        contents=[question, response.parts, function_responses],
        config=weather_config
    )

print(follow_up.text)