class CaseRecommender:
    """Recommends next cases based on student needs."""

    def recommend(self, student_profile: dict) -> list:
        recommendations = []
        specialty_scores = student_profile.get("specialty_scores", {})

        weak_specialties = [s for s, score in specialty_scores.items() if score < 60]
        if weak_specialties:
            recommendations.append({
                "type": "weak_area",
                "specialty": weak_specialties[0],
                "difficulty": "beginner",
                "reason": f"Your {weak_specialties[0]} accuracy is only {specialty_scores[weak_specialties[0]]}%",
                "priority": "high",
            })

        if student_profile.get("biases", {}).get("anchoring"):
            recommendations.append({
                "type": "bias_counter",
                "specialty": "mixed",
                "difficulty": "intermediate",
                "reason": "Atypical presentation cases to reduce anchoring bias",
                "priority": "medium",
            })

        strong_specialties = [s for s, score in specialty_scores.items() if score > 80]
        if strong_specialties:
            recommendations.append({
                "type": "challenge",
                "specialty": strong_specialties[0],
                "difficulty": "advanced",
                "reason": f"Your {strong_specialties[0]} accuracy is {specialty_scores[strong_specialties[0]]}%. Ready for advanced cases!",
                "priority": "low",
            })

        return recommendations

    def get_demo_recommendations(self) -> list:
        return [
            {
                "type": "weak_area",
                "specialty": "Neurology",
                "difficulty": "beginner",
                "reason": "Your neurology accuracy is only 45%. Let's strengthen this foundation.",
                "priority": "high",
            },
            {
                "type": "bias_counter",
                "specialty": "Mixed",
                "difficulty": "intermediate",
                "reason": "Atypical presentation cases to reduce your anchoring bias pattern.",
                "priority": "medium",
            },
            {
                "type": "challenge",
                "specialty": "Cardiology",
                "difficulty": "advanced",
                "reason": "Your cardiology accuracy is 82%. Ready for advanced cases!",
                "priority": "low",
            },
        ]
