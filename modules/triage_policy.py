from modules.decision_engine import DecisionEngine
from modules.defense_simulator import DefenseSimulator
from modules.risk_scorer import RiskScorer


class TriagePolicy:
    def __init__(
        self,
        risk_scorer=None,
        decision_engine=None,
        defense_simulator=None,
    ):
        self.risk_scorer = risk_scorer or RiskScorer()
        self.decision_engine = decision_engine or DecisionEngine()
        self.defense_simulator = defense_simulator or DefenseSimulator()

    def score_risk(self, detector_result, llm_result=None):
        attack_types = []
        if isinstance(detector_result, dict):
            attack_types = detector_result.get("attack_types", [])
        return self.risk_scorer.score(attack_types)

    def decide(self, risk_result, llm_result=None):
        risk_level = None
        if isinstance(risk_result, dict):
            risk_level = risk_result.get("risk_level")
        return self.decision_engine.decide(risk_level)

    def simulate_defense(self, decision_result, detector_result=None, risk_result=None):
        decision = None
        if isinstance(decision_result, dict):
            decision = decision_result.get("decision")
        return self.defense_simulator.simulate(
            decision,
            detector_result or {},
            risk_result or {},
        )
