const API_BASE = 'http://localhost:8000/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'API request failed');
  }
  return res.json();
}

// --- Cases ---

export interface SpecialtyDTO {
  id: string;
  name: string;
  icon: string;
  cases_available: number;
  description: string;
}

export interface GeneratedCase {
  id: string;
  patient: { age: number; gender: string; location: string };
  chief_complaint: string;
  initial_presentation: string;
  vital_signs: { bp: string; hr: number; rr: number; temp: number; spo2: number };
  stages: { stage: string; info: string }[];
  diagnosis: string;
  differentials: string[];
  learning_points?: string[];
  atypical_features?: string;
  specialty: string;
  difficulty: string;
}

export interface DiagnosisResult {
  student_diagnosis: string;
  correct_diagnosis: string;
  is_correct: boolean;
  accuracy_score: number;
  differentials: string[];
  feedback: string;
  reasoning_strengths: string[];
  reasoning_gaps: string[];
  learning_points?: string[];
  suggested_review_topics?: string[];
}

export function fetchSpecialties(): Promise<{ specialties: SpecialtyDTO[] }> {
  return request('/cases/specialties');
}

export function fetchCase(caseId: string): Promise<GeneratedCase> {
  return request(`/cases/${caseId}`);
}

export function generateCase(specialty: string, difficulty: string): Promise<GeneratedCase> {
  return request('/cases/generate', {
    method: 'POST',
    body: JSON.stringify({ specialty, difficulty }),
  });
}

export function submitDiagnosis(caseId: string, diagnosis: string, reasoning: string): Promise<DiagnosisResult> {
  return request(`/cases/${caseId}/diagnose`, {
    method: 'POST',
    body: JSON.stringify({ case_id: caseId, diagnosis, reasoning }),
  });
}

// --- Tutor ---

export interface TutorResponse {
  response: string;
}

export function sendTutorMessage(caseId: string, message: string): Promise<TutorResponse> {
  return request('/cases/tutor', {
    method: 'POST',
    body: JSON.stringify({ case_id: caseId, message }),
  });
}

// --- Student ---

export interface StudentProfile {
  id: string;
  name: string;
  year_level: string;
  cases_completed: number;
  accuracy: number;
  avg_time: number;
  percentile: number;
  specialty_scores: Record<string, number>;
  weak_areas: string[];
}

export interface BiasReport {
  biases_detected: {
    type: string;
    severity: string;
    evidence: string;
    recommendation: string;
    score: number;
  }[];
  cases_analyzed: number;
  overall_accuracy: number;
}

export function fetchProfile(): Promise<StudentProfile> {
  return request('/student/profile');
}

export function fetchBiases(): Promise<BiasReport> {
  return request('/student/biases');
}

export interface KnowledgeGraphDTO {
  nodes: { id: string; strength: number; size: number; category: string }[];
  links: { source: string; target: string; strength: number }[];
}

export function fetchKnowledgeGraph(): Promise<KnowledgeGraphDTO> {
  return request('/student/knowledge-graph');
}

// --- Analytics ---

export interface PerformanceData {
  overall_accuracy: number;
  cases_completed: number;
  avg_time_minutes: number;
  peer_percentile: number;
  history: { week: string; accuracy: number; avg_time: number }[];
}

export interface RecommendationItem {
  type: string;
  specialty: string;
  difficulty: string;
  reason: string;
  priority: string;
}

export function fetchPerformance(): Promise<PerformanceData> {
  return request('/analytics/performance');
}

export function fetchRecommendations(): Promise<RecommendationItem[]> {
  return request('/analytics/recommendations');
}

// --- Multi-Agent System ---

export interface AgentMessageDTO {
  agent_type: 'patient' | 'nurse' | 'senior_doctor' | 'student';
  display_name: string;
  content: string;
  distress_level?: string;
  urgency_level?: string;
  thinking?: string;
}

export interface AgentSessionResponse {
  session_id: string;
  messages: AgentMessageDTO[];
  vitals: {
    vitals: { bp: string; hr: number; rr: number; temp: number; spo2: number };
    urgency_level: string;
    patient_distress: string;
  };
}

export function initializeAgents(caseId: string): Promise<AgentSessionResponse> {
  return request('/agents/initialize', {
    method: 'POST',
    body: JSON.stringify({ case_id: caseId }),
  });
}

export function sendAgentAction(
  sessionId: string,
  actionType: string,
  studentInput?: string,
): Promise<AgentSessionResponse> {
  return request('/agents/action', {
    method: 'POST',
    body: JSON.stringify({
      session_id: sessionId,
      action_type: actionType,
      student_input: studentInput,
    }),
  });
}

export function fetchAgentVitals(sessionId: string): Promise<AgentSessionResponse['vitals']> {
  return request(`/agents/vitals/${sessionId}`);
}
