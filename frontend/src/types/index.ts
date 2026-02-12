// Patient & Case Types
export interface Patient {
  age: number;
  gender: string;
  location: string;
  occupation?: string;
}

export interface VitalSigns {
  bp: string;
  hr: number;
  rr: number;
  temp: number;
  spo2: number;
}

export interface CaseStage {
  stage: 'initial' | 'history' | 'physical_exam' | 'labs' | 'imaging' | 'diagnosis';
  info: string;
  revealed: boolean;
}

export interface MedicalCase {
  id: string;
  patient: Patient;
  chiefComplaint: string;
  initialPresentation: string;
  vitalSigns: VitalSigns;
  stages: CaseStage[];
  diagnosis: string;
  differentials: string[];
  learningPoints: string[];
  atypicalFeatures: string;
  specialty: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
}

// Student Types
export interface StudentProfile {
  id: string;
  name: string;
  yearLevel: 'final_year' | 'intern' | 'resident';
  casesCompleted: number;
  accuracy: number;
  avgTime: number;
  percentile: number;
  specialtyScores: Record<string, number>;
  weakAreas: string[];
}

// Bias Types
export interface CognitiveBias {
  type: 'anchoring' | 'premature_closure' | 'availability' | 'confirmation';
  severity: 'low' | 'moderate' | 'high';
  evidence: string;
  recommendation: string;
  score: number;
}

export interface BiasReport {
  biasesDetected: CognitiveBias[];
  casesAnalyzed: number;
  overallAccuracy: number;
  generatedAt: string;
}

// Knowledge Graph Types
export interface GraphNode {
  id: string;
  strength: number;
  size: number;
  category?: string;
}

export interface GraphLink {
  source: string;
  target: string;
  strength: number;
}

export interface KnowledgeGraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

// Chat/Tutor Types
export interface Message {
  id: string;
  role: 'student' | 'ai';
  content: string;
  timestamp: Date;
}

// Action Types
export interface CaseAction {
  type: 'check_vitals' | 'take_history' | 'physical_exam' | 'order_labs' | 'order_imaging' | 'make_diagnosis';
  label: string;
  icon: string;
}

// Recommendation Types
export interface CaseRecommendation {
  type: 'weak_area' | 'bias_counter' | 'challenge' | 'review';
  specialty: string;
  difficulty: string;
  reason: string;
  priority: 'high' | 'medium' | 'low';
}

// Specialty Types
export interface Specialty {
  id: string;
  name: string;
  icon: string;
  casesAvailable: number;
  description: string;
}
