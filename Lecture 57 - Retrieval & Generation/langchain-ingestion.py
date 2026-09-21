
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from langchain_postgres import PGVector
from dotenv import load_dotenv

load_dotenv()



def chunks_with_overlap(text: str, chunk_size: int=500, overlap: int=100):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


EMBEDDING_MODEL = 'gemini-embedding-2'

embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)

vector_store = PGVector(
    embeddings=embeddings,
    collection_name='document_chunks',
    connection='postgresql+psycopg2://postgres:123123@localhost:5432/embedding',
    embedding_length=3072
)


with open('company_handbook.md', 'r') as file:
    raw_text = file.read()


chunks = chunks_with_overlap(raw_text)


docs = []

for index, chunk in enumerate(chunks):
    doc = Document(page_content=chunk,
             metadata={'source_document': 'company_handbook.md', 'chunk_index': index}
             )

    docs.append(doc)

vector_store.add_documents(docs)