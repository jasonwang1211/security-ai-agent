from modules.skills import get_agent_state


def run_followup(agent, question: str) -> str:
    # Thin wrapper around the existing Mode 4 follow-up flow with shared state.
    answer = agent.handle_query(question, get_agent_state(agent))
    return f"\nAI: {answer}\n"
