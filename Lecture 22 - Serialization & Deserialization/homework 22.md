# წიგნების ბიბლიოთეკის მართვის სისტემა

---

## შექმენი კონსოლური პროგრამა, რომელიც მართავს ბიბლიოთეკის წიგნებს და ინახავს ყველაფერს `books.json` ფაილში.

---

## ნაბიჯი 1 — მოდელი


```python
from dataclasses import dataclass

@dataclass
class Book:
    id: int
    title: str
    author: str
    year: int
    available: bool
```

`@dataclass` ავტომატურად უზრუნველყოფს, რომ `Book(1, "Clean Code", "Martin", 2008, True)` მუშაობდეს — `__init__` თავად იწერება.

---

## ნაბიჯი 2 — JSON-თან მუშაობა


```python
def save_books(books):
    with open("books.json", "w", encoding="utf-8") as f:
        json.dump([asdict(b) for b in books], f, ensure_ascii=False, indent=2)

def load_books():
    if os.path.exists("books.json"):
        with open("books.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return [Book(**item) for item in data]
    return []
```

> `asdict(b)` — `Book` ობიექტს გადააქვს dictionary-ად შესანახად  
> `Book(**item)` — dictionary-დან ქმნის `Book` ობიექტს ჩატვირთვისას

---

## ნაბიჯი 3 — მენიუ

```
1. წიგნის დამატება
2. ყველა წიგნის ნახვა
3. წიგნის ძებნა სახელით
4. წიგნის გატანა
5. წიგნის დაბრუნება
6. სტატისტიკა
7. მონაცემების შენახვა
8. გამოსვლა
```

---

## ნაბიჯი 4 — ფუნქციები

### 1. წიგნის დამატება

მომხმარებელი შეიყვანს სახელს, ავტორს და წელს. `available=True` ავტომატურად.

```
შეიყვანე სახელი: Clean Code
შეიყვანე ავტორი: Robert Martin
შეიყვანე წელი: 2008
✅ წიგნი დაემატა!
```

💡 **მინიშნება ID-სთვის:**
```python
new_id = max((b.id for b in books), default=0) + 1
```

---

### 2. ყველა წიგნის ნახვა

```
ID: 1 | Clean Code | Robert Martin | 2008 | ხელმისაწვდომი
ID: 2 | The Hobbit | Tolkien | 1937 | გაცემული
```

---

### 3. ძებნა სახელით

მომხმარებელი შეიყვანს ნაწილობრივ სახელს, მაგ. `code` — უნდა მოიძებნოს `Clean Code` და `Code Complete`.

💡 **მინიშნება:**
```python
if search.lower() in book.title.lower():
```

---

### 4. წიგნის გატანა

მომხმარებელი შეიყვანს ID-ს. თუ `available=True` — გასცე და `available` უნდა გახდეს `False`. თუ `available=False` — დაწერე შეცდომის შეტყობინება.

---

### 5. წიგნის დაბრუნება

მომხმარებელი შეიყვანს ID-ს. დააყენე `available=True`.

---

### 6. სტატისტიკა

```
სულ წიგნები:   10
ხელმისაწვდომი:  7
გაცემული:       3
```
