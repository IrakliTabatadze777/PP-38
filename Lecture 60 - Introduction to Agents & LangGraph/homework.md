### ამოცანა 1 — ბლოგპოსტის მომზადება

შექმენით LangGraph pipeline, რომელიც იდეას ამუშავებს და საბოლოოდ აბრუნებს მზა ბლოგპოსტს.

**მოთხოვნები:**
- State-ში უნდა იყოს შემდეგი ველები: `raw_idea`, `cleaned_idea`, `expanded_content`, `final_post`
- 3 Node:
  1. `clean_idea` — LLM-ის გარეშე. ტექსტს გაასუფთავებს (`.strip()`, ზედმეტი ახალი ხაზების და მრავალჯერადი space-ების მოშორება)
  2. `expand_content` — LLM-ით გააფართოებს გასუფთავებულ იდეას სრულ და თანმიმდევრულ ტექსტად (მინიმუმ 4-6 წინადადება)
  3. `create_final_post` — LLM-ით დაამატებს სათაურს და მოკლე დასკვნას, რათა მიიღოს მზა ბლოგპოსტი
- სტრუქტურა: `START → clean_idea → expand_content → create_final_post → END`

**ტესტური შეყვანა:**
```
We spend too much time on our phones.   

It hurts our eyes
and also affects our sleep quality.
```

**მინიშნებები:**
1. State განსაზღვრეთ `TypedDict`-ით. ყველა ველი `str` ტიპის გააკეთეთ.
2. პირველ Node-ში (`clean_idea`) არ გამოიყენოთ LLM. მხოლოდ Python-ის სტრინგის მეთოდები. მაგალითი:
   ```python
   cleaned = state["raw_idea"].strip()
   cleaned = cleaned.replace("\n", " ")
   while "  " in cleaned:
       cleaned = cleaned.replace("  ", " ")
   ```
3. მეორე და მესამე Node-ში გამოიყენეთ `ChatGoogleGenerativeAI`.
4. პრომპტები გააკეთეთ კონკრეტული და მკაფიო.
5. თითოეულმა Node-მა დააბრუნოს მხოლოდ ის ველი, რომელსაც ის ცვლის.
6. საბოლოოდ `print(result["final_post"])`-ით შეამოწმეთ შედეგი.

---

### ამოცანა 2 — მომხმარებლის გამოხმაურების დამუშავება

შექმენით LangGraph pipeline, რომელიც მომხმარებლის გამოხმაურებას (feedback) ამუშავებს და საბოლოოდ აბრუნებს თავაზიან პასუხს.

**მოთხოვნები:**
- State-ში უნდა იყოს შემდეგი ველები: `feedback`, `main_issues`, `suggested_actions`, `final_reply`
- 3 Node:
  1. `extract_issues` — LLM-ით ამოიღებს გამოხმაურებიდან მთავარ პრობლემებს / საჩივრებს
  2. `suggest_actions` — LLM-ით სთავაზობს, რა გააკეთოს კომპანიამ ამ პრობლემების გადასაჭრელად
  3. `generate_reply` — LLM-ით ქმნის თავაზიან და პროფესიონალურ პასუხს მომხმარებლისთვის
- სტრუქტურა: `START → extract_issues → suggest_actions → generate_reply → END`
- ყველა Node-ში აუცილებლად გამოიყენეთ LLM

**ტესტური შეყვანა:**
```
The product arrived two days late and the packaging was completely damaged. I am very disappointed with the service.
```

**მინიშნებები:**
1. State განსაზღვრეთ `TypedDict`-ით. ყველა ველი `str` ტიპის გააკეთეთ.
2. თითოეულ Node-ში შექმენით `ChatGoogleGenerativeAI` ობიექტი (ან ერთი გლობალური).
3. პრომპტები გააკეთეთ კონკრეტული და მკაფიო.
4. თითოეული Node დააბრუნოს მხოლოდ ის ველი, რომელსაც ის ცვლის.
5. საბოლოოდ `print(result)`-ით შეამოწმეთ, რომ სამივე ველი შევსებულია.