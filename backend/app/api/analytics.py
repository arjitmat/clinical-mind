from fastapi import APIRouter
from app.core.session import session

router = APIRouter()


@router.get("/performance")
async def get_performance():
    return session.get_performance_data()


@router.get("/peer-comparison")
async def get_peer_comparison():
    profile = session.get_student_profile()
    scores = profile["specialty_scores"]
    return {
        "student_accuracy": profile["accuracy"],
        "peer_average": 62,
        "top_10_average": 88,
        "ranking": f"Top {profile['percentile']}%",
        "specialty_comparison": {
            spec: {"student": score, "average": max(50, score - 10)}
            for spec, score in scores.items()
        },
    }


@router.get("/recommendations")
async def get_recommendations():
    return session.get_recommendations()
