"""
Adversarial Case Generator Endpoint
Analyzes student biases and creates cases designed to exploit them
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import os
import anthropic

logger = logging.getLogger(__name__)

router = APIRouter()


class PastCasePerformance(BaseModel):
    """Student's performance on a past case"""
    case_id: str
    specialty: str
    actual_diagnosis: str
    student_diagnosis: str
    was_correct: bool
    missed_clues: List[str]
    anchoring_evidence: Optional[str] = None
    bias_detected: Optional[str] = None


class AdversarialCaseRequest(BaseModel):
    """Request to generate an adversarial case"""
    student_id: str
    past_cases: List[PastCasePerformance]
    profile: Dict[str, Any]


class AdversarialCaseResponse(BaseModel):
    """Response with adversarial case designed to exploit biases"""
    case_id: str
    predicted_bias: str
    bias_explanation: str
    trap_description: str

    # Case details
    patient_name: str
    age: int
    gender: str
    chief_complaint: str
    setting: str

    # The trap
    obvious_diagnosis: str  # What we predict student will anchor on
    actual_diagnosis: str   # The real diagnosis
    critical_differentiator: str  # The key question that reveals the truth

    # Educational value
    learning_objective: str
    why_challenging: str


@router.post("/generate", response_model=AdversarialCaseResponse)
async def generate_adversarial_case(request: AdversarialCaseRequest):
    """
    Generate an adversarial case designed to exploit student's cognitive biases.

    Process:
    1. Analyze past cases to identify bias patterns
    2. Generate a case that exploits the most prominent bias
    3. Create a "trap" that catches the student
    4. Provide educational reveal
    """

    logger.info(f"Generating adversarial case for student {request.student_id}")

    # Build the analysis prompt
    analysis_prompt = f"""You are an expert medical educator creating an adversarial case to challenge a medical student's cognitive biases.

**Student's Past Performance:**
{_format_past_cases(request.past_cases)}

**Student Profile:**
- Year Level: {request.profile.get('yearLevel', 'unknown')}
- Comfortable Specialties: {', '.join(request.profile.get('comfortableSpecialties', []))}
- Setting: {request.profile.get('setting', 'unknown')}

**Your Task:**
Analyze the student's pattern of errors to identify their most prominent cognitive bias. Then design a case that will likely trap them in that bias.

Common biases to detect:
1. **Anchoring Bias**: Fixating on initial impression despite contradictory evidence
2. **Availability Bias**: Overweighting recent or memorable cases
3. **Premature Closure**: Accepting first diagnosis without full differential
4. **Confirmation Bias**: Seeking only evidence that supports initial hypothesis
5. **Frequency Bias**: Assuming common diseases are always the diagnosis

Your case should:
- Have obvious "distractor" diagnosis that matches the student's bias
- Have subtle clues pointing to the actual diagnosis
- Require the student to actively challenge their initial impression
- Be realistic and India-specific

Return your analysis in this JSON format:
{{
  "predicted_bias": "anchoring_bias",
  "bias_explanation": "Student consistently fixates on initial presentations matching their comfortable specialties",
  "trap_description": "Case presents with classic cardiology symptoms, but actual cause is a rare endocrine disorder",

  "patient_name": "Ramesh Kumar",
  "age": 45,
  "gender": "male",
  "chief_complaint": "Palpitations and chest discomfort for 2 weeks",
  "setting": "Urban Medical College OPD",

  "obvious_diagnosis": "Atrial fibrillation (cardiology - student's comfort zone)",
  "actual_diagnosis": "Thyrotoxicosis presenting with cardiac symptoms",
  "critical_differentiator": "Asking about weight loss, heat intolerance, and tremors",

  "learning_objective": "Recognize when cardiac symptoms may be secondary to systemic disease",
  "why_challenging": "Presents with student's comfortable specialty but requires broader differential thinking"
}}

Generate a realistic, challenging case that will help the student recognize and overcome their bias patterns.
"""

    try:
        # Create Claude Opus client
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key or api_key == "sk-ant-your-key-here":
            raise HTTPException(status_code=500, detail="Anthropic API key not configured")

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": analysis_prompt
            }]
        )

        # Extract the response
        case_text = ""
        for block in response.content:
            if block.type == "text":
                case_text += block.text

        logger.info("Adversarial case generated successfully")

        # Parse the JSON response
        import json
        import uuid
        case_data = json.loads(case_text)

        return AdversarialCaseResponse(
            case_id=str(uuid.uuid4()),
            **case_data
        )

    except Exception as e:
        logger.error(f"Adversarial case generation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Case generation failed: {str(e)}")


def _format_past_cases(cases: List[PastCasePerformance]) -> str:
    """Format past cases for the prompt"""
    formatted = []
    for i, case in enumerate(cases, 1):
        status = "✓ Correct" if case.was_correct else "✗ Incorrect"
        formatted.append(f"""
Case {i}: {case.specialty}
- Actual: {case.actual_diagnosis}
- Student: {case.student_diagnosis} ({status})
- Missed clues: {', '.join(case.missed_clues) if case.missed_clues else 'None'}
- Bias detected: {case.bias_detected or 'None'}
""")
    return "\n".join(formatted)


@router.get("/health")
async def adversarial_health():
    """Health check for adversarial endpoint"""
    return {"status": "healthy", "feature": "adversarial"}
