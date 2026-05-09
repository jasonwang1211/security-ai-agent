from modules.skills import get_agent_state


def run_knowledge_qa(agent, question: str) -> str:
    # Mode 3 is dedicated knowledge Q&A, so it bypasses follow-up and detection flows.
    answer = agent.handle_knowledge_query(question, get_agent_state(agent))
    return f"\nAI: {answer}\n"
