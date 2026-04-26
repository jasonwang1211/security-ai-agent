# Incident Response

## 定義
Incident Response 是組織在面對資安事件時，用於辨識、控制、根除、復原與追蹤改善的標準化流程。

## 常見攻擊特徵
- 同一事件可能橫跨 Web、主機、帳號與網路層。
- 初始告警通常只揭露部分現象，需透過調查還原全貌。
- 若反應不及時，事件可能擴大為持久化或橫向移動。

## 可疑 Payload / Log 特徵
- 告警事件集中發生於短時間內。
- 重要系統出現異常登入、檔案變更、程序建立或資料傳輸。
- 不同層級日誌對應出同一來源、帳號或時間軸。

## 偵測邏輯
- 依事件類型、影響範圍與資產重要性進行分級。
- 將偵測結果轉換為可執行的調查與處置步驟。
- 建立證據保全與時間軸整理機制，支援後續鑑識與報告。

## 風險評估
- 風險取決於資產重要性、受影響範圍、攻擊持續時間與可恢復性。
- 若事件涉及憑證、核心資料或高權限主機，應視為高風險。

## 防禦方式
- 預先定義角色分工、升級流程與通報窗口。
- 維持日誌、備份、隔離、封鎖與憑證輪替能力。
- 定期演練不同類型事件的應變流程。
- 將應變經驗回饋至偵測規則與安全控制。

## 事件應變流程
- 辨識：確認事件真實性、範圍與優先級。
- 控制：封鎖惡意來源、隔離主機、限制帳號或中止風險流程。
- 根除：清除惡意程式、修補弱點、移除持久化機制。
- 復原：恢復服務、驗證完整性並加強監控。
- 回顧：彙整證據、產出報告並修正流程與控制缺口。

## 報告用摘要
本主題描述藍隊面對資安事件時的標準應變框架，重點在於快速分級、有效控制與可追溯調查。建議結合日誌分析、資產重要性與修補計畫，確保事件處置與後續改善能形成閉環。

## Structured Signals
- attack_type: Incident Response
- severity: MEDIUM to HIGH
- detection_keywords: incident triage, containment trigger, evidence preservation, eradication workflow, recovery validation
- log_indicators: confirmed malicious alerts, suspicious host or account activity, policy violations, correlated telemetry showing active compromise
- risk_score_hint: Increase urgency when critical services, sensitive data, or privileged identities are involved.
- recommended_action: Triage quickly, contain affected assets, preserve evidence, eradicate root cause, recover safely, and document lessons learned.
