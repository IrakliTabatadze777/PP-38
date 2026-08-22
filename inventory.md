# პროექტი: InventoryPro — საწყობისა და ინვენტარის მართვა

## 1. პროექტის მიზანი

შექმენით სრულფასოვანი **Backend API** საწყობისა და ინვენტარის მართვის სისტემისთვის (InventoryPro), რომელიც საშუალებას მისცემს:

- პროდუქტებისა და კატეგორიების მართვას
- მარაგების (stock) კონტროლს
- მარაგის მოძრაობების რეგისტრაციას (შემოსვლა, გასვლა, კორექტირება)
- დაბალი მარაგის ავტომატურ შეტყობინებებს
- მომხმარებლების როლების მიხედვით წვდომის კონტროლს

**როლები და უფლებები:**

| როლი     | უფლებები                                                                 |
|----------|--------------------------------------------------------------------------|
| Staff    | მარაგის მოძრაობების რეგისტრაცია, პროდუქტების ნახვა                       |
| Manager  | პროდუქტებისა და კატეგორიების სრული მართვა + მოძრაობები                   |
| Admin    | სრული წვდომა + მომხმარებლების მართვა                                     |

ტექნოლოგიები:
- **FastAPI**
- **PostgreSQL**
- **SQLAlchemy 2.0** + **Alembic**
- **Pydantic v2**
- **JWT** ავტორიზაცია
- **passlib** + **bcrypt**
- **BackgroundTasks** (დაბალი მარაგის შეტყობინებებისთვის)

---

## 3. მონაცემთა ბაზის მოდელები (SQLAlchemy)

### 3.1. User
| ველი              | ტიპი          | აღწერა                                      |
|-------------------|---------------|---------------------------------------------|
| id                | Integer (PK)  |                                             |
| email             | String(255)   | უნიკალური, indexed                          |
| full_name         | String(150)   |                                             |
| hashed_password   | String        |                                             |
| role              | String(20)    | staff / manager / admin (default: staff)    |
| is_active         | Boolean       | default=True                                |
| created_at        | DateTime      | server_default=now()                        |
| updated_at        | DateTime      | onupdate=now()                              |

### 3.2. Category
| ველი        | ტიპი          | აღწერა                     |
|-------------|---------------|----------------------------|
| id          | Integer (PK)  |                            |
| name        | String(100)   | უნიკალური                  |
| description | Text          | nullable                   |
| is_active   | Boolean       | default=True               |

### 3.3. Product
| ველი              | ტიპი            | აღწერა                              |
|-------------------|-----------------|-------------------------------------|
| id                | Integer (PK)    |                                     |
| name              | String(200)     |                                     |
| sku               | String(50)      | უნიკალური, indexed (პროდუქტის კოდი) |
| description       | Text            | nullable                            |
| category_id       | Integer (FK)    | → categories.id                     |
| unit              | String(20)      | ცალი, კგ, ლიტრი და ა.შ.             |
| current_stock     | Integer         | default=0                           |
| min_stock_level   | Integer         | default=5 (დაბალი მარაგის ზღვარი)   |
| price             | Numeric(10, 2)  | nullable                            |
| is_active         | Boolean         | default=True                        |
| created_at        | DateTime        |                                     |
| updated_at        | DateTime        |                                     |

### 3.4. StockMovement
| ველი            | ტიპი            | აღწერა                                      |
|-----------------|-----------------|---------------------------------------------|
| id              | Integer (PK)    |                                             |
| product_id      | Integer (FK)    | → products.id                               |
| movement_type   | String(20)      | in / out / adjustment                       |
| quantity        | Integer         | ყოველთვის დადებითი რიცხვი                   |
| previous_stock  | Integer         | მოძრაობამდე არსებული მარაგი                 |
| new_stock       | Integer         | მოძრაობის შემდეგ არსებული მარაგი            |
| reason          | String(255)     | nullable (მიზეზი / კომენტარი)               |
| performed_by    | Integer (FK)    | → users.id                                  |
| created_at      | DateTime        | server_default=now()                        |

> **მნიშვნელოვანი:**  
> `current_stock` პროდუქტზე ყოველთვის უნდა შეესაბამებოდეს ბოლო `StockMovement`-ის `new_stock`-ს.  
> ყველა მოძრაობა **ტრანზაქციაში** უნდა შესრულდეს.

---

## 4. API ენდპოინტები და ბიზნეს ლოგიკა

### 4.1. ავტორიზაცია (`/auth`)

