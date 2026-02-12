/**
 * TypeScript types for AI Patient Simulation
 */

export type EmotionalState = 'calm' | 'concerned' | 'anxious' | 'defensive';

export type PatientGender = 'male' | 'female' | 'pregnant';

export type RapportLevel = 1 | 2 | 3 | 4 | 5;

export type FeedbackType = 'positive' | 'warning' | 'critical';

export interface PatientInfo {
  age: number;
  gender: PatientGender;
  name: string;
  chief_complaint: string;
}

export interface TutorFeedback {
  type: FeedbackType;
  message: string;
  timestamp: string;
}

export interface SimulationMessage {
  role: 'student' | 'patient';
  content: string;
  timestamp: string;
  emotional_state?: EmotionalState;
}

// API Request/Response Types

export interface StartSimulationRequest {
  specialty: string;
  difficulty: string;
  year_level: string;
}

export interface StartSimulationResponse {
  case_id: string;
  patient_info: PatientInfo;
  avatar_path: string;
  setting_context: string;
  initial_message: string;
}

export interface SendMessageRequest {
  case_id: string;
  student_message: string;
}

export interface SendMessageResponse {
  patient_response: string;
  emotional_state: EmotionalState;
  rapport_level: RapportLevel;
  tutor_feedback: TutorFeedback[];
  avatar_path: string;
}

export interface CompleteSimulationRequest {
  case_id: string;
  diagnosis: string;
  reasoning: string;
}

export interface CognitiveAutopsy {
  mental_model: string;
  breaking_point: string;
  what_you_missed: string[];
  why_you_missed_it: string;
  pattern_across_cases?: string;
  prediction: string;
}

export interface EvaluationMetrics {
  empathy_score: number;
  communication_quality: number;
  clinical_reasoning: number;
  open_ended_questions: number;
  acknowledged_distress: boolean;
  bedside_manner: number;
}

export interface CompleteSimulationResponse {
  correct_diagnosis: string;
  diagnosis_correct: boolean;
  cognitive_autopsy: CognitiveAutopsy;
  evaluation: EvaluationMetrics;
}
