from google.genai import Client
from dotenv import load_dotenv
import psycopg2


load_dotenv()


client = Client()


def get_pg_connection():
    return psycopg2.connect(user='postgres', password='123123', host='localhost', port='5432', database='embedding')




# connection = get_pg_connection()
# cursor = connection.cursor()
#
#
# texts = [
#     'A small dog running in the park',
#     'A puppy playing outside',
#     'A new laptop with a fast processor'
# ]


# for text in texts:
#     vector = client.models.embed_content(
#         model='gemini-embedding-2',
#         contents=text
#     )
#
#     cursor.execute('insert into document(content, vector) values (%s, %s)', (text, vector.embeddings[0].values))
#
# connection.commit()
# cursor.close()
# connection.close()






connection = get_pg_connection()
cursor = connection.cursor()

input_text = input('please input some text: ')



embedded_text = client.models.embed_content(
        model='gemini-embedding-2',
        contents=input_text
    )

vector = embedded_text.embeddings[0].values
vector = '[' + ','.join(str(x) for x in vector) + ']'


cursor.execute("select id, content, vector <=> %s as distance from document order by distance limit 1", (vector, ))


rows = cursor.fetchone()

cursor.close()
connection.close()


print(rows)

