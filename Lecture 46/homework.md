# საშინაო დავალება — აუთენტიფიკაცია და ავტორიზაცია

## დავალება

წინა დავალებაში აწყობილ FastAPI პროექტს დაამატეთ **აუთენტიფიკაცია** და
**ავტორიზაცია**. ზოგიერთი მისამართი ხელმისაწვდომი უნდა იყოს მხოლოდ
ავტორიზებული მომხმარებლისთვის, ზოგი კი — მხოლოდ კონკრეტული როლისთვის.

ბიზნეს ლოგიკა მარტივი დატოვეთ. მთავარი პრიორიტეტია auth-ის სწორად
ჩაშენება არსებულ სტრუქტურაში.

წინა დავალებაში აღწერილი CRUD ლოგიკის სრულყოფა/გამოსწორება სავალდებულო არ
არის — ამ დავალებაში ფასდება auth და endpoint-ების შეზღუდვა.

## რა უნდა დაამატოთ

### 1. `User` მოდელის გაფართოება

`User`-ს დაამატეთ:

- `hashed_password: str`
- `is_active: bool` (default: `True`)
- `role` — enum: `admin`, `customer` (default: `customer`)

### 2. უსაფრთხოების დამხმარე ფუნქციები (`core/security.py`)

- პაროლის hashing / verification (`bcrypt`)
- JWT access token-ის შექმნა და decode
- (სურვილისამებრ) refresh token

კონფიგურაცია (`SECRET_KEY`, `ALGORITHM`, token lifetime და ა.შ.) გამოიტანეთ
`core/config.py`-ში ან `.env`-ში — hardcoded მნიშვნელობები არ დატოვოთ.

### 3. Auth schemas და service / router

დაამატეთ:

- **schemas** — მაგ.: register request, login request, token response
- **`AuthService`** — register, login (და სურვილისამებრ refresh / logout)
- **`/auth` router** endpoint-ებით:
  - `POST /auth/register` — რეგისტრაცია (პაროლი უნდა შეინახოს hashed სახით)
  - `POST /auth/login` — აბრუნებს access token-ს (და სურვილისამებრ refresh-ს)
  - `GET /auth/me` — აბრუნებს მიმდინარე მომხმარებელს (აუთენტიფიკაცია სავალდებულოა)

შეინარჩუნეთ იგივე ფენები: `router → service → repository`.

### 4. Dependencies (`core/dependencies.py`)

გააკეთეთ dependency-ები, რომლებსაც router-ებში გამოიყენებთ:

- `get_current_user` — token-იდან იღებს მომხმარებელს; თუ token არასწორია /
  მომხმარებელი არ არსებობს → `401`
- `require_role(...)` — ამოწმებს მომხმარებლის როლს; თუ როლი არ ემთხვევა →
  `403`

## რომელი მისამართები როგორ შეზღუდოთ

| Endpoint | წვდომა |
|----------|--------|
| `POST /auth/register` | საჯარო |
| `POST /auth/login` | საჯარო |
| `GET /auth/me` | მხოლოდ აუთენტიფიცირებული |
| `GET /products/`, `GET /products/{id}` | საჯარო |
| `POST /products/`, `DELETE /products/{id}` | მხოლოდ `admin` |
| `GET /orders/`, `GET /orders/{id}` | აუთენტიფიცირებული |
| `POST /orders/` | აუთენტიფიცირებული |
| `DELETE /orders/{id}` | მხოლოდ `admin` |
| `GET /users/`, `GET /users/{id}` | მხოლოდ `admin` |
| `DELETE /users/{id}` | მხოლოდ `admin` |

შეზღუდვა გააკეთეთ `Depends(get_current_user)` ან
`Depends(require_role(...))`-ით — router-ში ხელით if/else ნუ დაწერთ.

## მოთხოვნები

- პაროლი ბაზაში არასდროს არ შეინახოს plain text-ად.
- დაცული endpoint-ზე token-ის გარეშე მოთხოვნა უნდა აბრუნებდეს `401`-ს.
- როლი არასწორი რომ იყოს — `403`-ს.
- auth-ის ლოგიკა არ უნდა იყოს router-ში; გამოიყენეთ service და dependency-ები.
