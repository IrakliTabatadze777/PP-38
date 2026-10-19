import json
import uuid

import httpx
import streamlit as st
import os

API_URL = os.environ.get('API_URL')


def api_get(path: str) -> dict:
    response = httpx.get(f'{API_URL}{path}', timeout=30)
    response.raise_for_status()
    return response.json()


def api_stream(path: str, payload: dict):
    with httpx.stream('POST', f'{API_URL}{path}', json=payload, timeout=120) as response:
        if response.status_code >= 400:
            response.read()
            yield {'type': 'error', 'detail': response.json().get('detail', response.text)}
            return
        for line in response.iter_lines():
            if line.startswith('data: '):
                yield json.loads(line[len('data: ') :])


st.set_page_config(page_title='Trip Assistant')
st.title('Trip Assistant')

if 'session_id' not in st.session_state:
    st.session_state.session_id = st.query_params.get('session') or str(uuid.uuid4())
    st.query_params['session'] = st.session_state.session_id
    st.session_state.result = None
    try:
        st.session_state.result = api_get(f'/sessions/{st.session_state.session_id}')
    except httpx.HTTPStatusError as error:
        if error.response.status_code != 404:
            raise


STEP_LABELS = {
    'supervisor': 'Supervisor is deciding...',
    'general_agent': 'Answering...',
    'tool_agent': 'Tool agent is working...',
    'plan_agent': 'Plan agent is working...',
}


def run_and_render(path: str, payload: dict) -> None:
    final = None
    with st.status('Working...', expanded=False) as status:
        for event in api_stream(path, payload):
            if event['type'] == 'step':
                status.update(label=STEP_LABELS.get(event['node'], event['node']))
            elif event['type'] == 'final':
                final = event
            elif event['type'] == 'error':
                status.update(label='Failed', state='error')
                st.error(event['detail'])
                return
        status.update(label='Done', state='complete')

    st.session_state.result = final
    st.rerun()


def show_plan(plan: dict) -> None:
    st.markdown(f'**{plan["destination"]}**, {plan["duration_days"]} days, **${plan["daily_budget_usd"]:.0f}/day**')
    st.markdown('Packing list: ' + ', '.join(plan['packing_list']))


def decide(decision: dict) -> None:
    run_and_render('/approve/stream', {'session_id': st.session_state.session_id, **decision})


def render_approval_card(plan: dict) -> None:
    st.warning('Paused. Review the plan before it is finalized.')
    budget = st.number_input(
        'Daily budget (USD)', min_value=1.0, max_value=10000.0, value=float(plan['daily_budget_usd']), step=5.0
    )
    approve_col, edit_col = st.columns(2)
    if approve_col.button('Approve', type='primary'):
        decide({'action': 'approve'})
    if edit_col.button('Approve with my budget'):
        decide({'action': 'edit', 'daily_budget_usd': budget})


result = st.session_state.result
paused = result is not None and result['status'] == 'awaiting_approval'

if result:
    with st.chat_message('user'):
        st.markdown(result['user_request'])
    with st.chat_message('assistant'):
        if result['general_answer']:
            st.markdown(result['general_answer'])
        if result['tool_result']:
            st.markdown(result['tool_result'])
        if result['plan']:
            show_plan(result['plan'])
        if result['final_note']:
            st.success(result['final_note'])
        if paused:
            render_approval_card(result['plan'])

prompt = st.chat_input('Ask about a trip...', disabled=paused)
if prompt:
    with st.chat_message('user'):
        st.markdown(prompt)
    run_and_render('/chat/stream', {'session_id': st.session_state.session_id, 'message': prompt})
