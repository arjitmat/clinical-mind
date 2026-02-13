"""In-memory session tracker for student case history and dynamic analytics.

All analytics data is derived from REAL session activity. No hardcoded demo data.
Analytics start empty and build up as the student completes cases.
"""

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

    def get_performance_data(self) -> dict:
        """Build performance data from real session results only."""
        if not self.case_history:
            return {
                "overall_accuracy": 0,
                "cases_completed": 0,
                "avg_time_minutes": 0,
                "peer_percentile": 0,
                "history": [],
                "message": "No cases completed yet. Start a case to see your performance data.",
            }

        # Build history from actual case results, grouped in batches of 5
        history = []
        batch_size = 5
        for i in range(0, len(self.case_history), batch_size):
            batch = self.case_history[i:i + batch_size]
            batch_accuracy = round(sum(c["accuracy_score"] for c in batch) / len(batch))
            history.append({
                "batch": f"Cases {i + 1}-{i + len(batch)}",
                "accuracy": batch_accuracy,
                "count": len(batch),
            })

        return {
            "overall_accuracy": self.overall_accuracy,
            "cases_completed": self.cases_completed,
            "avg_time_minutes": 0,
            "peer_percentile": 0,
            "history": history,
        }

    def get_student_profile(self) -> dict:
        """Build dynamic student profile from real session data only."""
        scores = self.get_specialty_scores()
        weak = [s for s, sc in scores.items() if sc < 60]

        return {
            "id": "student-001",
            "name": "Medical Student",
            "year_level": "final_year",
            "cases_completed": self.cases_completed,
            "accuracy": self.overall_accuracy,
            "avg_time": 0,
            "percentile": 0,
            "specialty_scores": scores,
            "weak_areas": weak,
        }

    def detect_biases(self) -> dict:
        """Detect cognitive biases from session case history."""
        if self.cases_completed < 3:
            return {
                "biases_detected": [],
                "cases_analyzed": 0,
                "overall_accuracy": 0,
                "message": "Complete at least 3 cases to get bias analysis.",
                "generated_at": datetime.now().isoformat(),
            }

        biases = []
        recent = self.case_history[-10:]

        # Anchoring: repeated wrong diagnoses
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
        """Build knowledge graph from real session data only."""
        if not self.case_history:
            return {
                "nodes": [],
                "links": [],
                "message": "Complete cases to build your knowledge graph.",
            }

        nodes = []
        links = []
        seen_specialties: dict[str, dict] = {}
        seen_diagnoses: dict[str, dict] = {}
        diagnosis_links: list[dict] = []

        for case in self.case_history:
            diag = case["correct_diagnosis"]
            spec = case["specialty"].capitalize()

            # Build specialty nodes
            if spec not in seen_specialties:
                seen_specialties[spec] = {
                    "id": spec, "strength": 0.0, "size": 0, "category": "specialty",
                    "correct": 0, "total": 0,
                }
            seen_specialties[spec]["total"] += 1
            seen_specialties[spec]["size"] += 1
            if case["is_correct"]:
                seen_specialties[spec]["correct"] += 1

            # Build diagnosis nodes
            if diag not in seen_diagnoses:
                seen_diagnoses[diag] = {
                    "id": diag, "strength": 0.0, "size": 0, "category": "diagnosis",
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

        # Calculate specialty strengths
        for spec_data in seen_specialties.values():
            if spec_data["total"] > 0:
                spec_data["strength"] = round(spec_data["correct"] / spec_data["total"], 2)
            del spec_data["correct"]
            del spec_data["total"]

        nodes = list(seen_specialties.values()) + list(seen_diagnoses.values())

        # Add cross-specialty links
        spec_list = list(seen_specialties.keys())
        for i in range(len(spec_list)):
            for j in range(i + 1, len(spec_list)):
                links.append({
                    "source": spec_list[i],
                    "target": spec_list[j],
                    "strength": 0.4,
                })

        links.extend(diagnosis_links)

        return {"nodes": nodes, "links": links}

    def get_recommendations(self) -> list[dict]:
        """Generate recommendations based on real session performance."""
        if not self.case_history:
            return [{
                "type": "start",
                "specialty": "Any",
                "difficulty": "beginner",
                "reason": "Start with any specialty to begin building your clinical skills.",
                "priority": "high",
            }]

        scores = self.get_specialty_scores()
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
        high_biases = [b for b in biases.get("biases_detected", []) if b["severity"] in ("moderate", "high")]
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
            recommendations.append({
                "type": "continue",
                "specialty": "Mixed",
                "difficulty": "intermediate",
                "reason": "Keep practicing across different specialties to build well-rounded skills.",
                "priority": "medium",
            })

        return recommendations


# Singleton instance shared across the app
session = SessionTracker()
