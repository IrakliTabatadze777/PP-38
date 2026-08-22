# პროექტი: E-Commerce API აპლიკაცია

## 1. პროექტის მიზანი

შექმენით სრულფასოვანი **Backend API** ელექტრონული კომერციისთვის (E-Commerce), რომელიც საშუალებას მისცემს მომხმარებლებს:
- რეგისტრაცია და ავტორიზაცია
- პროდუქტების ნახვა, ძებნა და ფილტრაცია
- კალათაში დამატება / ამოღება
- შეკვეთის გაფორმება
- შეკვეთების ისტორიის ნახვა
- ადმინისტრატორის მხრიდან პროდუქტებისა და შეკვეთების მართვა

ტექნოლოგიები:
- **FastAPI** (API ფრეიმვორკი)
- **PostgreSQL** (მონაცემთა ბაზა)
- **SQLAlchemy 2.0** + **Alembic** (ORM და მიგრაციები)
- **Pydantic v2** (ვალიდაცია)
- **JWT** ავტორიზაცია (python-jose ან PyJWT)
- **passlib** + **bcrypt** (პაროლების ჰეშირება)
- **BackgroundTasks** (ფონური დავალებებისთვის)

---

## 2. მონაცემთა ბაზის მოდელები (SQLAlchemy)

### 2.1. User
| ველი              | ტიპი          | აღწერა                              |
|-------------------|---------------|-------------------------------------|
| id                | Integer (PK)  |                                     |
| email             | String(255)   | უნიკალური, indexed                  |
| hashed_password   | String        |                                     |
| full_name         | String(150)   |                                     |
| is_active         | Boolean       | default=True                        |
| is_admin          | Boolean       | default=False                       |
| created_at        | DateTime      | server_default=now()                |
| updated_at        | DateTime      | onupdate=now()                      |

### 2.2. Category
| ველი        | ტიპი          | აღწერა                     |
|-------------|---------------|----------------------------|
| id          | Integer (PK)  |                            |
| name        | String(100)   | უნიკალური                  |
| slug        | String(120)   | უნიკალური, indexed         |
| description | Text          | nullable                   |
| is_active   | Boolean       | default=True               |

### 2.3. Product
| ველი          | ტიპი            | აღწერა                              |
|---------------|-----------------|-------------------------------------|
| id            | Integer (PK)    |                                     |
| name          | String(200)     |                                     |
| slug          | String(220)     | უნიკალური, indexed                  |
| description   | Text            |                                     |
| price         | Numeric(10, 2)  |                                     |
| stock         | Integer         | default=0                           |
| category_id   | Integer (FK)    | → categories.id                     |
| is_active     | Boolean         | default=True                        |
| created_at    | DateTime        |                                     |
| updated_at    | DateTime        |                                     |

### 2.4. CartItem
| ველი        | ტიპი         | აღწერა                          |
|-------------|--------------|---------------------------------|
| id          | Integer (PK) |                                 |
| user_id     | Integer (FK) | → users.id                      |
| product_id  | Integer (FK) | → products.id                   |
| quantity    | Integer      | default=1, check > 0            |
| created_at  | DateTime     |                                 |

> **მინიშნება:** ერთ მომხმარებელს ერთი პროდუქტი კალათაში მხოლოდ ერთხელ უნდა ჰქონდეს (UniqueConstraint user_id + product_id).

### 2.5. Order
| ველი            | ტიპი            | აღწერა                                      |
|-----------------|-----------------|---------------------------------------------|
| id              | Integer (PK)    |                                             |
| user_id         | Integer (FK)    | → users.id                                  |
| status          | String(50)      | pending / paid / shipped / delivered / cancelled |
| total_amount    | Numeric(12, 2)  |                                             |
| shipping_address| Text            |                                             |
| created_at      | DateTime        |                                             |
| updated_at      | DateTime        |                                             |

### 2.6. OrderItem
| ველი        | ტიპი            | აღწერა                     |
|-------------|-----------------|----------------------------|
| id          | Integer (PK)    |                            |
| order_id    | Integer (FK)    | → orders.id                |
| product_id  | Integer (FK)    | → products.id              |
| quantity    | Integer         |                            |
| unit_price  | Numeric(10, 2)  | შეკვეთის მომენტის ფასი     |

---

## 3. API ენდპოინტები და ბიზნეს ლოგიკა

### 3.1. ავტორიზაცია (`/auth`)

