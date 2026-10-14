from dotenv import load_dotenv
from langsmith import Client

load_dotenv()

ls_client = Client()
DATASET = "trip-supervisor-v1"

examples = [
    {
        "inputs": {"question": "What's the weather in Rome? Do I need an umbrella?"},
        "outputs": {"expected_agents": ["tool_agent"]},
    },
    {
        "inputs": {"question": "What are the main sights in Tbilisi?"},
        "outputs": {"expected_agents": ["tool_agent"]},
    },
    {
        "inputs": {"question": "I'm in London tomorrow. What's the weather and what should I see?"},
        "outputs": {"expected_agents": ["tool_agent"]},
    },
    {
        "inputs": {"question": "What is your name?"},
        "outputs": {"expected_agents": ["general_agent"]},
    },
    {
        "inputs": {"question": "What is the capital of France?"},
        "outputs": {"expected_agents": ["general_agent"]},
    },
    {
        "inputs": {"question": "Plan a 5-day trip to Rome with a budget."},
        "outputs": {"expected_agents": ["plan_agent"]},
    },
    {
        "inputs": {"question": "What's the weather in Tbilisi, and make me a 3-day plan with a budget."},
        "outputs": {"expected_agents": ["tool_agent", "plan_agent"]},
    },
    {
        "inputs": {"question": "თბილისში რა ამინდია?"},
        "outputs": {"expected_agents": ["tool_agent"]},
    },
]

if __name__ == "__main__":
    if ls_client.has_dataset(dataset_name=DATASET):
        print(f"Dataset '{DATASET}' already exists.")
    else:
        dataset = ls_client.create_dataset(
            dataset_name=DATASET,
            description="Questions for the trip supervisor with the agents we expect it to use.",
        )
        ls_client.create_examples(dataset_id=dataset.id, examples=examples)
        print(f"Created '{DATASET}' with {len(examples)} examples.")
