"""In-memory session tracker for student case history and dynamic analytics."""

from datetime import datetime
from typing import Optional


class SessionTracker:
    """Tracks student case results within a session for dynamic analytics."""

    def __init__(self):
        self.case_history: list[dict] = []
        self.specialty_results: dict[str, dict] = {}

    def record_case_result(
        self,
        case_id: str,
        specialty: str,
        difficulty: str,
        diagnosis: str,
        correct_diagnosis: str,
        is_correct: bool,
        accuracy_score: int,
        stages_revealed: int = 3,
    ):
        """Record a completed case result."""
        result = {
            "case_id": case_id,
            "specialty": specialty,
            "difficulty": difficulty,
            "student_diagnosis": diagnosis,
            "correct_diagnosis": correct_diagnosis,
            "is_correct": is_correct,
            "accuracy_score": accuracy_score,
            "stages_revealed": stages_revealed,
            "timestamp": datetime.now().isoformat(),
        }
        self.case_history.append(result)

        # Update specialty tracking
        if specialty not in self.specialty_results:
            self.specialty_results[specialty] = {"correct": 0, "total": 0, "scores": []}
        self.specialty_results[specialty]["total"] += 1
        self.specialty_results[specialty]["scores"].append(accuracy_score)
        if is_correct:
            self.specialty_results[specialty]["correct"] += 1

    @property
    def cases_completed(self) -> int:
        return len(self.case_history)

    @property
    def overall_accuracy(self) -> float:
        if not self.case_history:
            return 0.0
        total_score = sum(c["accuracy_score"] for c in self.case_history)
        return round(total_score / len(self.case_history), 1)

    def get_specialty_scores(self) -> dict[str, int]:
        """Get accuracy percentage per specialty."""
        scores = {}
        for spec, data in self.specialty_results.items():
            if data["scores"]:
                scores[spec] = round(sum(data["scores"]) / len(data["scores"]))
        return scores

    def get_weak_areas(self) -> list[str]:
        """Specialties with accuracy below 60%."""
        scores = self.get_specialty_scores()
        return [s for s, score in scores.items() if score < 60]

    def get_performance_data(self, base_cases: int = 48, base_accuracy: float = 75) -> dict:
        """Build performance data merging base demo data with real session results."""
        session_completed = self.cases_completed
        total_completed = base_cases + session_completed

        if session_completed > 0:
            # Blend base accuracy with session accuracy
            session_acc = self.overall_accuracy
            blended = round((base_accuracy * base_cases + session_acc * session_completed) / total_completed, 1)
        else:
            blended = base_accuracy

        # Build history: base weeks + session weeks
        history = [
            {"week": "W1", "accuracy": 55, "avg_time": 18},
            {"week": "W2", "accuracy": 60, "avg_time": 16},
            {"week": "W3", "accuracy": 58, "avg_time": 15},
            {"week": "W4", "accuracy": 68, "avg_time": 14},
            {"week": "W5", "accuracy": 72, "avg_time": 12},
            {"week": "W6", "accuracy": 75, "avg_time": 11},
            {"week": "W7", "accuracy": 78, "avg_time": 10},
        ]

        if session_completed > 0:
            history.append({
                "week": "Now",
                "accuracy": round(self.overall_accuracy),
                "avg_time": 8,
            })

        return {
            "overall_accuracy": blended,
            "cases_completed": total_completed,
            "avg_time_minutes": 9 if session_completed > 0 else 10,
            "peer_percentile": max(5, 15 - session_completed),
            "history": history,
        }

    def get_student_profile(self) -> dict:
        """Build dynamic student profile merging base data with session results."""
        base_scores = {
            "cardiology": 82, "respiratory": 65, "infectious": 78,
            "neurology": 45, "gastro": 70, "emergency": 55,
        }

        # Merge session specialty scores into base
        session_scores = self.get_specialty_scores()
        merged_scores = {**base_scores}
        for spec, score in session_scores.items():
            if spec in merged_scores:
                # Average base with session
                merged_scores[spec] = round((merged_scores[spec] + score) / 2)
            else:
                merged_scores[spec] = score

        weak = [s for s, sc in merged_scores.items() if sc < 60]

        return {
            "id": "student-001",
            "name": "Medical Student",
            "year_level": "final_year",
            "cases_completed": 48 + self.cases_completed,
            "accuracy": self.get_performance_data()["overall_accuracy"],
            "avg_time": 9 if self.cases_completed > 0 else 10,
            "percentile": max(5, 15 - self.cases_completed),
            "specialty_scores": merged_scores,
            "weak_areas": weak or ["neurology", "emergency"],
        }

    def detect_biases(self) -> dict:
        """Detect cognitive biases from session case history."""
        if self.cases_completed < 3:
            # Not enough data — return base demo biases
            return self._demo_biases()

        biases = []
        recent = self.case_history[-10:]

        # Anchoring: if student gets similar diagnoses wrong repeatedly
        wrong_cases = [c for c in recent if not c["is_correct"]]
        if len(wrong_cases) >= 3:
            biases.append({
                "type": "anchoring",
                "severity": "high" if len(wrong_cases) >= 5 else "moderate",
                "score": min(100, len(wrong_cases) * 15),
                "evidence": f"You missed the correct diagnosis in {len(wrong_cases)} of your last {len(recent)} cases. Consider whether you're anchoring to your initial impression.",
                "recommendation": "After your initial assessment, deliberately list 3 alternative diagnoses before committing.",
            })

        # Premature closure: low stages revealed
        low_info = [c for c in recent if c.get("stages_revealed", 3) < 2]
        if len(low_info) >= 2:
            biases.append({
                "type": "premature_closure",
                "severity": "moderate",
                "score": min(100, len(low_info) * 20),
                "evidence": f"You diagnosed {len(low_info)} cases without revealing all available information.",
                "recommendation": "Gather all available data before making your diagnosis — history, exam, and labs.",
            })

        # Availability: same specialty errors
        spec_errors: dict[str, int] = {}
        for c in wrong_cases:
            spec_errors[c["specialty"]] = spec_errors.get(c["specialty"], 0) + 1
        repeated = [(s, n) for s, n in spec_errors.items() if n >= 2]
        if repeated:
            spec, count = repeated[0]
            biases.append({
                "type": "availability",
                "severity": "moderate",
                "score": min(100, count * 25),
                "evidence": f"You made {count} errors in {spec} cases. Recent focus on certain specialties may be influencing your pattern recognition.",
                "recommendation": f"Review {spec} fundamentals and practice differentials from other organ systems.",
            })

        # Confirmation bias: high accuracy overall but specific blind spots
        if self.overall_accuracy > 70 and len(wrong_cases) >= 2:
            biases.append({
                "type": "confirmation",
                "severity": "low",
                "score": 25,
                "evidence": "Your overall accuracy is good, but review incorrect cases to check if you selectively focused on confirming evidence.",
                "recommendation": "For each case, actively seek one finding that contradicts your leading diagnosis.",
            })

        if not biases:
            biases = [
                {"type": "anchoring", "severity": "low", "score": 20,
                 "evidence": "Minimal anchoring bias detected in your recent cases.",
                 "recommendation": "Continue practicing systematic differential diagnosis."},
                {"type": "confirmation", "severity": "low", "score": 15,
                 "evidence": "Good job considering contradicting evidence.",
                 "recommendation": "Keep actively seeking disconfirming data."},
            ]

        return {
            "biases_detected": biases,
            "cases_analyzed": len(recent),
            "overall_accuracy": self.overall_accuracy,
            "generated_at": datetime.now().isoformat(),
        }

    def build_knowledge_graph(self) -> dict:
        """Build knowledge graph from session data merged with base graph."""
        base_nodes = [
            {"id": "Cardiology", "strength": 0.82, "size": 12, "category": "specialty"},
            {"id": "Respiratory", "strength": 0.65, "size": 8, "category": "specialty"},
            {"id": "Infectious", "strength": 0.78, "size": 10, "category": "specialty"},
            {"id": "Neurology", "strength": 0.45, "size": 5, "category": "specialty"},
            {"id": "Gastro", "strength": 0.70, "size": 7, "category": "specialty"},
            {"id": "Emergency", "strength": 0.55, "size": 6, "category": "specialty"},
        ]
        base_links = [
            {"source": "Cardiology", "target": "Respiratory", "strength": 0.6},
            {"source": "Infectious", "target": "Respiratory", "strength": 0.7},
            {"source": "Neurology", "target": "Emergency", "strength": 0.4},
            {"source": "Gastro", "target": "Emergency", "strength": 0.5},
        ]

        # Add diagnosis nodes from session history
        seen_diagnoses: dict[str, dict] = {}
        diagnosis_links: list[dict] = []

        for case in self.case_history:
            diag = case["correct_diagnosis"]
            spec = case["specialty"].capitalize()

            if diag not in seen_diagnoses:
                seen_diagnoses[diag] = {
                    "id": diag, "strength": 0.0, "size": 0, "category": "diagnosis"
                }
            seen_diagnoses[diag]["size"] += 1
            if case["is_correct"]:
                seen_diagnoses[diag]["strength"] = min(1.0, seen_diagnoses[diag]["strength"] + 0.3)
            else:
                seen_diagnoses[diag]["strength"] = max(0.0, seen_diagnoses[diag]["strength"] + 0.1)

            # Link diagnosis to specialty
            link_id = f"{spec}-{diag}"
            existing = next((l for l in diagnosis_links if f"{l['source']}-{l['target']}" == link_id), None)
            if not existing:
                diagnosis_links.append({
                    "source": spec,
                    "target": diag,
                    "strength": 0.8 if case["is_correct"] else 0.3,
                })

        # Update base specialty nodes with session data
        session_scores = self.get_specialty_scores()
        for node in base_nodes:
            spec_lower = node["id"].lower()
            if spec_lower in session_scores:
                node["strength"] = round(session_scores[spec_lower] / 100, 2)
                node["size"] += self.specialty_results.get(spec_lower, {}).get("total", 0)

        nodes = base_nodes + list(seen_diagnoses.values())
        links = base_links + diagnosis_links

        return {"nodes": nodes, "links": links}

    def get_recommendations(self) -> list[dict]:
        """Generate recommendations based on session performance."""
        profile = self.get_student_profile()
        scores = profile["specialty_scores"]

        recommendations = []

        # Weak areas
        weak = [(s, sc) for s, sc in scores.items() if sc < 60]
        weak.sort(key=lambda x: x[1])
        if weak:
            spec, score = weak[0]
            recommendations.append({
                "type": "weak_area",
                "specialty": spec.capitalize(),
                "difficulty": "beginner",
                "reason": f"Your {spec} accuracy is only {score}%. Let's strengthen this foundation.",
                "priority": "high",
            })

        # Bias counter
        biases = self.detect_biases()
        high_biases = [b for b in biases["biases_detected"] if b["severity"] in ("moderate", "high")]
        if high_biases:
            recommendations.append({
                "type": "bias_counter",
                "specialty": "Mixed",
                "difficulty": "intermediate",
                "reason": f"Atypical presentation cases to reduce your {high_biases[0]['type']} bias pattern.",
                "priority": "medium",
            })

        # Challenge for strong areas
        strong = [(s, sc) for s, sc in scores.items() if sc >= 80]
        if strong:
            spec, score = strong[0]
            recommendations.append({
                "type": "challenge",
                "specialty": spec.capitalize(),
                "difficulty": "advanced",
                "reason": f"Your {spec} accuracy is {score}%. Ready for advanced cases!",
                "priority": "low",
            })

        if not recommendations:
            recommendations = [
                {"type": "weak_area", "specialty": "Neurology", "difficulty": "beginner",
                 "reason": "Your neurology accuracy is only 45%. Let's strengthen this foundation.", "priority": "high"},
                {"type": "challenge", "specialty": "Cardiology", "difficulty": "advanced",
                 "reason": "Your cardiology accuracy is 82%. Ready for advanced cases!", "priority": "low"},
            ]

        return recommendations

    def _demo_biases(self) -> dict:
        """Return demo biases when not enough session data."""
        return {
            "biases_detected": [
                {"type": "anchoring", "severity": "moderate", "score": 65,
                 "evidence": "You stuck with your initial diagnosis in 7 out of 10 recent cases, even when new information contradicted it.",
                 "recommendation": "Practice cases with atypical presentations. Force yourself to reconsider after each new piece of information."},
                {"type": "premature_closure", "severity": "low", "score": 40,
                 "evidence": "In 4 out of 10 cases, you considered fewer than 3 differential diagnoses before settling on your answer.",
                 "recommendation": "Before finalizing, always list at least 3 differential diagnoses and explain why you're ruling each one out."},
                {"type": "availability", "severity": "moderate", "score": 55,
                 "evidence": "After studying cardiology, you diagnosed 3 consecutive non-cardiac cases as cardiac.",
                 "recommendation": "Before diagnosing, list 3 differential diagnoses from different organ systems."},
                {"type": "confirmation", "severity": "low", "score": 30,
                 "evidence": "Minimal confirmation bias detected. You generally consider contradicting evidence.",
                 "recommendation": "Continue actively seeking evidence that contradicts your working diagnosis."},
            ],
            "cases_analyzed": 48,
            "overall_accuracy": 75,
            "generated_at": datetime.now().isoformat(),
        }


# Singleton instance shared across the app
session = SessionTracker()
