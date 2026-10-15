import pytest
from .fake_model import DEFAULT_PLAN
from langchain_core.exceptions import OutputParserException
from langgraph.graph import END

from app.agent import build_plan_graph, check_validation


@pytest.mark.parametrize(
    ('error_message', 'attempts', 'expected'),
    [
        ('', 1, END),
        ('bad plan', 1, 'generate_plan'),
        ('bad plan', 4, 'generate_plan'),
        ('bad plan', 5, END),
    ],
)
def test_check_validation(error_message, attempts, expected):
    state = {'user_request': '', 'error_message': error_message, 'attempts': attempts, 'plan': {}}
    assert check_validation(state) == expected


def run_plan_loop():
    state = {'user_request': 'Plan a trip to Rome', 'error_message': '', 'attempts': 0, 'plan': {}}
    return build_plan_graph().invoke(state)


def test_a_bad_plan_is_retried_with_the_error_in_the_prompt(fake_model):
    fake_model.plans = [OutputParserException('duration_days must be at most 20'), DEFAULT_PLAN]

    result = run_plan_loop()

    assert result['attempts'] == 2
    assert result['plan']['destination'] == 'Rome'
    second_prompt = fake_model.prompts[1]
    assert 'duration_days must be at most 20' in second_prompt


def test_the_loop_gives_up_after_five_attempts(fake_model):
    fake_model.plans = [OutputParserException('still bad')] * 5

    result = run_plan_loop()

    assert result['attempts'] == 5
    assert result['plan'] == {}
    assert result['error_message']
