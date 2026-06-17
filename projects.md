## ზოგადი მოთხოვნები ყველა პროექტისთვის:
- კონსოლური აპლიკაცია (`input()` / `print()`).
- OOP (კლასები, მემკვიდრეობა, encapsulation).
- დეკორატორები სადაც ლოგიკურია (ვალიდაცია, ქეშირება, retry და ა.შ.).
- მონაცემების შენახვა JSON ფაილში (სერიალიზაცია/დესერიალიზაცია).
- გამონაკლისების სრული მართვა და მკაფიო შეცდომის შეტყობინებები მომხმარებლისთვის.
- კოდი დაყოფილი რამდენიმე ფაილად (`models.py`, `storage.py`, `main.py` და სხვ.).
- `virtual environment` + `requirements.txt`.

---

## 1. პერსონალური Task Manager

**რას უნდა აკეთებდეს აპლიკაცია:**
- დავალებების შექმნა (სათაური, აღწერა, დედლაინი, პრიორიტეტი).
- დავალებების ნახვა, ძებნა, რედაქტირება და წაშლა.
- დავალების სტატუსის შეცვლა (pending, in-progress, completed).
- დავალებების დაჯგუფება პროექტებში.
- პროგრამის გაშვებისას მონაცემების ჩატვირთვა JSON-დან და დახურვისას ავტომატური შენახვა.

---

## 2. Asynchronous Weather Dashboard

**რას უნდა აკეთებდეს აპლიკაცია:**
- ქალაქის სახელით ამინდის მიღება.
- რამდენიმე ქალაქის ამინდის პარალელურად (ასინქრონულად) მიღება.
- შედეგების ლამაზად ჩვენება კონსოლში.
- ამინდის ისტორიის შენახვა და წარსული ჩანაწერების ნახვა.
- ქალაქების სიის მართვა (დამატება/წაშლა).

**API:** Open-Meteo

**1. Geocoding API (ქალაქის სახელიდან კოორდინატების მიღება)**
- რექვესტი: `GET https://geocoding-api.open-meteo.com/v1/search?name=Tbilisi&count=1&language=ka`
- რესპონსი მაგალითი:
```json
{
  "results": [
    {
      "name": "Tbilisi",
      "latitude": 41.7151,
      "longitude": 44.8271,
      "country": "Georgia"
    }
  ]
}
```

**2. Weather Forecast API**
- რექვესტი: `GET https://api.open-meteo.com/v1/forecast?latitude=41.7151&longitude=44.8271&current=temperature_2m,wind_speed_10m,weather_code`
- რესპონსი მაგალითი:
```json
{
  "current": {
    "time": "2025-06-17T12:00",
    "temperature_2m": 27.4,
    "wind_speed_10m": 8.5,
    "weather_code": 3
  }
}
```

---

## 3. Personal Finance Tracker

**რას უნდა აკეთებდეს აპლიკაცია:**
- ტრანზაქციების დამატება (შემოსავალი/ხარჯი, თანხა, კატეგორია, თარიღი, კომენტარი).
- ტრანზაქციების ნახვა, ფილტრაცია (თარიღის, კატეგორიის მიხედვით) და წაშლა.
- კატეგორიებზე ბიუჯეტის ლიმიტების დაყენება.
- თვიური და ზოგადი შეჯამებების ჩვენება (შემოსავალი, ხარჯები, ბალანსი, ლიმიტების სტატუსი).
- CSV/JSON ფაილები ინფორმაციის შესანახად

---

## 4. Rick and Morty Explorer

**რას უნდა აკეთებდეს აპლიკაცია:**
- პერსონაჟების, ლოკაციების და ეპიზოდების ძებნა სახელით ან ფილტრებით.
- კონკრეტული პერსონაჟის/ლოკაციის/ეპიზოდის დეტალური ინფორმაციის ჩვენება.
- რენდომ პერსონაჟის ან ეპიზოდის ჩვენება.
- საყვარელი პერსონაჟების შენახვა და მართვა JSON ფაილში.
- ძებნის ისტორიის ნახვა.

**API:** Rick and Morty API — https://rickandmortyapi.com/api (არ საჭიროებს key-ს)

**მთავარი ენდპოინტები:**
- პერსონაჟები: `GET https://rickandmortyapi.com/api/character`
- ძებნა: `GET https://rickandmortyapi.com/api/character/?name=Rick&status=Alive`
- კონკრეტული: `GET https://rickandmortyapi.com/api/character/1`
- ლოკაციები: `GET https://rickandmortyapi.com/api/location`
- ეპიზოდები: `GET https://rickandmortyapi.com/api/episode`

**პერსონაჟის რესპონსი მაგალითი:**
```json
{
  "id": 1,
  "name": "Rick Sanchez",
  "status": "Alive",
  "species": "Human",
  "gender": "Male",
  "origin": { "name": "Earth (C-137)" },
  "location": { "name": "Earth (Replacement Dimension)" },
  "image": "https://rickandmortyapi.com/api/character/avatar/1.jpeg"
}
```

---

## 5. Joke / Quote Daily Collector

**რას უნდა აკეთებდეს აპლიკაცია:**
- ხუმრობების მიღება API-დან.
- შედეგების ჩვენება და ისტორიაში შენახვა.
- კონტენტის ფილტრაცია კატეგორიით ან თემით.
- შენახული ხუმრობების/ციტატების ნახვა და წაშლა.
- რენდომ ან თემატური კონტენტის გენერაცია.

**API: jokeapi**

**JokeAPI**  
   რექვესტი: `GET https://v2.jokeapi.dev/joke/Any?safe-mode`  
   რესპონსი მაგალითი:
   ```json
   {
     "category": "Programming",
     "type": "single",
     "joke": "Why do programmers prefer dark mode? Because light attracts bugs."
   }
   ```
