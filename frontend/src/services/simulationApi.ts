/**
 * API client for AI Patient Simulation endpoints
 */
import axios from 'axios';
import type {
  StartSimulationRequest,
  StartSimulationResponse,
  SendMessageRequest,
  SendMessageResponse,
  CompleteSimulationRequest,
  CompleteSimulationResponse,
} from '../types/simulation';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const simulationApi = {
  /**
   * Start a new patient simulation
   */
  async startSimulation(
    request: StartSimulationRequest
  ): Promise<StartSimulationResponse> {
    const response = await api.post<StartSimulationResponse>(
      '/api/simulation/start',
      request
    );
    return response.data;
  },

  /**
   * Send a message to the patient
   */
  async sendMessage(
    request: SendMessageRequest
  ): Promise<SendMessageResponse> {
    const response = await api.post<SendMessageResponse>(
      '/api/simulation/message',
      request
    );
    return response.data;
  },

  /**
   * Complete the simulation and get cognitive autopsy
   */
  async completeSimulation(
    request: CompleteSimulationRequest
  ): Promise<CompleteSimulationResponse> {
    const response = await api.post<CompleteSimulationResponse>(
      '/api/simulation/complete',
      request
    );
    return response.data;
  },

  /**
   * Get simulation status (for debugging)
   */
  async getSimulationStatus(caseId: string): Promise<any> {
    const response = await api.get(`/api/simulation/status/${caseId}`);
    return response.data;
  },
};
