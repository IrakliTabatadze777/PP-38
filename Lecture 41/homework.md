# დავალება — FastAPI + SQLAlchemy CRUD

შექმენით FastAPI აპლიკაცია, რომელიც მართავს **მოგზაურობის ჩანაწერებს**.

აპლიკაციაში მომხმარებელს უნდა შეეძლოს მოგზაურობების დამატება, ნახვა, განახლება და წაშლა.

---

# მონაცემთა ბაზის მოდელი

შექმენით ცხრილი `trips`.

## Trip

| ველი | ტიპი | აღწერა |
|---|---|---|
| id | Integer | Primary Key |
| destination | String(100) | დანიშნულების ადგილი |
| country | String(50) | ქვეყანა |
| days | Integer | რამდენი დღე გაგრძელდა მოგზაურობა |
| budget | Integer | მოგზაურობის ბიუჯეტი |
| is_completed | Boolean | დასრულებულია თუ არა |

მაგალითი მონაცემი:

| id | destination | country | days | budget | is_completed |
|-|-|-|-|-|-|
| 1 | Paris | France | 5 | 1500 | True |
| 2 | Rome | Italy | 3 | 900 | False |

---

# SQLAlchemy

შექმენით:

- Base კლასი
- engine
- Session
- Trip მოდელი

მოდელში სწორად განსაზღვრეთ:

- Primary Key
- Column ტიპები
- საჭირო შეზღუდვები

---

# Pydantic Schema-ები

შექმენით:

## TripCreate

გამოიყენება ახალი ჩანაწერის შესაქმნელად.

უნდა შეიცავდეს:

- destination
- country
- days
- budget
- is_completed


## TripResponse

გამოიყენება მონაცემების დასაბრუნებლად.

უნდა შეიცავდეს:

- id
- destination
- country
- days
- budget
- is_completed

---

# API Endpoint-ები

## 1. ახალი მოგზაურობის დამატება

```

POST /trips

````

მიიღეთ JSON მონაცემები და შეინახეთ მონაცემთა ბაზაში.

მაგალითი:

```json
{
    "destination": "Barcelona",
    "country": "Spain",
    "days": 7,
    "budget": 2000,
    "is_completed": false
}
````

---

## 2. ყველა მოგზაურობის მიღება

```
GET /trips
```

დააბრუნეთ ყველა ჩანაწერი.

---

## 3. კონკრეტული მოგზაურობის მიღება

```
GET /trips/{trip_id}
```

თუ ასეთი ჩანაწერი არ არსებობს, დააბრუნეთ:

```
404 Not Found
```

---

## 4. მოგზაურობის განახლება

```
PUT /trips/{trip_id}
```

შეცვალეთ არსებული ჩანაწერის მონაცემები.

მაგალითად:

* ბიუჯეტის შეცვლა
* დასრულებულის სტატუსის შეცვლა

---

## 5. მოგზაურობის წაშლა

```
DELETE /trips/{trip_id}
```

წაშალეთ ჩანაწერი მონაცემთა ბაზიდან.

---

# დამატებითი მოთხოვნები

კოდში გამოიყენეთ:

* `session.add()`
* `session.commit()`
* `session.refresh()`
* `session.delete()`
* `select()`

არ გამოიყენოთ პირდაპირი SQL query-ები.
