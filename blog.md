# პროექტი: BlogForge — ბლოგის პლატფორმა

## 1. პროექტის მიზანი

შექმენით სრულფასოვანი **Backend API** ბლოგის პლატფორმისთვის (BlogForge), რომელიც საშუალებას მისცემს მომხმარებლებს:

- რეგისტრაცია და ავტორიზაცია
- სხვადასხვა როლების მიხედვით მოქმედება (Admin, Editor, Author, Reader)
- პოსტების შექმნა, რედაქტირება, წაშლა და გამოქვეყნება
- კომენტარების დამატება და მართვა
- მოდერაცია (პოსტებისა და კომენტარების დამტკიცება/უარყოფა)
- კატეგორიებისა და თეგების გამოყენება
- პოსტების ძებნა, ფილტრაცია და პაგინაცია

**როლები და უფლებები:**

| როლი     | უფლებები                                                                 |
|----------|--------------------------------------------------------------------------|
| Reader   | პოსტების კითხვა, კომენტარის დამატება                                     |
| Author   | საკუთარი პოსტების შექმნა / რედაქტირება / წაშლა, კომენტარების დამატება   |
| Editor   | ყველა პოსტის რედაქტირება, მოდერაცია (პოსტები + კომენტარები)             |
| Admin    | სრული წვდომა + მომხმარებლებისა და როლების მართვა                         |

ტექნოლოგიები:
- **FastAPI**
- **PostgreSQL**
- **SQLAlchemy 2.0** + **Alembic**
- **Pydantic v2**
- **JWT** ავტორიზაცია
- **passlib** + **bcrypt**
- **BackgroundTasks**


---

## 2. მონაცემთა ბაზის მოდელები (SQLAlchemy)

### 2.1. User
| ველი              | ტიპი          | აღწერა                                      |
|-------------------|---------------|---------------------------------------------|
| id                | Integer (PK)  |                                             |
| email             | String(255)   | უნიკალური, indexed                          |
| username          | String(50)    | უნიკალური, indexed                          |
| hashed_password   | String        |                                             |
| full_name         | String(150)   | nullable                                    |
| role              | String(20)    | reader / author / editor / admin (default: reader) |
| is_active         | Boolean       | default=True                                |
| created_at        | DateTime      | server_default=now()                        |
| updated_at        | DateTime      | onupdate=now()                              |

### 2.2. Category
| ველი        | ტიპი          | აღწერა                     |
|-------------|---------------|----------------------------|
| id          | Integer (PK)  |                            |
| name        | String(100)   | უნიკალური                  |
| slug        | String(120)   | უნიკალური, indexed         |
| description | Text          | nullable                   |

### 2.3. Tag
| ველი   | ტიპი          | აღწერა              |
|--------|---------------|---------------------|
| id     | Integer (PK)  |                     |
| name   | String(50)    | უნიკალური           |
| slug   | String(60)    | უნიკალური, indexed  |

### 2.4. Post
| ველი            | ტიპი            | აღწერა                                      |
|-----------------|-----------------|---------------------------------------------|
| id              | Integer (PK)    |                                             |
| title           | String(255)     |                                             |
| slug            | String(300)     | უნიკალური, indexed                          |
| content         | Text            |                                             |
| excerpt         | String(500)     | nullable (მოკლე აღწერა)                     |
| status          | String(20)      | draft / pending / published / rejected      |
| author_id       | Integer (FK)    | → users.id                                  |
| category_id     | Integer (FK)    | → categories.id (nullable)                  |
| views_count     | Integer         | default=0                                   |
| created_at      | DateTime        |                                             |
| updated_at      | DateTime        |                                             |
| published_at    | DateTime        | nullable                                    |

> **მინიშნება:** Post და Tag შორის Many-to-Many კავშირი (association table: `post_tags`).

### 2.5. Comment
| ველი        | ტიპი          | აღწერა                              |
|-------------|---------------|-------------------------------------|
| id          | Integer (PK)  |                                     |
| content     | Text          |                                     |
| post_id     | Integer (FK)  | → posts.id                          |
| author_id   | Integer (FK)  | → users.id                          |
| parent_id   | Integer (FK)  | → comments.id (nullable) — პასუხები |
| status      | String(20)    | pending / approved / rejected       |
| created_at  | DateTime      |                                     |
| updated_at  | DateTime      |                                     |

---

## 3. API ენდპოინტები და ბიზნეს ლოგიკა

### 3.1. ავტორიზაცია (`/auth`)

| მეთოდ | გზა              | აღწერა                              | ავტორიზაცია |
|-------|------------------|-------------------------------------|-------------|
| POST  | /auth/register   | რეგისტრაცია (default role: reader)  | არა         |
| POST  | /auth/login      | ლოგინი → JWT ტოკენი                 | არა         |
| GET   | /auth/me         | მიმდინარე მომხმარებლის ინფორმაცია   | კი          |

