
from google.genai import Client
from dotenv import load_dotenv

load_dotenv()

client = Client()

# result = client.models.embed_content(
#     model='gemini-embedding-2',
#     contents='A small dog running in the park'
# )


# embedding = result.embeddings[0].values
# print(len(embedding))
# print(embedding[:10])



import numpy as np

def cosine_similarity(vec_a, vec_b):
    a = np.array(vec_a)
    b = np.array(vec_b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))



dog_vector = client.models.embed_content(
    model='gemini-embedding-2',
    contents='A small dog running in the park'
)


puppy_vector = client.models.embed_content(
    model='gemini-embedding-2',
    contents='A puppy playing outside'
)


laptop_vector = client.models.embed_content(
    model='gemini-embedding-2',
    contents='A new laptop with a fast processor'
)


# print(dog_vector.embeddings[0].values[:10])
# print(puppy_vector.embeddings[0].values[:10])
# print(laptop_vector.embeddings[0].values[:10])

cosine_dog_puppy = cosine_similarity(dog_vector.embeddings[0].values, puppy_vector.embeddings[0].values)
cosine_dog_laptop = cosine_similarity(dog_vector.embeddings[0].values, laptop_vector.embeddings[0].values)

print(cosine_dog_puppy)
print(cosine_dog_laptop)