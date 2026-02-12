"""
Bias Detection Endpoint
Real-time detection of cognitive biases during simulation
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import os
import anthropic

logger = logging.getLogger(__name__)

router = APIRouter()


class ConversationMessage(BaseModel):
    """A message in the conversation"""
    role: str  # student or patient
    content: str
    timestamp: str


class BiasDetectionRequest(BaseModel):
    """Request for bias detection"""
    case_id: str
    conversation_history: List[ConversationMessage]
    patient_profile: Dict[str, Any]


class BiasDetectionResponse(BaseModel):
    """Response with bias detection result"""
    bias_detected: bool
    bias_type: Optional[str] = None  # anchoring, premature_closure, confirmation_bias
    confidence: Optional[float] = None  # 0.0 to 1.0
    explanation: Optional[str] = None
    intervention_message: Optional[str] = None
    reflection_questions: Optional[List[str]] = None


@router.post("/detect", response_model=BiasDetectionResponse)
async def detect_bias(request: BiasDetectionRequest):
    """
    Detect cognitive biases in real-time during simulation.

    Analyzes conversation to detect:
    - Anchoring bias: Fixating on initial diagnosis
    - Premature closure: Accepting first diagnosis without full differential
    - Confirmation bias: Only seeking evidence for initial hypothesis
    """

    logger.info(f"Analyzing bias for case {request.case_id}")

    # Build the detection prompt
    detection_prompt = f"""You are an expert medical educator monitoring a student's diagnostic reasoning in real-time.

**Case Information:**
Patient: {request.patient_profile.get('name', 'Unknown')}
Chief Complaint: {request.patient_profile.get('chief_complaint', 'Unknown')}
Actual Diagnosis: {request.patient_profile.get('actual_diagnosis', 'Unknown')}

**Conversation So Far:**
{_format_conversation(request.conversation_history)}

**Your Task:**
Analyze the student's questioning pattern and reasoning to detect cognitive biases. Look for:

1. **Anchoring Bias**: Has the student fixated on one diagnosis without exploring alternatives?
   - Are they only asking questions that support one specific diagnosis?
   - Have they ignored red flags or contradictory evidence?

2. **Premature Closure**: Has the student jumped to a conclusion too quickly?
   - Have they asked < 5 substantive questions before diagnosing?
   - Did they skip important screening questions?
   - Are they missing critical differentials?

3. **Confirmation Bias**: Is the student only seeking evidence for their initial hypothesis?
   - Are all questions directed toward confirming one diagnosis?
   - Are they ignoring or downplaying contradictory findings?

**Detection Criteria:**
- Only flag if bias is CLEAR and SIGNIFICANT
- Early in interview (<3 questions): Don't flag yet, student is still gathering data
- Mid-interview (3-6 questions): Flag if clear anchoring or confirmation bias
- Late interview (>6 questions): Flag if premature closure without full differential

Return your analysis in this JSON format:
{{
  "bias_detected": true,
  "bias_type": "anchoring",
  "confidence": 0.85,
  "explanation": "Student has asked 5 consecutive questions about cardiac symptoms without considering systemic causes despite patient mentioning weight loss",
  "intervention_message": "Take a step back. You've been focusing heavily on cardiac causes. What other systems could cause these symptoms?",
  "reflection_questions": [
    "What alternative diagnoses have you considered?",
    "Are there any findings that don't fit your current hypothesis?",
    "What key questions haven't you asked yet?"
  ]
}}

If NO significant bias detected, return:
{{
  "bias_detected": false
}}
"""

    try:
        # Create Claude client
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key or api_key == "sk-ant-your-key-here":
            raise HTTPException(status_code=500, detail="Anthropic API key not configured")

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-opus-4-20250514",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": detection_prompt
            }]
        )

        # Extract the response
        detection_text = ""
        for block in response.content:
            if block.type == "text":
                detection_text += block.text

        logger.info("Bias detection analysis completed")

        # Parse the JSON response
        import json
        detection_data = json.loads(detection_text)

        return BiasDetectionResponse(**detection_data)

    except Exception as e:
        logger.error(f"Bias detection failed: {str(e)}", exc_info=True)
        # Return no bias detected on error to avoid blocking simulation
        return BiasDetectionResponse(bias_detected=False)


def _format_conversation(messages: List[ConversationMessage]) -> str:
    """Format conversation for the prompt"""
    formatted = []
    for i, msg in enumerate(messages, 1):
        role = "Student" if msg.role == "student" else "Patient"
        formatted.append(f"{i}. [{msg.timestamp}] {role}: {msg.content}")
    return "\n".join(formatted)


@router.get("/health")
async def bias_detection_health():
    """Health check for bias detection endpoint"""
    return {"status": "healthy", "feature": "bias-detection"}
