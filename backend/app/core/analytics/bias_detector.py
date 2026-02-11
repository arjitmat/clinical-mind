from datetime import datetime
from typing import Optional


class BiasDetector:
    """Detects cognitive biases from student decision patterns."""

    def __init__(self):
        self.student_history: list = []

    def add_case_result(self, case_id: str, student_actions: list, diagnosis: str, correct: bool):
        self.student_history.append({
            "case_id": case_id,
            "actions": student_actions,
            "diagnosis": diagnosis,
            "correct": correct,
            "timestamp": datetime.now().isoformat(),
        })

    def detect_anchoring_bias(self) -> Optional[dict]:
        recent = self.student_history[-10:] if len(self.student_history) >= 10 else self.student_history
        if not recent:
            return None

        anchoring_count = sum(
            1 for case in recent
            if len(case.get("actions", [])) > 0
            and case["actions"][0].get("diagnosis") == case["diagnosis"]
        )

        if anchoring_count >= 7:
            return {
                "bias": "anchoring",
                "severity": "moderate",
                "score": anchoring_count * 10,
                "evidence": f"Stuck with initial diagnosis in {anchoring_count}/{len(recent)} cases",
                "recommendation": "Practice cases with atypical presentations. Force yourself to reconsider after each new piece of information.",
            }
        return None

    def detect_premature_closure(self) -> Optional[dict]:
        recent = self.student_history[-10:] if len(self.student_history) >= 10 else self.student_history
        if not recent:
            return None

        premature_count = sum(
            1 for case in recent
            if len(case.get("actions", {}).get("differential_list", [])) < 3
        )

        if premature_count >= 6:
            return {
                "bias": "premature_closure",
                "severity": "high",
                "score": premature_count * 10,
                "evidence": f"Only considered 1-2 diagnoses in {premature_count}/{len(recent)} cases",
                "recommendation": "Force yourself to list 3+ differential diagnoses before deciding.",
            }
        return None

    def generate_bias_report(self) -> dict:
        biases = []
        anchoring = self.detect_anchoring_bias()
        if anchoring:
            biases.append(anchoring)
        premature = self.detect_premature_closure()
        if premature:
            biases.append(premature)

        return {
            "biases_detected": biases,
            "cases_analyzed": len(self.student_history),
            "overall_accuracy": self._calculate_accuracy(),
            "generated_at": datetime.now().isoformat(),
        }

    def generate_demo_report(self) -> dict:
        return {
            "biases_detected": [
                {
                    "type": "anchoring",
                    "severity": "moderate",
                    "score": 65,
                    "evidence": "You stuck with your initial diagnosis in 7 out of 10 recent cases, even when new information contradicted it.",
                    "recommendation": "Practice cases with atypical presentations. Force yourself to reconsider after each new piece of information.",
                },
                {
                    "type": "premature_closure",
                    "severity": "low",
                    "score": 40,
                    "evidence": "In 4 out of 10 cases, you considered fewer than 3 differential diagnoses before settling on your answer.",
                    "recommendation": "Before finalizing, always list at least 3 differential diagnoses and explain why you're ruling each one out.",
                },
                {
                    "type": "availability",
                    "severity": "moderate",
                    "score": 55,
                    "evidence": "After studying cardiology, you diagnosed 3 consecutive non-cardiac cases as cardiac. Your recent study focus influenced your diagnoses.",
                    "recommendation": "Before diagnosing, list 3 differential diagnoses from different organ systems.",
                },
                {
                    "type": "confirmation",
                    "severity": "low",
                    "score": 30,
                    "evidence": "Minimal confirmation bias detected. You generally consider contradicting evidence.",
                    "recommendation": "Continue actively seeking evidence that contradicts your working diagnosis.",
                },
            ],
            "cases_analyzed": 48,
            "overall_accuracy": 75,
            "generated_at": datetime.now().isoformat(),
        }

    def _calculate_accuracy(self) -> float:
        if not self.student_history:
            return 0.0
        correct = sum(1 for case in self.student_history if case.get("correct"))
        return round(correct / len(self.student_history) * 100, 1)
