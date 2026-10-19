from agent import revise_plan
from schemas import AgentResponse


def thread_config(session_id: str):
    return {'recursion_limit': 20, 'configurable': {'thread_id': session_id}}


def is_paused(snapshot):
    return 'finalize_plan' in snapshot.next


def describe(snapshot):
    values = snapshot.values

    return AgentResponse(
        status='awaiting_approval' if is_paused(snapshot) else 'completed',
        user_request=values['user_request'],
        tool_result=values['tool_agent_result'],
        plan=values['plan_agent_result'],
        general_answer=values['general_agent_result'],
        final_note=values['final_note'],
    )


async def apply_decision(graph, config, decision):
    if decision.action == 'edit':
        values = (await graph.aget_state(config)).values
        new_plan = revise_plan(values['user_request'], decision.daily_budget_usd)
        await graph.aupdate_state(config, {'plan_agent_result': new_plan})
