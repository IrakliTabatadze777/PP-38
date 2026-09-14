
### ამოცანა 1
შექმენით Pydantic მოდელი სახელად `Book`, რომელსაც აქვს შემდეგი ველები:
- title (str)
- author (str)
- year (int)
- genres (list[str])
- pages (int)

გამოიყენეთ `ChatGoogleGenerativeAI` + `with_structured_output` და ამოიღეთ ინფორმაცია შემდეგი ტექსტიდან:

> "George Orwell's famous novel 1984 was published in 1949. It is a dystopian political fiction book with 328 pages."

დაბეჭდეთ ყველა ველი.

### ამოცანა 2
შექმენით `PromptTemplate`, რომელიც იღებს ერთ პარამეტრს `text`-ს და ითხოვს, რომ ტექსტიდან ამოიღოს პროდუქტის მახასიათებლები.

შექმენი Pydantic მოდელი `Product`:
- name
- price (float)
- currency
- in_stock (bool)
- colors (list[str])

გაუშვით chain და შეამოწმეთ ტექსტზე:

> "The new wireless headphones cost 149.99 USD. Available in black, white and blue. Currently in stock."

### ამოცანა 3

შექმენით Pydantic მოდელი სახელად `FantasyQuest`, რომელსაც აქვს შემდეგი ველები:

- quest_name (str)
- hero_name (str)
- enemy (str)
- magical_item (str)
- danger_level (int)          # 1-დან 10-მდე
- reward (str)
- side_quests (list[str])
- is_cursed (bool)

დაწერეთ `SystemMessage`, რომელიც მოდელს ეტყვის:

- იყოს მაქსიმალურად ეპიკური ფენტეზის სტილში
- თუ ტექსტში რაიმე ინფორმაცია აკლია, თვითონ მოიფიქროს ლოგიკური და საინტერესო დეტალი (მაგრამ მაინც სტრუქტურირებულად დააბრუნოს)
- danger_level ყოველთვის იყოს რეალისტური შეფასება მოცემული ინფორმაციის მიხედვით

გამოიყენეთ `ChatPromptTemplate` + `with_structured_output` და ააწყვეთ chain.

ტექსტი (შეგიძლიათ გამოიყენოთ სხვა ტექსტი):

> "ახალგაზრდა ჯადოქარი სახელად ლირა უნდა გაემგზავროს ჩრდილოეთის ტყეებში, რათა იპოვოს დაკარგული მთვარის ხმალი. გზად მას ელოდება უძველესი ტყის სული, რომელიც სძულს ადამიანებს. თუ წარმატებას მიაღწევს, მიიღებს უკვდავების ელექსირს."

დაბეჭდეთ მთელი `FantasyQuest` ობიექტი.