| მეთოდ | გზა              | აღწერა                              | ავტორიზაცია |
|-------|------------------|-------------------------------------|-------------|
| POST  | /auth/register   | რეგისტრაცია                         | არა         |
| POST  | /auth/login      | ლოგინი → JWT ტოკენი                 | არა         |
| GET   | /auth/me         | მიმდინარე მომხმარებლის ინფორმაცია   | კი (JWT)    |

**ბიზნეს ლოგიკა და მინიშნებები:**
- ელფოსტა უნდა იყოს უნიკალური. თუ უკვე არსებობს → `400 Bad Request`.
- პაროლი ინახება მხოლოდ ჰეშირებული სახით (`passlib` + `bcrypt`).
- JWT ტოკენში ჩაწერეთ მინიმუმ: `sub` (user_id) და `is_admin`.
- ტოკენის ვადა: 30 წუთი (ან `.env`-დან).
- `/auth/me` აბრუნებს მხოლოდ აქტიურ მომხმარებელს (`is_active=True`).

---

### 3.2. პროდუქტები (`/products`)

| მეთოდ | გზა                        | აღწერა                                      | ავტორიზაცია     |
|-------|----------------------------|---------------------------------------------|-----------------|
| GET   | /products                  | ყველა პროდუქტი (ფილტრაცია + პაგინაცია)      | არა             |
| GET   | /products/{id}             | ერთი პროდუქტი                               | არა             |
| GET   | /products/slug/{slug}      | პროდუქტი slug-ით                            | არა             |
| POST  | /products                  | ახალი პროდუქტი                              | მხოლოდ Admin    |
| PUT   | /products/{id}             | განახლება                                   | მხოლოდ Admin    |
| DELETE| /products/{id}             | წაშლა (soft delete – is_active=False)       | მხოლოდ Admin    |

**ბიზნეს ლოგიკა:**

- **გამოჩენა მომხმარებლისთვის:**  
  ჩვეულებრივი მომხმარებელი ხედავს მხოლოდ `is_active=True` პროდუქტებს.  
  ადმინისტრატორს შეუძლია ნახოს ყველა პროდუქტი (აქტიური + არააქტიური).

- **ფილტრაცია და პაგინაცია (`GET /products`):**
  - `search` — ეძებს როგორც სახელში, ასევე აღწერაში (case-insensitive).
  - `category_id` — კონკრეტული კატეგორიის პროდუქტები.
  - `min_price` / `max_price` — ფასის დიაპაზონი.
  - `in_stock=true` — მხოლოდ ის პროდუქტები, რომელთა `stock > 0`.
  - `page` და `page_size` — პაგინაცია (default: page=1, page_size=20).
  - `sort_by` + `order` — დალაგება (მაგ. `price_asc`, `created_at_desc`).

- **შექმნა / განახლება (Admin):**
  - `slug` უნდა იყოს უნიკალური. თუ არ მოგაწოდეს კლიენტი — დააგენერირეთ სახელიდან.
  - `price` არ შეიძლება იყოს უარყოფითი.
  - `stock` არ შეიძლება იყოს უარყოფითი.

- **წაშლა (Soft Delete):**
  - პროდუქტი ფიზიკურად არ იშლება.
  - უბრალოდ `is_active = False` ხდება.
  - უკვე შექმნილ შეკვეთებში ეს პროდუქტი რჩება (ისტორია არ უნდა დაიკარგოს).

#### პაგინაციის კოდის მაგალითი

ქვემოთ მოცემულია მარტივი და გასაგები მაგალითი, თუ როგორ შეიძლება პაგინაციის + ფილტრაციის იმპლემენტაცია.

**Schema (პაგინირებული პასუხისთვის):**

```python
# schemas/product.py
from pydantic import BaseModel
from typing import List, Optional

class ProductResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str]
    price: float
    stock: int
    category_id: int
    is_active: bool

    class Config:
        from_attributes = True


class PaginatedProductsResponse(BaseModel):
    items: List[ProductResponse]
    total: int          # სულ რამდენი ჩანაწერი მოიძებნა
    page: int
    page_size: int
    total_pages: int
```

**Router მაგალითი:**

