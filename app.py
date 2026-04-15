import os
from modules.rag_qa import RAGQA
from modules.followup_handler import FollowupHandler
from modules.detector import RuleBasedDetector
from modules.responder import Responder
from config import CHROMA_PATH

def main():
    print("🧠 載入模型中...")

    # 初始化模組
    rag_qa = RAGQA()
    followup_handler = FollowupHandler()
    detector = RuleBasedDetector()
    responder = Responder()

    if not os.path.exists(CHROMA_PATH):
        raise Exception("❌ 找不到 Chroma DB，請先執行 ingest_knowledge.py")

    print("\n🛡️ Security AI 啟動成功！")

    # 狀態變數
    last_question = ""
    last_answer = ""
    last_points = []
    last_focus = ""

    while True:
        query = input("\n👤 你: ").strip()

        if query.lower() in ["exit", "quit", "離開"]:
            print("👋 再見！")
            break

        if not query:
            continue

        try:
            print("🔍 檢查中...")

            # 第 N 點追問
            if followup_handler.is_point_followup(query):
                idx = followup_handler.extract_index(query)

                if not last_points:
                    print("\n🤖 AI: 目前沒有可追問的上一輪重點\n")
                    continue

                if idx is None or idx < 1 or idx > len(last_points):
                    print("\n🤖 AI: 找不到對應的重點項目\n")
                    continue

                target = last_points[idx - 1]
                last_focus = target

                answer = rag_qa.explain_point(target)
                print(f"\n🤖 AI: {answer}\n")

                last_question = query
                last_answer = answer
                continue

            # 自然追問
            if followup_handler.is_natural_followup(query):
                if not last_focus:
                    print("\n🤖 AI: 目前沒有可延續的焦點內容\n")
                    continue

                answer = rag_qa.handle_natural_followup(last_focus, query)
                print(f"\n🤖 AI: {answer}\n")

                last_question = query
                last_answer = answer
                continue

            # 非資安主題
            if not rag_qa.is_security(query):
                print("\n🤖 AI: 知識庫沒有相關資料\n")
                continue

            # 一般 RAG 問題
            context, ok = rag_qa.retrieve_context(query)

            if not ok:
                print("\n🤖 AI: 知識庫沒有相關資料\n")
                continue

            answer = rag_qa.generate_answer(query, context)
            print(f"\n🤖 AI: {answer}\n")

            last_question = query
            last_answer = answer
            last_points = followup_handler.extract_points(answer)
            last_focus = ""

        except Exception as e:
            print(f"\n❌ 錯誤: {e}\n")

if __name__ == "__main__":
    main()