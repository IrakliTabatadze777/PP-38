from langchain_core.messages import AIMessage

from app.agent import SupervisorDecision, TripPlan

DEFAULT_PLAN = TripPlan(
    destination='Rome',
    duration_days=5,
    daily_budget_usd=150,
    packing_list=['passport', 'comfortable shoes', 'sunscreen'],
)


def tool_call(name: str, **args) -> AIMessage:
    return AIMessage(content='', tool_calls=[{'name': name, 'args': args, 'id': f'call-{name}'}])


def take(items: list, what: str):
    if not items:
        raise AssertionError(f'The test did not script enough fake answers for: {what}')
    return items.pop(0)


class FakeModel:
    def __init__(self):
        self.decisions: list[str] = []
        self.tool_replies: list[AIMessage] = []
        self.plans: list = []
        self.text = 'A short fake answer.'
        self.prompts: list = []
        self.tool_inputs: list = []

    def invoke(self, prompt):
        self.prompts.append(prompt)
        return AIMessage(content=self.text)

    def with_structured_output(self, schema):
        return _StructuredFake(self, schema)

    def bind_tools(self, tools):
        return _ToolFake(self)


class _StructuredFake:
    def __init__(self, fake: FakeModel, schema):
        self.fake = fake
        self.schema = schema

    def invoke(self, prompt):
        self.fake.prompts.append(prompt)
        if self.schema is SupervisorDecision:
            return SupervisorDecision(next_agent=take(self.fake.decisions, 'the supervisor'), reasoning='fake')
        plan = self.fake.plans.pop(0) if self.fake.plans else DEFAULT_PLAN
        if isinstance(plan, Exception):
            raise plan
        return plan


class _ToolFake:
    def __init__(self, fake: FakeModel):
        self.fake = fake

    def invoke(self, messages):
        self.fake.tool_inputs.append(messages)
        return take(self.fake.tool_replies, 'the tool agent')
