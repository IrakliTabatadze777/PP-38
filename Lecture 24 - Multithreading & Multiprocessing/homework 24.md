# საშინაო დავალება: პოსტების ანალიზი

## მიმოხილვა

შექმენი პროგრამა, რომელიც **ერთდროულად** ჩამოტვირთავს მომხმარებლების პოსტებს ინტერნეტიდან, შემდეგ კი **პარალელურად** დაამუშავებს მათ და ბეჭდავს შედეგს.

---

## კონტექსტი

შენი ამოცანაა: რამდენიმე მომხმარებლის პოსტები **ერთდროულად** ჩამოტვირთო, შემდეგ კი **პარალელურად** გაანალიზო და შეაჯამო.

---

## API

გამოიყენე უფასო სატესტო API — **JSONPlaceholder**.

პოსტების მისაღებად:
```
GET https://jsonplaceholder.typicode.com/posts?userId={ID}
```
სადაც `ID` არის მომხმარებლის უნიკალური იდენტიფიკატორი (1-დან 10-მდე), რომელმაც ატვირთა პოსტი.

response მაგალითი:
```json
[
  {
    "userId": 1,
    "id": 2,
    "title": "qui est esse",
    "body": "est rerum tempore vitae\nsequi sint nihil reprehenderit dolor beatae ea dolores neque\nfugiat blanditiis voluptate porro vel nihil molestiae ut reiciendis\nqui aperiam non debitis possimus qui neque nisi nulla"
  },
  ...
]
```

---

## რა უნდა გააკეთოს პროგრამამ

### ნაბიჯი 1 — ჩამოტვირთე პოსტები Threads-ით

- მომხმარებლების სია: `[1, 2, 3, 4, 5]`
- გამოიყენე **ThreadPoolExecutor** რათა **ყველა მომხმარებლის** მოთხოვნა ერთდროულად გაიგზავნოს
- შედეგები დააგროვე ლისტში

> 💡 **ThreadPoolExecutor-ის მინიშნება:**
> ```python
> from concurrent.futures import ThreadPoolExecutor
>
> with ThreadPoolExecutor(max_workers=5) as executor:
>     results = list(executor.map(fetch_posts, user_ids))
> ```

---

### ნაბიჯი 2 — დაამუშავე პოსტები Processes-ით

მას შემდეგ, რაც ყველა მომხმარებლის პოსტები ჩამოიტვირთება, გაუშვი **სამი ანალიზი პარალელურად** — თითო ცალკე პროცესში:

| ფუნქცია | რას აკეთებს |
|---|---|
| `count_posts(all_posts)` | დაითვალოს თითოეული მომხმარებლის პოსტების რაოდენობა |
| `find_longest_post(all_posts)` | იპოვოს ყველაზე გრძელი `body`-ს მქონე პოსტი |
| `average_title_length(all_posts)` | გამოიანგარიშოს სათაურების საშუალო სიგრძე (სიმბოლოებში) |

> 💡 **ProcessPoolExecutor-ის მინიშნება:**
> ```python
> from concurrent.futures import ProcessPoolExecutor
>
> with ProcessPoolExecutor() as executor:
>     f1 = executor.submit(task1, args)
>     f2 = executor.submit(task2, args)
>     f3 = executor.submit(task3, args)
>
>     task1_result  = f1.result()
>     task2_result  = f2.result()
>     task3_result  = f3.result()
> ```

---

### ნაბიჯი 3 — დაბეჭდე შედეგი
ფორმატი აირჩიეთ თქვენი სურვილისამებრ, მთავარია ყველანაირი ინფორმაცია იყოს დაბეჭდილი
```
========================================
        პოსტების ანალიზი
========================================
მომხმარებელი   პოსტების რაოდენობა
------------------------------------
User 1              10
User 2              10
User 3              10
User 4              10
User 5              10

ყველაზე გრძელი პოსტი:
  მომხმარებელი: User 3
  სათაური: "ea molestias quasi exercitationem..."
  სიგრძე: 234 სიმბოლო

სათაურების საშუალო სიგრძე: 49.2 სიმბოლო
========================================
```

---


> ⚠️ **მნიშვნელოვანი:** `if __name__ == "__main__":` **სავალდებულოა** `multiprocessing`-ის გამოყენებისას Windows-სა და macOS-ზე. მის გარეშე პროგრამა დაერორდება.

---



- **Thread** უნდა გამოიყენო ჩამოტვირთვისთვის
- **Process** უნდა გამოიყენო ანალიზისთვის
- **Timeout** — თუ მოთხოვნა 5 წამზე მეტს გრძელდება, გამოტოვე ის მომხმარებელი (`requests`-ს აქვს `timeout` პარამეტრი)

