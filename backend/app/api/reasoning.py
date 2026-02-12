"""
Reasoning Chain Analysis Endpoint
Uses Claude Opus extended thinking to analyze student diagnostic approach
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import os
from datetime import datetime
import anthropic

logger = logging.getLogger(__name__)

router = APIRouter()


class ReasoningStep(BaseModel):
    """A single step in the reasoning process"""
    step_number: int
    timestamp: str
    category: str  # data_gathering, hypothesis_generation, testing, diagnosis
    description: str
    quality: str  # excellent, good, acceptable, concerning, critical_gap
    expert_insight: str


class ReasoningAnalysisRequest(BaseModel):
    """Request for reasoning chain analysis"""
    case_id: str
    student_actions: List[Dict[str, Any]]  # List of student's questions/actions
    final_diagnosis: str
    case_info: Dict[str, Any]  # Patient info, actual diagnosis, etc.


class ReasoningAnalysisResponse(BaseModel):
    """Response with reasoning chain analysis"""
    analysis_id: str
    student_reasoning_steps: List[ReasoningStep]
    expert_reasoning_steps: List[ReasoningStep]
    divergence_points: List[Dict[str, str]]
    overall_assessment: str
    strengths: List[str]
    gaps: List[str]
    learning_recommendations: List[str]
    thinking_time_seconds: float


@router.post("/analyze", response_model=ReasoningAnalysisResponse)
async def analyze_reasoning_chain(request: ReasoningAnalysisRequest):
    """
    Analyze student's diagnostic reasoning using Claude Opus extended thinking.

    This uses extended thinking with a 10-minute budget to deeply analyze:
    1. Student's reasoning process step-by-step
    2. Expert reasoning approach for the same case
    3. Divergence points where student deviated from optimal path
    4. Specific gaps and learning opportunities
    """

    logger.info(f"Starting reasoning chain analysis for case {request.case_id}")

    # Build the analysis prompt
    analysis_prompt = f"""You are an expert medical educator analyzing a medical student's diagnostic reasoning process.

**Case Information:**
Patient: {request.case_info.get('patient_name', 'Unknown')}
Chief Complaint: {request.case_info.get('chief_complaint', 'Unknown')}
Actual Diagnosis: {request.case_info.get('actual_diagnosis', 'Unknown')}

**Student's Actions (chronological):**
{_format_student_actions(request.student_actions)}

**Student's Final Diagnosis:** {request.final_diagnosis}

**Your Task:**
Please spend significant time thinking deeply about this case using extended thinking. Analyze:

1. **Student's Reasoning Process:**
   - Break down each action the student took into reasoning steps
   - Categorize each step (data gathering, hypothesis generation, hypothesis testing, diagnosis)
   - Evaluate the quality of each step (excellent, good, acceptable, concerning, critical_gap)
   - Note the reasoning behind each action

2. **Expert Reasoning Process:**
   - How would an expert clinician approach this case?
   - What are the critical data points an expert would prioritize?
   - What hypotheses would they generate and in what order?
   - What tests would they use to differentiate?

3. **Divergence Analysis:**
   - Where did the student's path diverge from the expert path?
   - Were there critical questions NOT asked?
   - Were there premature conclusions or anchoring biases?
   - Were differential diagnoses appropriately considered?

4. **Educational Insights:**
   - What are the student's key strengths?
   - What are critical gaps in their reasoning?
   - Specific learning recommendations for improvement

Return your analysis in this JSON format:
{{
  "student_reasoning_steps": [
    {{
      "step_number": 1,
      "timestamp": "0:30",
      "category": "data_gathering",
      "description": "Asked about chest pain characteristics",
      "quality": "excellent",
      "expert_insight": "Excellent first question - chest pain characterization is critical for cardiac differential"
    }}
  ],
  "expert_reasoning_steps": [
    {{
      "step_number": 1,
      "timestamp": "0:00",
      "category": "hypothesis_generation",
      "description": "Generate initial differential: ACS, PE, aortic dissection, anxiety",
      "quality": "excellent",
      "expert_insight": "Expert immediately considers life-threatening causes"
    }}
  ],
  "divergence_points": [
    {{
      "student_action": "Did not ask about cocaine use until late in interview",
      "expert_action": "Would ask about substance use early given young patient with chest pain",
      "impact": "Delayed critical diagnosis",
      "learning_point": "Always ask about substance use in chest pain, especially in younger patients"
    }}
  ],
  "overall_assessment": "The student demonstrated good basic history-taking skills but showed anchoring bias...",
  "strengths": ["Systematic approach to history", "Good rapport building"],
  "gaps": ["Did not consider substance-induced ACS", "Anchored on anxiety diagnosis"],
  "learning_recommendations": ["Review differential diagnosis of chest pain in young adults", "Practice systematic substance use screening"]
}}
"""

    try:
        start_time = datetime.now()

        # Create Claude Opus client
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key or api_key == "sk-ant-your-key-here":
            raise HTTPException(status_code=500, detail="Anthropic API key not configured")

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-opus-4-20250514",
            max_tokens=16000,
            thinking={
                "type": "enabled",
                "budget_tokens": 10000  # 10-minute thinking budget
            },
            messages=[{
                "role": "user",
                "content": analysis_prompt
            }]
        )

        thinking_time = (datetime.now() - start_time).total_seconds()

        # Extract the analysis from response
        analysis_text = ""
        for block in response.content:
            if block.type == "text":
                analysis_text += block.text

        logger.info(f"Extended thinking completed in {thinking_time:.2f} seconds")

        # Parse the JSON response
        import json
        analysis_data = json.loads(analysis_text)

        # Generate analysis ID
        import uuid
        analysis_id = str(uuid.uuid4())

        # Build response
        return ReasoningAnalysisResponse(
            analysis_id=analysis_id,
            student_reasoning_steps=[
                ReasoningStep(**step) for step in analysis_data["student_reasoning_steps"]
            ],
            expert_reasoning_steps=[
                ReasoningStep(**step) for step in analysis_data["expert_reasoning_steps"]
            ],
            divergence_points=analysis_data["divergence_points"],
            overall_assessment=analysis_data["overall_assessment"],
            strengths=analysis_data["strengths"],
            gaps=analysis_data["gaps"],
            learning_recommendations=analysis_data["learning_recommendations"],
            thinking_time_seconds=thinking_time
        )

    except Exception as e:
        logger.error(f"Reasoning analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


def _format_student_actions(actions: List[Dict[str, Any]]) -> str:
    """Format student actions for the prompt"""
    formatted = []
    for i, action in enumerate(actions, 1):
        timestamp = action.get('timestamp', 'Unknown')
        content = action.get('content', 'Unknown action')
        formatted.append(f"{i}. [{timestamp}] {content}")
    return "\n".join(formatted)


@router.get("/health")
async def reasoning_health():
    """Health check for reasoning endpoint"""
    return {"status": "healthy", "feature": "reasoning-chain"}
