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
from modules.skills.followup_skill import run_followup
from modules.skills.knowledge_qa_skill import run_knowledge_qa
from modules.skills.log_ingestion_skill import run_log_ingestion
from modules.skills.payload_analysis_skill import run_payload_analysis

EXIT_COMMANDS = {"exit", "quit", "離開"}
MENU_EXIT_COMMANDS = EXIT_COMMANDS | {"0"}

MENU_TEXT = """
請選擇模式：
1. Payload / event analysis
2. Log file ingestion demo
3. Security knowledge Q&A
4. Follow-up / more details
0. Exit
"""


def _is_exit_command(value):
    return (value or "").strip().lower() in MENU_EXIT_COMMANDS


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

    mode_handlers = {
        "1": {
            "prompt": "\n請輸入 payload 或事件描述: ",
            "runner": lambda user_input: run_payload_analysis(agent, user_input),
            "show_analyzing": True,
        },
        "2": {
            "prompt": "\n請輸入 log 檔案路徑: ",
            "runner": run_log_ingestion,
            "show_analyzing": False,
        },
        "3": {
            "prompt": "\n請輸入資安知識問題: ",
            "runner": lambda user_input: run_knowledge_qa(agent, user_input),
            "show_analyzing": True,
        },
        "4": {
            "prompt": "\n請輸入追問或想了解的細節: ",
            "runner": lambda user_input: run_followup(agent, user_input),
            "show_analyzing": True,
        },
    }

    while True:
        print(MENU_TEXT)
        choice = input("請輸入模式編號: ").strip()

        if _is_exit_command(choice):
            print("再見。")
            break

        if not choice:
            continue

        handler = mode_handlers.get(choice)
        if handler is None:
            print("\n無效的模式編號，請重新選擇。\n")
            continue

        user_input = input(handler["prompt"]).strip()

        if _is_exit_command(user_input):
            print("再見。")
            break

        if not user_input:
            continue

        try:
            if handler["show_analyzing"]:
                print("分析中...")

            output = handler["runner"](user_input)
            print(output)
        except Exception as exc:
            print(f"\n系統錯誤: {exc}\n")


if __name__ == "__main__":
    main()
