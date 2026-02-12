/**
 * API client for Bias Detection endpoints
 */
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface ConversationMessage {
  role: string; // student or patient
  content: string;
  timestamp: string;
}

export interface BiasDetectionRequest {
  case_id: string;
  conversation_history: ConversationMessage[];
  patient_profile: {
    name: string;
    chief_complaint: string;
    actual_diagnosis: string;
  };
}

export interface BiasDetectionResponse {
  bias_detected: boolean;
  bias_type?: string; // anchoring, premature_closure, confirmation_bias
  confidence?: number; // 0.0 to 1.0
  explanation?: string;
  intervention_message?: string;
  reflection_questions?: string[];
}

export const biasApi = {
  /**
   * Detect cognitive bias in real-time during simulation
   */
  async detectBias(request: BiasDetectionRequest): Promise<BiasDetectionResponse> {
    const response = await api.post<BiasDetectionResponse>('/api/bias/detect', request);
    return response.data;
  },

  /**
   * Health check for bias detection endpoint
   */
  async healthCheck(): Promise<any> {
    const response = await api.get('/api/bias/health');
    return response.data;
  },
};