```python
# routers/products.py
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from math import ceil

from app.database import get_db
from app.models.product import Product
from app.schemas.product import PaginatedProductsResponse, ProductResponse

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=PaginatedProductsResponse)
def get_products(
    page: int = Query(1, ge=1, description="გვერდის ნომერი"),
    page_size: int = Query(20, ge=1, le=100, description="ჩანაწერების რაოდენობა გვერდზე"),
    search: str | None = Query(None, description="ძებნა სახელსა და აღწერაში"),
    category_id: int | None = Query(None),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    in_stock: bool | None = Query(None),
    sort_by: str = Query("created_at", description="დალაგების ველი: price, name, created_at"),
    order: str = Query("desc", description="asc ან desc"),
    db: Session = Depends(get_db),
):
    query = db.query(Product).filter(Product.is_active == True)

    # ძებნა
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Product.name.ilike(search_term),
                Product.description.ilike(search_term)
            )
        )

    # კატეგორია
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)

    # ფასის დიაპაზონი
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    # მარაგში არსებული
    if in_stock is True:
        query = query.filter(Product.stock > 0)

    # დალაგება
    sort_column = {
        "price": Product.price,
        "name": Product.name,
        "created_at": Product.created_at,
    }.get(sort_by, Product.created_at)

    if order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # სულ ჩანაწერების რაოდენობა (პაგინაციამდე)
    total = query.count()

    # პაგინაცია
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    total_pages = ceil(total / page_size) if total > 0 else 0

    return PaginatedProductsResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
```

**მინიშნებები პაგინაციაზე:**
- `page` იწყება 1-დან (არა 0-დან).
- `offset = (page - 1) * page_size`
- ყოველთვის დააბრუნეთ `total` და `total_pages`, რომ frontend-მა იცოდეს რამდენი გვერდია.
- `page_size`-ზე სასურველია ლიმიტის დაწესება (მაგ. მაქსიმუმ 100), რომ ვერავინ გამოითხოვოს ძალიან დიდი მონაცემები ერთბაშად.

---

### 3.3. კატეგორიები (`/categories`)

| მეთოდ | გზა                  | აღწერა                    | ავტორიზაცია  |
|-------|----------------------|---------------------------|--------------|
| GET   | /categories          | ყველა აქტიური კატეგორია   | არა          |
| POST  | /categories          | ახალი კატეგორია           | Admin        |
| PUT   | /categories/{id}     | განახლება                 | Admin        |
| DELETE| /categories/{id}     | წაშლა                     | Admin        |

**ბიზნეს ლოგიკა:**
- ჩვეულებრივი მომხმარებელი ხედავს მხოლოდ `is_active=True` კატეგორიებს.
- კატეგორიის წაშლისას (ან `is_active=False`-ზე გადაყვანისას) რეკომენდებულია შეამოწმოთ, აქვს თუ არა მასთან დაკავშირებული პროდუქტები.  
  თუ აქვს — ან არ მისცეთ წაშლის უფლება, ან გააკეთოთ soft delete.

---

### 3.4. კალათა (`/cart`)

| მეთოდ | გზა                      | აღწერა                              | ავტორიზაცია |
|-------|--------------------------|-------------------------------------|-------------|
| GET   | /cart                    | მიმდინარე მომხმარებლის კალათა       | კი          |
| POST  | /cart/items              | პროდუქტის დამატება კალათაში         | კი          |
| PUT   | /cart/items/{item_id}    | რაოდენობის შეცვლა                   | კი          |
| DELETE| /cart/items/{item_id}    | პროდუქტის ამოღება კალათიდან         | კი          |
| DELETE| /cart                    | მთლიანი კალათის გასუფთავება         | კი          |

**დეტალური ბიზნეს ლოგიკა:**

#### პროდუქტის დამატება (`POST /cart/items`)
1. მომხმარებელი აგზავნის `product_id` და `quantity`.
2. შეამოწმეთ:
   - პროდუქტი არსებობს და `is_active=True`.
   - `quantity > 0`.
   - პროდუქტის `stock >= quantity` (არ შეიძლება მარაგზე მეტის დამატება).
3. თუ ეს პროდუქტი **უკვე არის** კალათაში:
   - გაზარდეთ არსებული `quantity` (ახალი რაოდენობა = ძველი + მოთხოვნილი).
   - კვლავ შეამოწმეთ, რომ საბოლოო რაოდენობა არ აღემატებოდეს `stock`-ს.
4. თუ პროდუქტი **არ არის** კალათაში:
   - შექმენით ახალი `CartItem`.
5. წარმატების შემთხვევაში დააბრუნეთ განახლებული კალათა ან დამატებული ელემენტი.

#### რაოდენობის შეცვლა (`PUT /cart/items/{item_id}`)
- მხოლოდ საკუთარი კალათის ელემენტის შეცვლა შეიძლება.
- ახალი `quantity` უნდა იყოს > 0 და ≤ პროდუქტის მიმდინარე `stock`.
- თუ `quantity = 0` გააგზავნეს — უმჯობესია წაშალოთ ელემენტი კალათიდან.

