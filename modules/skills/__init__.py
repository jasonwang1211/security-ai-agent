def get_agent_state(agent):
    # CLI skills are thin wrappers, so shared conversation state stays on the agent.
    if not hasattr(agent, "cli_state"):
        agent.cli_state = {
            "last_question": "",
            "last_answer": "",
            "last_points": [],
            "last_focus": "",
        }

    return agent.cli_state