**ბიზნეს ლოგიკა:**
- რეგისტრაციისას როლი ავტომატურად არის `reader`.
- მხოლოდ Admin-ს შეუძლია მომხმარებლის როლის შეცვლა.
- JWT-ში ჩაწერეთ: `sub` (user_id), `role`, `username`.

---

### 3.2. პოსტები (`/posts`)

| მეთოდ | გზა                        | აღწერა                                      | ავტორიზაცია          |
|-------|----------------------------|---------------------------------------------|----------------------|
| GET   | /posts                     | გამოქვეყნებული პოსტები (ფილტრაცია+პაგინაცია)| არა                  |
| GET   | /posts/{id}                | ერთი პოსტი                                  | არა                  |
| GET   | /posts/slug/{slug}         | პოსტი slug-ით                               | არა                  |
| POST  | /posts                     | ახალი პოსტის შექმნა                         | Author და ზემოთ      |
| PUT   | /posts/{id}                | პოსტის განახლება                            | Author (საკუთარი) / Editor / Admin |
| DELETE| /posts/{id}                | პოსტის წაშლა                                | Author (საკუთარი) / Editor / Admin |
| GET   | /posts/my                  | ჩემი პოსტები (ყველა სტატუსით)               | Author და ზემოთ      |
| PATCH | /posts/{id}/submit         | დრაფტის გაგზავნა მოდერაციაზე (pending)      | Author               |

**დეტალური ბიზნეს ლოგიკა:**

#### პოსტის შექმნა (`POST /posts`)
- მხოლოდ `author`, `editor`, `admin` როლის მომხმარებელს შეუძლია.
- საწყისი სტატუსი: `draft`.
- `slug` უნდა იყოს უნიკალური. თუ არ მოგაწოდეს — დააგენერირეთ title-დან.
- Author-ს შეუძლია მხოლოდ საკუთარი პოსტების შექმნა.

#### პოსტის განახლება
- **Author** — მხოლოდ საკუთარ პოსტს და მხოლოდ მაშინ, თუ სტატუსი არის `draft` ან `rejected`.
- **Editor / Admin** — ნებისმიერ პოსტს, ნებისმიერ სტატუსში.

#### გამოქვეყნება და მოდერაცია
- Author აგზავნის პოსტს მოდერაციაზე (`status = pending`).
- Editor ან Admin ამტკიცებს (`published`) ან უარყოფს (`rejected`).
- მხოლოდ `published` სტატუსის პოსტები ჩანს საჯაროდ (`GET /posts`).
- `published_at` ივსება მხოლოდ გამოქვეყნების მომენტში.

#### ფილტრაცია და პაგინაცია (`GET /posts`)
- მხოლოდ `status = published` პოსტები.
- პარამეტრები:
  - `search` — title და content-ში ძებნა
  - `category_id`
  - `tag` (slug ან id)
  - `author_id`
  - `page`, `page_size`
  - `sort_by` (created_at, published_at, views_count, title) + `order`

#### პაგინაციის მაგალითი (მსგავსი წინა პროექტისა)

```python
@router.get("", response_model=PaginatedPostsResponse)
def get_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    search: str | None = None,
    category_id: int | None = None,
    tag: str | None = None,
    author_id: int | None = None,
    sort_by: str = "published_at",
    order: str = "desc",
    db: Session = Depends(get_db),
):
    query = db.query(Post).filter(Post.status == "published")

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(Post.title.ilike(search_term), Post.content.ilike(search_term))
        )

    if category_id:
        query = query.filter(Post.category_id == category_id)

    if author_id:
        query = query.filter(Post.author_id == author_id)

    # თეგით ფილტრაცია (Many-to-Many)
    if tag:
        query = query.join(Post.tags).filter(Tag.slug == tag)

    # დალაგება
    sort_column = {
        "published_at": Post.published_at,
        "created_at": Post.created_at,
        "views_count": Post.views_count,
        "title": Post.title,
    }.get(sort_by, Post.published_at)

    query = query.order_by(sort_column.asc() if order == "asc" else sort_column.desc())

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    total_pages = ceil(total / page_size) if total > 0 else 0

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }
```

---

### 3.3. კომენტარები (`/comments`)

| მეთოდ | გზა                              | აღწერა                              | ავტორიზაცია     |
|-------|----------------------------------|-------------------------------------|-----------------|
| GET   | /posts/{post_id}/comments        | პოსტის დამტკიცებული კომენტარები     | არა             |
| POST  | /posts/{post_id}/comments        | კომენტარის დამატება                 | კი (ნებისმიერი ავტორიზებული) |
| PUT   | /comments/{id}                   | კომენტარის რედაქტირება              | Author (საკუთარი) |
| DELETE| /comments/{id}                   | კომენტარის წაშლა                    | Author (საკუთარი) / Editor / Admin |
| GET   | /comments/pending                | მოდერაციის მოლოდინში მყოფი          | Editor / Admin  |
| PATCH | /comments/{id}/moderate          | კომენტარის დამტკიცება/უარყოფა       | Editor / Admin  |

