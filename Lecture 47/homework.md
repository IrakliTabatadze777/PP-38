# საშინაო დავალება — CORS და Middleware

## დავალება

წინა დავალებებში აწყობილ FastAPI პროექტს დაამატეთ **CORS** და
**middleware**-ები. ამ დავალებაში ფასდება middleware-ის სწორად ჩაშენება და
CORS-ის კონფიგურაცია — არსებული CRUD ან auth ლოგიკის სრულყოფა/გამოსწორება
სავალდებულო არ არის.

## რა უნდა დაამატოთ

### 1. CORS (`CORSMiddleware`)

`main.py`-ში დაამატეთ FastAPI-ს `CORSMiddleware`, რომ frontend-ს
(მაგ. `http://localhost:3000`) შეეძლოს API-სთან მოთხოვნების გაგზავნა.

მინიმუმ დააკონფიგურირეთ:

- `allow_origins` — კონკრეტული origin-ები (არა მხოლოდ `"*"`)
- `allow_credentials`
- `allow_methods`
- `allow_headers`

### 2. GZip Middleware (`GZipMiddleware`)

`main.py`-ში დაამატეთ Starlette/FastAPI-ს `GZipMiddleware`, რომ პასუხები
ავტომატურად იკუმშებოდეს gzip-ით, როცა კლიენტი ამას ითხოვს.



`minimum_size` განსაზღვრავს, რა ზომის პასუხიდან იწყება შეკუმშვა.

>გადახედეთ პრეზენტაციას!!

### 3. Correlation ID Middleware

შექმენით `core/middlewares.py` და მასში კლასი `CorrelationIDMiddleware`
(`BaseHTTPMiddleware`-ის საფუძველზე), რომელიც:

1. ყოველ მოთხოვნაზე ქმნის უნიკალურ ID-ს (`uuid`)
2. ინახავს მას `request.state`-ში (მაგ. `X-Correlation-ID`)
3. პასუხში ამატებს იმავე ID-ს header-ად (`X-Correlation-ID`)

ეს middleware დაარეგისტრირეთ `app.add_middleware(...)`-ით.
