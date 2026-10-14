from dotenv import load_dotenv

load_dotenv()

import langsmith as ls
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tracers.langchain import wait_for_all_tracers
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash", temperature=0)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a concise travel guide for Georgia (the country)."),
    ("user", "Give me {n} reasons to visit {city}."),
])

chain = prompt | llm | StrOutputParser()

try:
    print(chain.invoke({"n": 3, "city": "Kutaisi"}))

    print(chain.invoke(
        {"n": 3, "city": "Kutaisi"},
        config={"run_name": "city_reasons", "tags": ["lecture-demo"]},
    ))

    with ls.tracing_context(project_name="trip-assistant-experiments", enabled=True):
        chain.invoke({"n": 3, "city": "Batumi"})

    with ls.tracing_context(enabled=False):
        chain.invoke({"n": 3, "city": "Batumi"})
finally:
    wait_for_all_tracers()
