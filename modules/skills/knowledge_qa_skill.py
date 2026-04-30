from modules.skills import get_agent_state


def run_knowledge_qa(agent, question: str) -> str:
    # Thin wrapper around the existing Mode 3 agent/RAG flow.
    answer = agent.handle_query(question, get_agent_state(agent))
    return f"\nAI: {answer}\n"
