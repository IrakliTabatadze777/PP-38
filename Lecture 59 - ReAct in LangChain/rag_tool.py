from google.genai import Client, types
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_postgres import PGVector


load_dotenv()


EMBEDDING_MODEL = 'gemini-embedding-2'
CHAT_MODEL = 'gemini-3.6-flash'



def get_retriever(top_k: int = 5):
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)

    vector_store = PGVector(
        embeddings=embeddings,
        collection_name='document_chunks',
        connection='postgresql+psycopg2://postgres:123123@localhost:5432/embedding',
        embedding_length=3072
    )

    return vector_store.as_retriever(search_kwargs={'k': top_k})


def search_docs(retriever, question: str):
    retrieved_docs = retriever.invoke(question)

    docs_string = '\n\n'.join(doc.page_content for doc in retrieved_docs)
    return docs_string


retriever_tool_schema = {
    'name': 'search_docs',
    'description': 'Search internal company documents for information relevant to a question',
    'parameters': {
        'type': 'object',
        'properties': {
            'question': {
                'type': 'string',
                'description': 'the question to search company documents for.'
            }
        },
        'required': ['question']
    }
}


retriever_tool = types.Tool(function_declarations=[retriever_tool_schema])
retriever_config = types.GenerateContentConfig(tools=[retriever_tool])



def main():
    client = Client()

    retriever = get_retriever(top_k=5)

    question = 'What is our policy on remote work?'

    response = client.models.generate_content(
        model=CHAT_MODEL, contents=question, config=retriever_config
    )


    function_response_parts = []

    for part in response.parts:
        if part.function_call:
            call = part.function_call

            print(f'Requested: {call.name}, args:', dict(call.args))

            if call.name == 'search_docs':
                result = search_docs(retriever, **call.args)

                function_response_parts.append(
                    types.Part.from_function_response(name=call.name, response={'result': result})
                )


    follow_up = client.models.generate_content(
        model=CHAT_MODEL,
        contents=[question, response.parts, function_response_parts],
        config=retriever_config
    )


    print(follow_up.text)



main()