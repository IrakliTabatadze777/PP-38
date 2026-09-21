
from dotenv import load_dotenv
from langchain_postgres import PGVector
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_classic.chains.combine_documents.stuff import create_stuff_documents_chain



from langsmith import Client


load_dotenv()

EMBEDDING_MODEL = 'gemini-embedding-2'
CHAT_MODEL = 'gemini-2.5-flash'

embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)

vector_store = PGVector(
    embeddings=embeddings,
    collection_name='document_chunks',
    connection='postgresql+psycopg2://postgres:123123@localhost:5432/embedding',
    embedding_length=3072
)


retriever = vector_store.as_retriever(search_kwargs={'k': 5})


client = Client()
retrieval_qa_chat_prompt = client.pull_prompt("langchain-ai/retrieval-qa-chat", dangerously_pull_public_prompt=True)

model = ChatGoogleGenerativeAI(model=CHAT_MODEL)
combine_docs_chain = create_stuff_documents_chain(model, retrieval_qa_chat_prompt)
retrieval_chain = create_retrieval_chain(retriever, combine_docs_chain)

result = retrieval_chain.invoke({'input': 'What is our policy on remote work?'})


print(result['answer'])
