
from dotenv import load_dotenv
from google import genai
from google.genai import types
import os

load_dotenv('.env')


MODEL = 'gemini-3.6-flash'
API_KEY = os.getenv('GEMINI_API_KEY')

client = genai.Client(api_key=API_KEY)

system_prompt_formal = 'You are formal legal assistant, respond precisely and cautiously'
system_prompt_friendly = 'You are casual, friendly helper, respond warmly and informally'

# messages = [
#      {"role": "system", "content": "You are a friendly assistant who explains things simply."},
#      {"role": "user", "content": "What is a token?"},
#      {"role": "assistant", "content": "A token is a small chunk of text the model processes."},
#      {"role": "user", "content": "what was my first question?"}
# ]

# response = client.models.generate_content(
#     model=MODEL,
#     contents='can I get refund if I change my mind about purchase?',
#     config=types.GenerateContentConfig(temperature=0.1, system_instruction=system_prompt_friendly)
# )


messages = [
    types.UserContent('What is a token?'),
    types.ModelContent('A token is a small chunk of text the model processes.'),
    types.UserContent('what was my first question?'),
]

response = client.models.generate_content(
    model=MODEL,
    contents=messages,
    config=types.GenerateContentConfig(temperature=0.1, system_instruction=system_prompt_friendly)
)


print(response.text)