#### წაშლა
- მომხმარებელს შეუძლია წაშალოს მხოლოდ საკუთარი კალათის ელემენტები.
- მთლიანი კალათის გასუფთავება (`DELETE /cart`) წაშლის ყველა `CartItem`-ს მოცემული მომხმარებლისთვის.

#### დამატებითი წესები
- კალათაში მხოლოდ `is_active=True` პროდუქტები შეიძლება იყოს.
- თუ პროდუქტი მოგვიანებით გახდა არააქტიური, კალათიდან მისი ამოღება ან შეცდომის დაბრუნება რეკომენდებულია შეკვეთის გაფორმებისას.

---

### 3.5. შეკვეთები (`/orders`)

| მეთოდ | გზა                      | აღწერა                                      | ავტორიზაცია |
|-------|--------------------------|---------------------------------------------|-------------|
| POST  | /orders                  | შეკვეთის გაფორმება (კალათიდან)              | კი          |
| GET   | /orders                  | მომხმარებლის შეკვეთების ისტორია             | კი          |
| GET   | /orders/{id}             | კონკრეტული შეკვეთის დეტალები                | კი (მხოლოდ საკუთარი) |
| PATCH | /orders/{id}/cancel      | შეკვეთის გაუქმება (მხოლოდ pending სტატუსზე) | კი          |

**დეტალური ბიზნეს ლოგიკა — შეკვეთის გაფორმება (`POST /orders`):**

ეს არის პროექტის ერთ-ერთი ყველაზე მნიშვნელოვანი ნაწილი. ყველა ქმედება **ერთ ტრანზაქციაში** უნდა შესრულდეს.

1. **კალათის წაკითხვა**  
   წაიკითხეთ მიმდინარე მომხმარებლის ყველა `CartItem`.  
   თუ კალათა ცარიელია → `400 Bad Request`.

2. **პროდუქტების და მარაგის შემოწმება**  
   თითოეული კალათის ელემენტისთვის:
   - პროდუქტი ჯერ კიდევ არსებობს და `is_active=True`.
   - `product.stock >= cart_item.quantity`.  
   თუ რომელიმე პირობა არ სრულდება → ტრანზაქცია გაუქმდება და დაბრუნდება შესაბამისი შეცდომა.

3. **Order-ის შექმნა**
   - `user_id` = მიმდინარე მომხმარებელი
   - `status` = `"pending"`
   - `total_amount` = ყველა (unit_price × quantity)-ის ჯამი
   - `shipping_address` მოდის request body-დან

4. **OrderItem-ების შექმნა**
   - თითოეული კალათის ელემენტისთვის იქმნება `OrderItem`.
   - `unit_price` = პროდუქტის **მიმდინარე** ფასი (არა კალათაში შენახული, რადგან კალათაში ფასი არ გვაქვს).
   - ეს მნიშვნელოვანია, რადგან პროდუქტის ფასი მომავალში შეიძლება შეიცვალოს, მაგრამ შეკვეთაში ძველი ფასი უნდა დარჩეს.

5. **მარაგის შემცირება**
   - თითოეული პროდუქტის `stock`-იდან აკლდება შეკვეთილი რაოდენობა.

6. **კალათის გასუფთავება**
   - მომხმარებლის ყველა `CartItem` იშლება.

7. **ტრანზაქციის დასრულება**
   - თუ ყველაფერი წარმატებით შესრულდა → `commit`.
   - ნებისმიერი შეცდომის შემთხვევაში → `rollback`.

8. **BackgroundTasks**
   - ტრანზაქციის წარმატების შემდეგ გაუშვით ფონური დავალება (იხ. სექცია 5).

**შეკვეთის გაუქმება (`PATCH /orders/{id}/cancel`):**
- მხოლოდ საკუთარი შეკვეთის გაუქმება შეიძლება.
- მხოლოდ `status = "pending"` შეკვეთის გაუქმებაა შესაძლებელი.
- გაუქმებისას:
  - `status` ხდება `"cancelled"`.
  - **რეკომენდებულია** პროდუქტების `stock`-ის დაბრუნება (შეკვეთილი რაოდენობების დამატება უკან).