| მეთოდ | გზა              | აღწერა                              | ავტორიზაცია |
|-------|------------------|-------------------------------------|-------------|
| POST  | /auth/register   | რეგისტრაცია (default role: staff)   | არა         |
| POST  | /auth/login      | ლოგინი → JWT ტოკენი                 | არა         |
| GET   | /auth/me         | მიმდინარე მომხმარებლის ინფორმაცია   | კი          |

**ბიზნეს ლოგიკა:**
- რეგისტრაციისას როლი ავტომატურად არის `staff`.
- მხოლოდ Admin-ს შეუძლია მომხმარებლის როლის შეცვლა.
- JWT-ში ჩაწერეთ: `sub` (user_id) და `role`.

---

### 4.2. კატეგორიები (`/categories`)

| მეთოდ | გზა                  | აღწერა                    | ავტორიზაცია     |
|-------|----------------------|---------------------------|-----------------|
| GET   | /categories          | ყველა აქტიური კატეგორია   | კი              |
| POST  | /categories          | ახალი კატეგორია           | Manager / Admin |
| PUT   | /categories/{id}     | განახლება                 | Manager / Admin |
| DELETE| /categories/{id}     | წაშლა (soft delete)       | Admin           |

---

### 4.3. პროდუქტები (`/products`)

| მეთოდ | გზა                        | აღწერა                                      | ავტორიზაცია     |
|-------|----------------------------|---------------------------------------------|-----------------|
| GET   | /products                  | პროდუქტების სია (ფილტრაცია + პაგინაცია)     | კი              |
| GET   | /products/{id}             | ერთი პროდუქტი                               | კი              |
| GET   | /products/sku/{sku}        | პროდუქტი SKU-ით                             | კი              |
| POST  | /products                  | ახალი პროდუქტი                              | Manager / Admin |
| PUT   | /products/{id}             | განახლება                                   | Manager / Admin |
| DELETE| /products/{id}             | წაშლა (soft delete – is_active=False)       | Admin           |
| GET   | /products/low-stock        | დაბალი მარაგის პროდუქტები                   | კი              |

**ბიზნეს ლოგიკა:**

- **ფილტრაცია და პაგინაცია:**
  - `search` — სახელში ან SKU-ში ძებნა
  - `category_id`
  - `low_stock=true` — მხოლოდ ის პროდუქტები, სადაც `current_stock <= min_stock_level`
  - `is_active`
  - `page`, `page_size`
  - `sort_by` (name, current_stock, created_at) + `order`

- **პროდუქტის შექმნა:**
  - `sku` უნდა იყოს უნიკალური.
  - `current_stock` საწყისად შეიძლება იყოს 0 ან მითითებული მნიშვნელობა.
  - თუ საწყისი მარაგი > 0, რეკომენდებულია პირველი `StockMovement` (type=`in`) ავტომატურად შეიქმნას.

- **განახლება:**
  - `current_stock`-ის პირდაპირ შეცვლა **აკრძალულია**.  
    მარაგი იცვლება მხოლოდ `StockMovement`-ის მეშვეობით.

- **დაბალი მარაგის სია (`/products/low-stock`):**
  - აბრუნებს ყველა პროდუქტს, სადაც `current_stock <= min_stock_level` და `is_active=True`.

---

### 4.4. მარაგის მოძრაობები (`/movements`)

| მეთოდ | გზა                        | აღწერა                                      | ავტორიზაცია     |
|-------|----------------------------|---------------------------------------------|-----------------|
| GET   | /movements                 | მოძრაობების ისტორია (ფილტრაცია + პაგინაცია) | კი              |
| GET   | /movements/{id}            | ერთი მოძრაობის დეტალები                     | კი              |
| POST  | /movements                 | ახალი მოძრაობის რეგისტრაცია                 | Staff და ზემოთ  |
| GET   | /products/{id}/movements   | კონკრეტული პროდუქტის მოძრაობები             | კი              |

**დეტალური ბიზნეს ლოგიკა — მოძრაობის რეგისტრაცია (`POST /movements`):**

ეს არის სისტემის ყველაზე მნიშვნელოვანი ნაწილი. ყველა ქმედება **ერთ ტრანზაქციაში** უნდა შესრულდეს.

1. **მოთხოვნის მონაცემები:**
   - `product_id`
   - `movement_type`: `in` | `out` | `adjustment`
   - `quantity` (ყოველთვის დადებითი რიცხვი)
   - `reason` (ოფციონალური)

2. **შემოწმებები:**
   - პროდუქტი არსებობს და `is_active=True`.
   - `quantity > 0`.

