from modules.agent import SecurityAgent
from modules.decision_engine import DecisionEngine
from modules.defense_simulator import DefenseSimulator
from modules.detector import RuleBasedDetector
from modules.followup_handler import FollowupHandler
from modules.llm_analyzer import LLMSecurityAnalyzer
from modules.llm_threat_judge import LLMThreatJudge
from modules.rag_qa import RAGQA
from modules.risk_scorer import RiskScorer
from modules.responder import Responder

EXIT_COMMANDS = {"exit", "quit", "離開"}


def main():
    print("正在啟動 Security AI...")

    rag_qa = RAGQA()
    followup_handler = FollowupHandler()
    detector = RuleBasedDetector()
    responder = Responder()
    risk_scorer = RiskScorer()
    decision_engine = DecisionEngine()
    defense_simulator = DefenseSimulator()
    llm_analyzer = LLMSecurityAnalyzer()
    llm_threat_judge = LLMThreatJudge()
    agent = SecurityAgent(
        followup_handler=followup_handler,
        detector=detector,
        rag_qa=rag_qa,
        responder=responder,
        risk_scorer=risk_scorer,
        decision_engine=decision_engine,
        defense_simulator=defense_simulator,
        llm_analyzer=llm_analyzer,
        llm_threat_judge=llm_threat_judge,
    )

    if rag_qa.is_ready():
        print("\nSecurity AI 已啟動。")
    else:
        print("\nSecurity AI 已啟動，但知識庫目前不可用，仍可進行攻擊偵測與防禦建議。")

    state = {
        "last_question": "",
        "last_answer": "",
        "last_points": [],
        "last_focus": "",
    }

    while True:
        query = input("\n你: ").strip()

        if query.lower() in EXIT_COMMANDS:
            print("再見。")
            break

        if not query:
            continue

        try:
            print("分析中...")
            answer = agent.handle_query(query, state)
            print(f"\nAI: {answer}\n")
        except Exception as exc:
            print(f"\n系統錯誤: {exc}\n")


if __name__ == "__main__":
    main()
