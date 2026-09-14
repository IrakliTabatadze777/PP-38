from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

MODEL = 'gemini-3.6-flash'

chat_gemini = ChatGoogleGenerativeAI(model=MODEL)

# response = chat_gemini.invoke('explain langchain in two sentences')
# print(response.content[0]['text'])


# messages = [
#     SystemMessage(content='You are helpful technical assistant'),
#     HumanMessage(content='what is a token?'),
#     AIMessage(content='A token is a small chunk of text'),
#     HumanMessage(content='can you give me an example?')
# ]
#
# response = chat_gemini.invoke(messages)
# print(response.content[0]['text'])



class Event(BaseModel):
    title: str
    date: str
    location: str
    attendees: list[str]


structured_model = chat_gemini.with_structured_output(Event)

template = PromptTemplate.from_template(
    "Extract the event details from this text:"
    "\n\n{input_text}"
)


# message = template.invoke({'input_text': 'The team meeting is on Friday at 3pm in Room 204.'})

# print(message.text)

# chain = template | chat_gemini
chain = template | structured_model

response = chain.invoke({'input_text': 'The team meeting is on Friday at 3pm in Room 204.'})
# print(response.text)
print(response.title)
print(response.date)
print(response.location)
print(response.attendees)
