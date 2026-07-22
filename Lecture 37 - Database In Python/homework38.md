# დავალება

შექმენით ონლაინ მაღაზიის მონაცემთა ბაზის მოდელი SQLAlchemy ORM-ის გამოყენებით.

მონაცემთა ბაზაში უნდა გქონდეთ შემდეგი ცხრილები:

- `customers` — მომხმარებლები
- `orders` — შეკვეთები
- `products` — პროდუქტები
- `order_items` — შეკვეთაში დამატებული პროდუქტები

---

# 1. Customer Model

შექმენით `Customer` კლასი.

ველები:

| ველი | ტიპი |
|---|---|
| id | Integer (Primary Key) |
| name | String |
| email | String (Unique) |

ერთ მომხმარებელს შეიძლება ჰქონდეს რამდენიმე შეკვეთა.

დაამატეთ შესაბამისი `relationship`.

მაგალითად:

```

Customer 1 -------- N Order

```

---

# 2. Order Model

შექმენით `Order` კლასი.

ველები:

| ველი | ტიპი |
|---|---|
| id | Integer (Primary Key) |
| customer_id | ForeignKey |
| order_date | DateTime |

`customer_id` უნდა უკავშირდებოდეს `customers` ცხრილის `id` ველს.

დაამატეთ:

- `ForeignKey`
- `relationship`

---

# 3. Product Model

შექმენით `Product` კლასი.

ველები:

| ველი | ტიპი |
|---|---|
| id | Integer (Primary Key) |
| name | String |
| price | Integer |

---

# 4. OrderItem Model (Many-to-Many კავშირის ცხრილი)

შექმენით დამაკავშირებელი ცხრილი `order_items`.

რადგან:

- ერთ შეკვეთას შეიძლება ჰქონდეს ბევრი პროდუქტი
- ერთი პროდუქტი შეიძლება იყოს ბევრ შეკვეთაში

საჭიროა Many-to-Many ურთიერთობა.

კავშირი:

```

Order N -------- N Product

````

ცხრილს უნდა ჰქონდეს:

| ველი | ტიპი |
|---|---|
| id | Integer (Primary Key) |
| order_id | ForeignKey |
| product_id | ForeignKey |
| quantity | Integer |

დაამატეთ შესაბამისი `relationship`.

---

# 5. შექმენით ცხრილები

გამოიყენეთ:

```python
Base.metadata.create_all(engine)
````

---

# 6. დაამატეთ მონაცემები

ბაზაში დაამატეთ:

## მომხმარებლები

მინიმუმ 5 მომხმარებელი.

მაგალითი:

```
John
Anna
Kate
Bob
Patrick
```

---

## პროდუქტები

მინიმუმ 8 პროდუქტი.

მაგალითი:

```
Laptop
Phone
Keyboard
Mouse
Monitor
Headphones
Tablet
Camera
```

---

# 7. შექმენით შეკვეთები

შექმენით მინიმუმ 5 შეკვეთა.

თითოეულ შეკვეთას უნდა ჰყავდეს მომხმარებელი.

მაგალითად:

```
John
 |
 Order 1
 Order 2
```

---

# 8. დაამატეთ პროდუქტები შეკვეთებში

შექმენით `OrderItem` ჩანაწერები.

მაგალითად:

```
Order 1
 |
 |---- Laptop (quantity: 1)
 |---- Mouse (quantity: 2)


Order 2
 |
 |---- Phone (quantity: 1)
 |---- Headphones (quantity: 1)
```

---

# 9. SELECT ოპერაციები

შეასრულეთ შემდეგი მოთხოვნები:

## 1.

გამოიტანეთ ყველა მომხმარებელი.

მაგალითი:

```
ID: 1
Name: John
Email: john@gmail.com
```

---

## 2.

გამოიტანეთ კონკრეტული მომხმარებლის ყველა შეკვეთა.

მაგალითად:

```
Customer: John

Order ID: 1
Order Date: 2026-07-22

Order ID: 2
Order Date: 2026-07-22
```

გამოიყენეთ:

```python
joinedload()
```

---

## 3.

გამოიტანეთ კონკრეტული შეკვეთის ყველა პროდუქტი.

მაგალითი:

```
Order ID: 1

Laptop
Quantity: 1

Mouse
Quantity: 2
```

---

# 10. ახალი შეკვეთის დამატება

შექმენით ახალი შეკვეთა:

* აირჩიეთ არსებული მომხმარებელი
* დაამატეთ მინიმუმ 3 პროდუქტი

გამოიყენეთ ORM ურთიერთობები:

მაგალითად:

```python
order = Order(
    customer=customer
)
```

და არა მხოლოდ ID-ების ჩაწერა.

---

# 11. UPDATE

შეცვალეთ რომელიმე პროდუქტის ფასი.

მაგალითად:

```
Laptop
Old price: 1000

New price: 1200
```

ცვლილება შეინახეთ:

```python
session.commit()
```

