from modules.agent import SecurityAgent
from modules.detector import RuleBasedDetector
from modules.followup_handler import FollowupHandler
from modules.llm_analyzer import LLMSecurityAnalyzer
from modules.llm_threat_judge import LLMThreatJudge
from modules.rag_qa import RAGQA
from modules.responder import Responder
from modules.skills.followup_skill import run_followup
from modules.skills.knowledge_qa_skill import run_knowledge_qa
from modules.skills.log_ingestion_skill import run_log_agent_analysis, run_log_ingestion, run_with_progress
from modules.skills.payload_analysis_skill import run_payload_analysis
from modules.triage_policy import TriagePolicy

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

LOG_AGENT_SCOPE_MENU = """
Choose SecurityAgent analysis scope:
1. Analyze first event only
2. Analyze all events
0. Cancel
"""


def _is_exit_command(value):
    return (value or "").strip().lower() in MENU_EXIT_COMMANDS


def _log_agent_scope_from_choice(choice):
    if choice == "1":
        return "first"
    if choice == "2":
        return "all"
    return None


def _print_status(message):
    print(message, flush=True)


def _prompt_log_agent_scope():
    print(LOG_AGENT_SCOPE_MENU)
    scope_choice = input("請選擇分析範圍: ").strip()
    if not scope_choice:
        print("未輸入分析範圍，已取消 SecurityAgent 分析。")
        return None

    scope = _log_agent_scope_from_choice(scope_choice)
    if scope is None:
        print("已取消 SecurityAgent 分析。")
    return scope


def _run_log_agent_analysis(agent, log_path, scope):
    print("[Mode 2] Running SecurityAgent analysis...")
    analysis_output = run_log_agent_analysis(
        agent,
        log_path,
        scope=scope,
        progress_callback=_print_status,
        result_callback=_print_status,
    )
    if analysis_output:
        print(analysis_output)
    print("[Mode 2] SecurityAgent analysis complete.")


def _show_detailed_json_if_requested(log_path):
    json_choice = input("Show detailed JSON output? (y/n): ").strip()
    if _is_exit_command(json_choice):
        print("再見。")
        return False

    if json_choice.lower() == "y":
        print("[Mode 2] Generating detailed JSON output...")
        print(run_log_ingestion(log_path, include_json=True, include_summary=False))
    elif not json_choice:
        print("未顯示 detailed JSON output。")
    return True


def _run_standard_mode(handler, user_input):
    print(handler["status_message"])
    output = run_with_progress(
        lambda: handler["runner"](user_input),
        handler["progress_label"],
    )
    print(output)


def main():
    print("正在啟動 Security AI...")

    rag_qa = RAGQA()
    followup_handler = FollowupHandler()
    detector = RuleBasedDetector()
    responder = Responder()
    triage_policy = TriagePolicy()
    llm_analyzer = LLMSecurityAnalyzer()
    llm_threat_judge = LLMThreatJudge()
    agent = SecurityAgent(
        followup_handler=followup_handler,
        detector=detector,
        rag_qa=rag_qa,
        responder=responder,
        triage_policy=triage_policy,
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
            "status_message": "[Mode 1] Running payload/event analysis...",
            "progress_label": "[Mode 1] Payload/event analysis",
        },
        "2": {
            "prompt": "\n請輸入 log 檔案路徑: ",
            "runner": None,
        },
        "3": {
            "prompt": "\n請輸入資安知識問題: ",
            "runner": lambda user_input: run_knowledge_qa(agent, user_input),
            "status_message": "[Mode 3] Running security knowledge Q&A...",
            "progress_label": "[Mode 3] Security knowledge Q&A",
        },
        "4": {
            "prompt": "\n請輸入追問或想了解的細節: ",
            "runner": lambda user_input: run_followup(agent, user_input),
            "status_message": "[Mode 4] Running follow-up analysis...",
            "progress_label": "[Mode 4] Follow-up analysis",
        },
    }

    while True:
        print(MENU_TEXT)
        choice = input("請輸入模式編號: ").strip()

        if _is_exit_command(choice):
            print("再見。")
            break

        if not choice:
            print("請輸入模式編號，或輸入 0 離開。")
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
            if choice == "2":
                print("[Mode 2] Reading and summarizing log file...")
                summary_output = run_log_ingestion(user_input)
                print(summary_output)
                if summary_output.startswith("\n讀取 log 檔案失敗"):
                    continue

                agent_choice = input("Send aggregated events to SecurityAgent? (y/n): ").strip()
                if _is_exit_command(agent_choice):
                    print("再見。")
                    break

                if agent_choice.lower() == "y":
                    print("[Mode 2] Preparing SecurityAgent analysis...")
                    scope = _prompt_log_agent_scope()
                    if scope:
                        _run_log_agent_analysis(agent, user_input, scope)

                if not _show_detailed_json_if_requested(user_input):
                    break
                continue

            _run_standard_mode(handler, user_input)
        except Exception as exc:
            print(f"\n系統錯誤: {exc}\n")


if __name__ == "__main__":
    main()
