from modules.skills import get_agent_state
from modules.log_input_adapter import format_input_translation, try_translate_raw_log_input


def run_payload_analysis(agent, user_input: str) -> str:
    # Thin wrapper around the existing Mode 1 agent analysis flow.
    translation = try_translate_raw_log_input(user_input)
    if translation:
        answer = agent.handle_query(translation.agent_input, get_agent_state(agent))
        return f"\n{format_input_translation(translation)}\n\nAI: {answer}\n"

    answer = agent.handle_query(user_input, get_agent_state(agent))
    return f"\nAI: {answer}\n"