**დეტალური ბიზნეს ლოგიკა:**

#### კომენტარის დამატება
- ნებისმიერ ავტორიზებულ მომხმარებელს შეუძლია.
- საწყისი სტატუსი: `pending` (მოდერაცია სავალდებულოა).
- შესაძლებელია პასუხის გაცემა (`parent_id`-ით).
- მხოლოდ `approved` კომენტარები ჩანს საჯაროდ.

#### მოდერაცია
- Editor და Admin ამტკიცებენ ან უარყოფენ კომენტარებს.
- Author-ს არ აქვს მოდერაციის უფლება.

#### წაშლა / რედაქტირება
- კომენტარის ავტორს შეუძლია საკუთარი კომენტარის რედაქტირება და წაშლა (მხოლოდ `pending` ან `approved` სტატუსზე).
- Editor/Admin-ს შეუძლია ნებისმიერი კომენტარის წაშლა.

---

### 3.4. კატეგორიები და თეგები

**კატეგორიები (`/categories`)**

| მეთოდ | გზა                  | ავტორიზაცია     |
|-------|----------------------|-----------------|
| GET   | /categories          | არა             |
| POST  | /categories          | Editor / Admin  |
| PUT   | /categories/{id}     | Editor / Admin  |
| DELETE| /categories/{id}     | Admin           |

**თეგები (`/tags`)**

| მეთოდ | გზა             | ავტორიზაცია     |
|-------|-----------------|-----------------|
| GET   | /tags           | არა             |
| POST  | /tags           | Author და ზემოთ |
| DELETE| /tags/{id}      | Editor / Admin  |

---

### 3.5. ადმინისტრაცია (`/admin`)

| მეთოდ | გზა                              | აღწერა                              |
|-------|----------------------------------|-------------------------------------|
| GET   | /admin/users                     | ყველა მომხმარებელი                  |
| PATCH | /admin/users/{id}/role           | როლის შეცვლა                        |
| PATCH | /admin/users/{id}/status         | მომხმარებლის დაბლოკვა/გააქტიურება   |
| GET   | /admin/stats                     | სტატისტიკა                          |
| GET   | /admin/posts/pending             | მოდერაციის მოლოდინში მყოფი პოსტები  |
| PATCH | /admin/posts/{id}/moderate       | პოსტის დამტკიცება / უარყოფა         |

**ბიზნეს ლოგიკა:**
- მხოლოდ `admin` როლს აქვს წვდომა `/admin/users` ენდპოინტებზე.
- Editor-საც შეუძლია პოსტებისა და კომენტარების მოდერაცია.
- როლის შეცვლისას Admin ვერ შეცვლის საკუთარ როლს (დაცვა).

---

## 4. BackgroundTasks-ის გამოყენება

BackgroundTasks გამოიყენეთ მარტივი ფონური შეტყობინებისთვის.

**რეკომენდებული გამოყენება:**

როცა ახალი კომენტარი დაემატება პოსტს, BackgroundTasks-ით კონსოლში დაბეჭდეთ შეტყობინება.

### მაგალითი

**`services/notification_service.py`:**

```python
from datetime import datetime

def notify_new_comment(post_id: int, post_title: str, comment_author: str):
    """
    ფონური დავალება — ახალი კომენტარის შეტყობინება.
    """
    print("=" * 50)
    print(f"ახალი კომენტარი მიღებულია!")
    print(f"დრო: {datetime.now()}")
    print(f"პოსტი: #{post_id} — {post_title}")
    print(f"ავტორი: {comment_author}")
    print("=" * 50)
```

**გამოყენება კომენტარის შექმნისას:**

```python
@router.post("/posts/{post_id}/comments")
def create_comment(
    post_id: int,
    comment_data: CommentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # ... კომენტარის შექმნის ლოგიკა ...

    background_tasks.add_task(
        notify_new_comment,
        post_id=post.id,
        post_title=post.title,
        comment_author=current_user.username,
    )

    return new_comment
```

**მინიშნებები:**
- მხოლოდ `print()` გამოიყენეთ.
- რეალური ელფოსტა ან რთული ლოგირება არ არის საჭირო.

---

## 5. უსაფრთხოება და დამოკიდებულებები

### 5.1. როლებზე დაფუძნებული წვდომა
შექმენით dependency-ები:

- `get_current_user`
- `get_current_active_user`
- `require_role(["author", "editor", "admin"])`
- `require_author_or_above`
- `require_editor_or_above`
- `require_admin`

### 5.2. პაროლები
- გამოიყენეთ `passlib[bcrypt]`
- plain text პაროლი არასოდეს შეინახოთ.

### 5.3. CORS
დაუშვით საჭირო origin-ები (development-ისთვის `*`).

---

## 6. კონფიგურაცია (.env)

```env
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/blogforge_db
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=1
```