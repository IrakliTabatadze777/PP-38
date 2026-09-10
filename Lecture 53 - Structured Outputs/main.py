from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ClientError
from pydantic import BaseModel
import os

load_dotenv('.env')


MODEL = 'gemini-3.6-flash'
API_KEY = os.getenv('GEMINI_API_KEY')

client = genai.Client(api_key=API_KEY)

# history = [
#     types.UserContent('Hello, how are you'),
#     types.ModelContent('Hello, I\'m fine, How may I help you?'),
#     types.UserContent('I love learning about AI.'),
# ]

# token_count = client.models.count_tokens(
#     model=MODEL,
#     contents=history
#     # contents='მე მიყვარს ხელოვნური ინტელექტის შესწავლა'
# )


# print(token_count.total_tokens)
#
# if token_count.total_tokens == 0:
#     pass
#
# if token_count.total_tokens > 500:
#     raise ClientError(response_json={'message': f'Too much token count: {token_count.total_tokens}'}, code=429)
#


# def trim_history(history, max_turns):
    # system_prompt = history[0]
    # recent_history = [system_prompt] + history[-max_turns:]
    # recent_history = history[-max_turns:] # [-10:]
    # return recent_history



# history = []
#
# for i in range(101):
#     if i % 2 == 0:
#         history.append(types.UserContent(f'User Content Turn {i}'))
#     else:
#         history.append(types.ModelContent(f'Model Content Turn {i-1}'))
#
#
# trimmed_history = trim_history(history, 10)
#
# print(f'full history: {len(history)}, trimmed history: {len(trimmed_history)}')
#
# response = client.models.generate_content(
#     model=MODEL,
#     contents=trimmed_history
# )
#
# print(response.usage_metadata.total_token_count)





class Event(BaseModel):
    date: str
    location: str
    attendees: list[str]


txt = '''Reminder: the quarterly planning meeting is happening on March 14th
at the downtown office, 3rd floor conference room. Nino, David, and Ana are expected.'''


prompt = f'Extract information from text: {txt}'


# class Contents(BaseModel):
#     title: str
#     attendees: str
#     content: str


# prompt = 'I\'m content creator, need you to generate content about my new meet, meet should be about Python Langchain'


response = client.models.generate_content(
    model=MODEL,
    contents=prompt,
    config=types.GenerateContentConfig(
        temperature=0.1,
        response_schema=Event,
        response_mime_type='application/json',
    )
)


# contents = Contents.model_validate_json(response.text)
#
# print(contents.title)
# print(contents.attendees)
# print(contents.content)

event = Event.model_validate_json(response.text)

print(event.date)
print(event.location)
print(event.attendees)
