

from google.genai import Client
from pgvector import Vector
from dotenv import load_dotenv
from pgvector.psycopg2 import register_vector
import psycopg2


load_dotenv()



EMBEDDING_MODEL = 'gemini-embedding-2'
CHAT_MODEL = 'gemini-2.5-flash'


def get_pg_connection():
    connection = psycopg2.connect(host='localhost', port=5432, user='postgres', password='123123', database='embedding')

    register_vector(connection)
    return connection



def search_chunk(connection, query_embedding: Vector, top_k: int = 5):
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT source_document, chunk_index, content, embedding <=> %s AS distance
        FROM document_chunks
        ORDER BY distance
        LIMIT %s
        """,
        (query_embedding, top_k)
    )

    rows = cursor.fetchall()

    cursor.close()
    return rows



def embed_query(client: Client, user_input: str):
    result = client.models.embed_content(model=EMBEDDING_MODEL, contents=user_input)

    return Vector(result.embeddings[0].values)


def build_prompt(user_input: str, retrieved_chunks: list):
    prompt = """
Answer the question using ONLY the context provided below.
If the answer is not contained in the context, say "I don't have enough information to answer question",
Cite which source(s) you used in your answer.

Context:
{context_data}

Question:
{user_input}
"""

    chunk_blocks = []
    for source, index, content, distance in retrieved_chunks:
        chunk_blocks.append(f'Source: {source} (chunk {index})\nContent: {content}')

    context_data = '\n\n---\n\n'.join(chunk_blocks)

    formatted_prompt = prompt.format(context_data=context_data, user_input=user_input)

    return formatted_prompt


def main():
    USER_INPUT = 'What is our policy on remote work?'

    client = Client()



    embedded_query = embed_query(client, USER_INPUT)


    database_connection = get_pg_connection()
    retrieved_chunks = search_chunk(database_connection, embedded_query, top_k=5)


    # for source, index, content, distance in retrieved_chunks:
    #     print(f'[{source} #{index}]  distance={distance:.4f}')

    prompt = build_prompt(USER_INPUT, retrieved_chunks)
    # print(prompt)

    result = client.models.generate_content(model=CHAT_MODEL, contents=prompt)
    print(result.text)

if __name__ == "__main__":
    main()


