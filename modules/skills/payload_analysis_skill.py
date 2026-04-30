from modules.skills import get_agent_state


def run_payload_analysis(agent, user_input: str) -> str:
    # Thin wrapper around the existing Mode 1 agent analysis flow.
    answer = agent.handle_query(user_input, get_agent_state(agent))
    return f"\nAI: {answer}\n"
