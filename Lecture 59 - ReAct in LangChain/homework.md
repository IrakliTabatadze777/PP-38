
# ამოცანა
აგენტმა უნდა უპასუხოს შემდეგ კითხვას:  
**„რომელ თაროზე და რა სართულზეა ბიბლიოთეკაში ამჟამად ყველაზე მოთხოვნადი წიგნი?“**

### Tools
გამოიყენეთ ზუსტად ეს tools:

```python
from langchain_core.tools import tool

@tool
def get_most_requested_book() -> str:
    """Returns the title of the currently most requested book in the library."""
    return "Clean Code"


@tool
def get_book_location(book_title: str) -> str:
    """Returns the shelf and floor location of the given book."""
    locations = {
        "Clean Code": "3rd floor, shelf B-17",
        "Design Patterns": "2nd floor, shelf A-09",
        "The Pragmatic Programmer": "4th floor, shelf C-04"
    }
    return locations.get(book_title, "Book not found")
```

### მოსალოდნელი საბოლოო პასუხი
აგენტმა დაახლოებით ასე უნდა დაასრულოს:  
**„ყველაზე მოთხოვნადი წიგნი არის Clean Code და ის მდებარეობს მე-3 სართულზე, თარო B-17-ზე.“**

---

### ნაწილი 1 – LCEL(LangChain Expression Language) იმპლემენტაცია (ხელით აწყობილი ReAct)

მოთხოვნები:
- აგენტი ააწყვეთ მხოლოდ LCEL-ის გამოყენებით (`PromptTemplate` + `ChatGoogleGenerativeAI` + `ReActSingleInputOutputParser`)
- ხელით მართეთ `intermediate_steps` / `agent_scratchpad`
- დაწერეთ საკუთარი `run_tool` დამხმარე ფუნქცია
- აგენტი შეზღუდეთ მაქსიმუმ 5 ნაბიჯით
- დაბეჭდეთ ყოველი Thought → Action → Action Input → Observation
- თუ აგენტი 5 ნაბიჯში ვერ მივა Final Answer-მდე, დააბრუნეთ შესაბამისი შეტყობინება

---

### ნაწილი 2 – სტანდარტული ReAct იმპლემენტაცია

შექმენით ფაილი სახელად `react_standard.py`.

მოთხოვნები:
- გამოიყენეთ `create_react_agent` + `AgentExecutor`
- Prompt-ი გაიწევეთ LangSmith-იდან (`hwchase17/react`) ან დაწერეთ თქვენი
- დააყენეთ `verbose=True` და `return_intermediate_steps=True`
- აგენტი შეზღუდეთ მაქსიმუმ 5 იტერაციით
- დაბეჭდეთ intermediate steps და საბოლოო პასუხი
