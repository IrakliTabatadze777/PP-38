# ამოცანა 1 — Movie Request Router

ააწყვეთ გრაფი, რომელიც მომხმარებლის მოთხოვნას კლასიფიკაციას გაუკეთებს და შესაბამის node-ზე გადაიყვანს.

### 1. სტრუქტურირებული მოდელი

```python
class MovieRequestCategory(BaseModel):
    category: Literal['recommendation', 'snacks', 'trivia']
```

### 2. State

```python
class MovieState(TypedDict):
    user_request: str
    genre: str
    category: str
    response: str
```

### 3. Nodes

* `classify_request` — LLM-ს `with_structured_output(MovieRequestCategory)`-ით მოთხოვნის კატეგორიას განსაზღვრინებს.
* სამი specialist node (`recommendation`, `snacks`, `trivia`), თითოეული თავისი prompt-ით და `genre`-ის გამოყენებით:

```python
SPECIALIST_PROMPTS = {
    'recommendation': 'Recommend one {genre} movie to watch tonight and explain why in 2 sentences.',
    'snacks': 'Suggest 3 snacks that go well with a {genre} movie night.',
    'trivia': 'Tell me one interesting trivia fact about {genre} movies.',
}
```

### 4. Routing

`route_by_category` აბრუნებს `state['category']`-ს, ხოლო `add_conditional_edges`-ში სამივე კატეგორია უნდა მიუთითოთ.

### 5. ტესტირება

გაუშვით გრაფი **3 განსხვავებულ მოთხოვნაზე** (თითო კატეგორიაზე) და დაბეჭდეთ კატეგორია და საბოლოო პასუხი.
მაგალითად, `genre='horror'`:

* `"What should I watch tonight?"`
* `"What should I eat while watching?"`
* `"Tell me something fun about this genre"`

### 6. ვიზუალიზაცია

შეინახეთ გრაფი `movie_graph.png`.

---

# ამოცანა 2 — Self-Correcting Movie Plan

ააწყვეთ გრაფი, რომელიც LLM-ისგან იღებს სტრუქტურირებულ პასუხს და თუ ვალიდაცია ჩავარდა, თავიდან ცდის.

### 1. მოდელი

```python
class MoviePlan(BaseModel):
    title: str
    duration_minutes: int = Field(gt=0, le=240, description='Movie length in minutes')
    ticket_price_usd: float = Field(gt=0, description='Ticket price in USD')
    snacks: list[str] = Field(min_length=3, description='Snacks to buy')
```

### 2. State

```python
class MoviePlanState(TypedDict):
    user_request: str
    error_message: str
    attempts: int
    plan: dict
```

### 3. Nodes და routing

* `generate_plan` node:
  * ზრდის `attempts`-ს;
  * თუ წინა შეცდომა არსებობს, prompt-ს უმატებს მას;
  * იყენებს `with_structured_output(MoviePlan)`-ს;
  * `try/except (ValidationError, OutputParserException)`-ით ამუშავებს წარუმატებელ მცდელობას.
* `check_validation` აბრუნებს:
  * `END` — თუ `error_message` ცარიელია;
  * `END` — თუ `attempts >= 3`;
  * `'generate_plan'` — სხვა შემთხვევაში.

### 4. ტესტირება

გაუშვით ორი მოთხოვნით:

1. `"Plan a cozy movie night for a family comedy"`
2. `"Plan a movie night with a 5-hour long epic movie"`

თითოეულისთვის დაბეჭდეთ, რამდენი მცდელობა დასჭირდა და შედეგის ყველა ველი.

---

# ამოცანა 3 — Movie Night Supervisor

გააერთიანეთ წინა ამოცანები supervisor-ში.

### 1. Tool-ები

შექმენით ორი `@tool` ფუნქცია fake მონაცემებით (მინიმუმ 3-3 ჩანაწერი, უცნობისთვის `'Unknown'`):

```python
@tool
def get_showtimes(movie: str):
    '''Get showtimes for the given movie'''
    ...

@tool
def get_movie_rating(movie: str):
    '''Get rating for the given movie'''
    ...
```

### 2. Tool Agent

ააწყვეთ tool-graph (`call_model` ↔ `call_tools`).

### 3. Supervisor

```python
class SupervisorDecision(BaseModel):
    next_agent: Literal['tool_agent', 'plan_agent']
    reasoning: str


class SupervisorState(TypedDict):
    user_request: str
    next_agent: str
    reasoning: str
    completed_agents: list[str]
    tool_agent_result: str
    plan_agent_result: dict
```

* `tool_agent` — ამუშავებს ჩვენების დროს და რეიტინგს (tool-graph-ით);
* `plan_agent` — იძახებს ამოცანა 2-ის გრაფს და წერს შედეგს `plan_agent_result`-ში;
* `supervisor_node`:
  * LLM-ს გადასცემს მოთხოვნას და `completed_agents`-ს;
  * თუ არჩეული აგენტი უკვე შესრულებულია, `next_agent = END`.
* `plan_agent`-ის მოთხოვნა **უნდა აიღოთ `state['user_request']`-დან**, და არა hardcode-ით.

### 4. ტესტირება

გაუშვით ასეთი მოთხოვნით:

```text
"I want to watch Inception tonight. Tell me its showtimes and rating, and plan the movie night for me."
```

დაბეჭდეთ:

* supervisor-ის ყოველი გადაწყვეტილება (`Next Agent`, `Reasoning`);
* `completed_agents`;
* `tool_agent_result`;
* `plan_agent_result`.

### 5. ვიზუალიზაცია

შეინახეთ სრული გრაფი `movie_supervisor_graph.png` სახელით.

> ⚠️ **გაითვალისწინეთ:** `add_conditional_edges`-ის path map-ში `END: END`-ის დამატება არ დაგავიწყდეთ, თორემ supervisor-ის დასრულებისას მიიღებთ `KeyError: '__end__'`-ს.
