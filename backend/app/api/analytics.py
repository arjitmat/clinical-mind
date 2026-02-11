from fastapi import APIRouter

router = APIRouter()


@router.get("/performance")
async def get_performance():
    return {
        "overall_accuracy": 75,
        "cases_completed": 48,
        "avg_time_minutes": 10,
        "peer_percentile": 15,
        "history": [
            {"week": "W1", "accuracy": 55, "avg_time": 18},
            {"week": "W2", "accuracy": 60, "avg_time": 16},
            {"week": "W3", "accuracy": 58, "avg_time": 15},
            {"week": "W4", "accuracy": 68, "avg_time": 14},
            {"week": "W5", "accuracy": 72, "avg_time": 12},
            {"week": "W6", "accuracy": 75, "avg_time": 11},
            {"week": "W7", "accuracy": 78, "avg_time": 10},
        ],
    }


@router.get("/peer-comparison")
async def get_peer_comparison():
    return {
        "student_accuracy": 75,
        "peer_average": 62,
        "top_10_average": 88,
        "ranking": "Top 15%",
        "specialty_comparison": {
            "cardiology": {"student": 82, "average": 65},
            "respiratory": {"student": 65, "average": 60},
            "infectious": {"student": 78, "average": 70},
            "neurology": {"student": 45, "average": 55},
            "gastro": {"student": 70, "average": 58},
            "emergency": {"student": 55, "average": 52},
        },
    }


@router.get("/recommendations")
async def get_recommendations():
    from app.core.analytics.recommender import CaseRecommender
    recommender = CaseRecommender()
    return recommender.get_demo_recommendations()
