
### დავალება 1 — Cosine Similarity

| # | ტექსტი 1                              | ტექსტი 2                                      |
|---|---------------------------------------|-----------------------------------------------|
| 1 | A small dog running in the park       | A puppy playing outside                       |
| 2 | A small dog running in the park       | A new laptop with a fast processor            |
| 3 | I love programming in Python          | Python is a great programming language        |
| 4 | I love programming in Python          | The capital of France is Paris                |

**რა უნდა გააკეთო:**
- დაწერე კოდი, რომელიც ამ 4 წყვილის cosine similarity-ს გამოთვლის.
- კონსოლში უნდა დაიბეჭდოს ზუსტად ასე:

```
1. 0.XXXX
2. 0.XXXX
3. 0.XXXX
4. 0.XXXX
```

---

### დავალება 2 — მონაცემების ჩაწერა PostgreSQL-ში

შექმენი ცხრილი (თუ არ გაქვს):

```sql
CREATE TABLE document (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    vector vector(768)   -- თუ განზომილება სხვაა, შეცვალე
);
```

ჩაწერე **ეს 8 ტექსტი**:

1. A small dog running in the park  
2. A puppy playing outside  
3. A new laptop with a fast processor  
4. I love programming in Python  
5. Machine learning is a subset of artificial intelligence  
6. The weather is very cold today  
7. Cats are independent animals  
8. Deep learning uses neural networks  

- დაწერე კოდი, რომელიც ამ 8 ტექსტს embedding-ით ჩაწერს ბაზაში.

---

### დავალება 3 — Similarity Search

დაწერე პროგრამა, რომელიც:

1. იღებს ტექსტს მომხმარებლისგან (`input()`-ით).
2. აგენერირებს მის embedding-ს.
3. ბაზიდან აბრუნებს **TOP-3** ყველაზე მსგავს დოკუმენტს.
4. ბეჭდავს შედეგს **ზუსტად** შემდეგი ფორმატით:
5. გამოიყენეთ წინა ამოცანაში შენახული მონაცემები ბაზიდან

```
Top 3 similar documents:
1. [id=X] distance=0.XXXX | content: ...
2. [id=X] distance=0.XXXX | content: ...
3. [id=X] distance=0.XXXX | content: ...
```