**შეკვეთების ნახვა:**
- მომხმარებელი ხედავს მხოლოდ საკუთარ შეკვეთებს.
- `GET /orders/{id}`-ზე თუ შეკვეთა სხვა მომხმარებლისაა → `403 Forbidden` ან `404 Not Found`.

---

### 3.6. ადმინისტრატორის ენდპოინტები (`/admin`)

| მეთოდ | გზა                              | აღწერა                              |
|-------|----------------------------------|-------------------------------------|
| GET   | /admin/orders                    | ყველა შეკვეთა (ფილტრაცია სტატუსით)  |
| PATCH | /admin/orders/{id}/status        | შეკვეთის სტატუსის შეცვლა            |
| GET   | /admin/stats                     | სტატისტიკა (შეკვეთების რაოდენობა, შემოსავალი და ა.შ.) |

**ბიზნეს ლოგიკა:**

- მხოლოდ `is_admin=True` მომხმარებელს აქვს წვდომა.
- **სტატუსის შეცვლა:**  
  ადმინისტრატორს შეუძლია შეცვალოს სტატუსი ნებისმიერ ვალიდურ მნიშვნელობაზე  
  (`pending`, `paid`, `shipped`, `delivered`, `cancelled`).  
  რეკომენდებულია გარკვეული ლოგიკის დაცვა (მაგ. `delivered`-დან უკან დაბრუნება არასასურველია).

- **სტატისტიკა (`/admin/stats`)** — მაგალითები რა შეიძლება დაბრუნდეს:
  - სულ შეკვეთების რაოდენობა
  - შეკვეთები სტატუსების მიხედვით
  - ჯამური შემოსავალი (`total_amount`-ების ჯამი, მხოლოდ არა-გაუქმებული შეკვეთებიდან)
  - ბოლო 7/30 დღის შეკვეთები და ა.შ.

---

## 4. BackgroundTasks-ის გამოყენება

BackgroundTasks გამოიყენეთ შეკვეთის წარმატებით გაფორმების შემდეგ მარტივი ფონური დავალების გასაშვებად.

**რა უნდა გააკეთოთ:**

როცა `POST /orders` წარმატებით შესრულდება, BackgroundTasks-ით გაუშვით ფუნქცია, რომელიც **კონსოლში დაბეჭდავს** შეკვეთის ინფორმაციას.

### მაგალითი

**1. შექმენით ფაილი `services/notification_service.py`:**

```python
from datetime import datetime

def notify_order_created(order_id: int, user_email: str, total_amount: float):
    """
    ფონური დავალება.
    უბრალოდ ბეჭდავს ინფორმაციას კონსოლში.
    """
    print("=" * 50)
    print(f"შეკვეთა მიღებულია!")
    print(f"დრო: {datetime.now()}")
    print(f"Order ID: {order_id}")
    print(f"მომხმარებელი: {user_email}")
    print(f"თანხა: {total_amount} GEL")
    print("=" * 50)
```

**2. Router-ში გამოყენება (`routers/orders.py`):**

```python
from fastapi import BackgroundTasks
from app.services.notification_service import notify_order_created

@router.post("/orders")
def create_order(
    order_data: OrderCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # ... აქ არის შეკვეთის შექმნის მთელი ლოგიკა ...

    # ფონური დავალების დამატება (response-ის დაბრუნებამდე)
    background_tasks.add_task(
        notify_order_created,
        order_id=new_order.id,
        user_email=current_user.email,
        total_amount=float(new_order.total_amount)
    )

    return new_order
```

### მნიშვნელოვანი მინიშნებები:

- `BackgroundTasks` არის FastAPI-ის ჩაშენებული შესაძლებლობა.
- `add_task()`-ის შემდეგ ფუნქცია **response-ის გაგზავნის შემდეგ** გაეშვება.
- სტუდენტებმა **არ უნდა** გამოიყენონ რეალური ელფოსტა ან რთული ლოგირების ბიბლიოთეკები.
- საკმარისია უბრალო `print()`.

---

## 5. უსაფრთხოება და დამოკიდებულებები

### 5.1. JWT ავტორიზაცია
- `HTTPBearer`
- `get_current_user` dependency
- `get_current_active_user`
- `get_current_admin_user` (is_admin=True შემოწმება)

### 5.2. პაროლები
- გამოიყენეთ `passlib[bcrypt]`
- არასოდეს შეინახოთ plain text პაროლი

### 5.3. CORS
დაუშვით frontend-ისთვის საჭირო origin-ები (development-ისთვის `*`).

---

## 6. კონფიგურაცია (.env)

```env
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/ecommerce_db
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=1
```