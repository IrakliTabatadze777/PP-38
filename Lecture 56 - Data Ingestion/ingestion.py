from pypdf import PdfReader
from google.genai import Client
from dotenv import load_dotenv
from pgvector import Vector
from pgvector.psycopg2 import register_vector
import psycopg2

load_dotenv()

###########################################################################
# File Readers
def read_md_file(filename):
    with open(filename, 'r') as f:
        raw_text = f.read()

    return raw_text

def read_pdf_file(filename):
    reader = PdfReader(filename)

    full_text = ''

    for page in reader.pages:
        full_text += page.extract_text() + '\n'


    return full_text

###########################################################################


# *************************************************************************
# Fixed Sized Chunk
def fixed_sized_chunk(text: str, chunk_size: int = 500) -> list:
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i + chunk_size]) # [0:500] -> [500:1000]

    return chunks


def check_fixed_sized_chunk():
    pdf_content = read_pdf_file('handbook.pdf')

    pdf_chunks = fixed_sized_chunk(pdf_content)

    print(len(pdf_chunks))
    print(len(pdf_chunks[0]))
    print(pdf_chunks[0])
# *************************************************************************



###########################################################################
# Structure-Aware Chunking

def paragraph_chunk(text: str) -> list:
    chunks = []

    for paragraph in text.split('\n\n'):
        chunks.append(paragraph.strip())

    return chunks

def check_paragraph_chunk():
    # pdf_content = read_pdf_file('handbook.pdf')
    # pdf_chunks = paragraph_chunk(pdf_content)

    md_content = read_md_file('company_handbook.md')
    md_chunks = paragraph_chunk(md_content)
    print(md_chunks[2])

# check_paragraph_chunk()
###########################################################################




# *************************************************************************
# Chunk Overlap

def chunks_with_overlap(text: str, chunk_size: int=500, overlap: int=100):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap # [0:500] -> [400:900]
    return chunks

def check_chunks_with_overlap():
    pdf_content = read_pdf_file('handbook.pdf')

    pdf_chunks = chunks_with_overlap(pdf_content)

    print(pdf_chunks[0])
    print(pdf_chunks[1])

# check_chunks_with_overlap()
# *************************************************************************





###########################################################################
# Document Ingestion

def embed_chunk(client: Client, chunk_text: str):
    model = 'gemini-embedding-2'
    result = client.models.embed_content(model=model, contents=chunk_text)

    return Vector(result.embeddings[0].values)


def ingest_info_pgvector(source_document: str, chunk_index: int, content: str, embedding: Vector):
    connection = psycopg2.connect(host='localhost', port=5432, user='postgres', password='123123', database='embedding')
    register_vector(connection)

    cursor = connection.cursor()

    cursor.execute('''
        insert into document_chunks(source_document, chunk_index, content, embedding)
        values (%s, %s, %s, %s)
    ''',
    (source_document, chunk_index, content, embedding)
    )

    connection.commit()
    cursor.close()
    connection.close()

    print(f'Ingestion completed for chunk {chunk_index}')

def ingestion():
    client = Client()

    filename = 'handbook.pdf'
    pdf_content = read_pdf_file(filename)
    pdf_chunks = chunks_with_overlap(pdf_content)

    for i, chunk in enumerate(pdf_chunks):
        embedded_content = embed_chunk(client, chunk)

        ingest_info_pgvector(filename, i, chunk, embedded_content)


# ingestion()

###########################################################################



def demo_search():
    client = Client()


    query_text = 'how much paid vacation do employees get?'
    embedded_content = embed_chunk(client, query_text)


    connection = psycopg2.connect(host='localhost', port=5432, user='postgres', password='123123', database='embedding')
    register_vector(connection)

    cursor = connection.cursor()

    cursor.execute('''
        select chunk_index, content, embedding <=> %s as distance
        from document_chunks
        order by distance
    ''', (embedded_content,))

    rows = cursor.fetchall()
    for row in rows:
        print(row)

    cursor.close()
    connection.close()

# demo_search()