3. **მარაგის გამოთვლა:**
   - `previous_stock` = პროდუქტის მიმდინარე `current_stock`
   - თუ `movement_type == "in"` → `new_stock = previous_stock + quantity`
   - თუ `movement_type == "out"` → `new_stock = previous_stock - quantity`
   - თუ `movement_type == "adjustment"` → `new_stock = quantity` (პირდაპირ დაყენება)

4. **ვალიდაცია:**
   - `out` ტიპის მოძრაობისას `new_stock` არ შეიძლება იყოს უარყოფითი → `400 Bad Request`.

5. **ჩანაწერების შექმნა (ტრანზაქციაში):**
   - იქმნება `StockMovement` ჩანაწერი (`previous_stock`, `new_stock`, `performed_by` და სხვა ველებით).
   - პროდუქტის `current_stock` ახლდება `new_stock`-ით.

6. **დაბალი მარაგის შემოწმება (BackgroundTasks):**
   - თუ განახლების შემდეგ `current_stock <= min_stock_level`, გაუშვით ფონური შეტყობინება (იხ. სექცია 5).

**მოძრაობების ფილტრაცია (`GET /movements`):**
- `product_id`
- `movement_type`
- `performed_by`
- `date_from` / `date_to`
- `page`, `page_size`

---

### 4.5. ადმინისტრაცია (`/admin`)

| მეთოდ | გზა                              | აღწერა                              |
|-------|----------------------------------|-------------------------------------|
| GET   | /admin/users                     | ყველა მომხმარებელი                  |
| PATCH | /admin/users/{id}/role           | როლის შეცვლა                        |
| PATCH | /admin/users/{id}/status         | მომხმარებლის დაბლოკვა/გააქტიურება   |
| GET   | /admin/stats                     | სტატისტიკა                          |

**სტატისტიკის მაგალითები:**
- სულ პროდუქტების რაოდენობა
- დაბალი მარაგის პროდუქტების რაოდენობა
- დღიური/ყოველკვირეული მოძრაობების რაოდენობა
- ყველაზე მოძრავი პროდუქტები

---

## 5. BackgroundTasks-ის გამოყენება

BackgroundTasks გამოიყენეთ **დაბალი მარაგის შეტყობინებისთვის**.

**როდის გაეშვას:**
როცა `StockMovement`-ის შემდეგ პროდუქტის `current_stock <= min_stock_level` გახდება.

### მაგალითი

**`services/notification_service.py`:**

```python
from datetime import datetime

def notify_low_stock(product_id: int, product_name: str, sku: str, current_stock: int, min_stock_level: int):
    """
    ფონური დავალება — დაბალი მარაგის შეტყობინება.
    """
    print("=" * 60)
    print(f"⚠ დაბალი მარაგის გაფრთხილება!")
    print(f"დრო: {datetime.now()}")
    print(f"პროდუქტი: {product_name} (SKU: {sku})")
    print(f"მიმდინარე მარაგი: {current_stock}")
    print(f"მინიმალური ზღვარი: {min_stock_level}")
    print("=" * 60)
```

**გამოყენება მოძრაობის რეგისტრაციისას:**

```python
@router.post("/movements")
def create_movement(
    movement_data: StockMovementCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # ... ტრანზაქციაში მოძრაობის შექმნა და current_stock-ის განახლება ...

    # დაბალი მარაგის შემოწმება
    if product.current_stock <= product.min_stock_level:
        background_tasks.add_task(
            notify_low_stock,
            product_id=product.id,
            product_name=product.name,
            sku=product.sku,
            current_stock=product.current_stock,
            min_stock_level=product.min_stock_level,
        )

    return new_movement
```

**მინიშნებები:**
- მხოლოდ `print()` გამოიყენეთ.
- შეტყობინება უნდა გაეშვას მხოლოდ მაშინ, როცა მარაგი ზღვარს ქვემოთ ჩამოვა (ან ზღვარზეა).

---

## 6. უსაფრთხოება და დამოკიდებულებები

### 6.1. როლებზე დაფუძნებული წვდომა
შექმენით dependency-ები:
- `get_current_user`
- `get_current_active_user`
- `require_staff_or_above`
- `require_manager_or_above`
- `require_admin`

### 6.2. პაროლები
- გამოიყენეთ `passlib[bcrypt]`
- plain text პაროლი არასოდეს შეინახოთ.

### 6.3. CORS
დაუშვით საჭირო origin-ები (development-ისთვის `*`).

---

## 7. კონფიგურაცია (.env)

```env
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/inventorypro_db
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=1
```