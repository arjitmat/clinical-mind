class KnowledgeGraphBuilder:
    """Builds knowledge graph from student case history."""

    def __init__(self):
        self.concepts: dict = {}
        self.connections: list = []

    def update_concept(self, concept: str, correct: bool):
        if concept not in self.concepts:
            self.concepts[concept] = {"correct": 0, "total": 0}
        self.concepts[concept]["total"] += 1
        if correct:
            self.concepts[concept]["correct"] += 1

    def add_connection(self, source: str, target: str, correct: bool):
        connection_id = f"{source}-{target}"
        existing = next((c for c in self.connections if c["id"] == connection_id), None)
        if existing:
            existing["total"] += 1
            if correct:
                existing["correct"] += 1
        else:
            self.connections.append({
                "id": connection_id,
                "source": source,
                "target": target,
                "correct": 1 if correct else 0,
                "total": 1,
            })

    def to_graph_data(self) -> dict:
        nodes = [
            {"id": concept, "strength": data["correct"] / max(data["total"], 1), "size": data["total"]}
            for concept, data in self.concepts.items()
        ]
        links = [
            {"source": conn["source"], "target": conn["target"], "strength": conn["correct"] / max(conn["total"], 1)}
            for conn in self.connections
        ]
        return {"nodes": nodes, "links": links}

    def build_demo_graph(self) -> dict:
        return {
            "nodes": [
                {"id": "Cardiology", "strength": 0.82, "size": 12, "category": "specialty"},
                {"id": "Respiratory", "strength": 0.65, "size": 8, "category": "specialty"},
                {"id": "Infectious", "strength": 0.78, "size": 10, "category": "specialty"},
                {"id": "Neurology", "strength": 0.45, "size": 5, "category": "specialty"},
                {"id": "Gastro", "strength": 0.70, "size": 7, "category": "specialty"},
                {"id": "Emergency", "strength": 0.55, "size": 6, "category": "specialty"},
                {"id": "STEMI", "strength": 0.85, "size": 8, "category": "diagnosis"},
                {"id": "Pulmonary Embolism", "strength": 0.40, "size": 4, "category": "diagnosis"},
                {"id": "Dengue", "strength": 0.80, "size": 9, "category": "diagnosis"},
                {"id": "Pneumonia", "strength": 0.72, "size": 7, "category": "diagnosis"},
                {"id": "Meningitis", "strength": 0.35, "size": 3, "category": "diagnosis"},
                {"id": "Chest Pain", "strength": 0.90, "size": 10, "category": "symptom"},
                {"id": "Dyspnea", "strength": 0.75, "size": 8, "category": "symptom"},
                {"id": "Fever", "strength": 0.85, "size": 11, "category": "symptom"},
                {"id": "Headache", "strength": 0.60, "size": 6, "category": "symptom"},
                {"id": "ECG", "strength": 0.88, "size": 9, "category": "investigation"},
                {"id": "Troponin", "strength": 0.80, "size": 7, "category": "investigation"},
            ],
            "links": [
                {"source": "Chest Pain", "target": "STEMI", "strength": 0.9},
                {"source": "Chest Pain", "target": "Pulmonary Embolism", "strength": 0.3},
                {"source": "Cardiology", "target": "STEMI", "strength": 0.9},
                {"source": "STEMI", "target": "ECG", "strength": 0.9},
                {"source": "STEMI", "target": "Troponin", "strength": 0.85},
                {"source": "Dyspnea", "target": "Pneumonia", "strength": 0.75},
                {"source": "Dyspnea", "target": "Pulmonary Embolism", "strength": 0.35},
                {"source": "Respiratory", "target": "Pneumonia", "strength": 0.72},
                {"source": "Fever", "target": "Dengue", "strength": 0.8},
                {"source": "Fever", "target": "Infectious", "strength": 0.78},
                {"source": "Fever", "target": "Meningitis", "strength": 0.4},
                {"source": "Infectious", "target": "Dengue", "strength": 0.82},
                {"source": "Headache", "target": "Meningitis", "strength": 0.35},
                {"source": "Headache", "target": "Neurology", "strength": 0.48},
            ],
        }
