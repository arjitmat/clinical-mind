/**
 * API client for Profile-based case selection
 */
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface StudentProfile {
  yearLevel: string;
  comfortableSpecialties: string[];
  setting: string;
}

export interface CaseSelectionRequest {
  profile: StudentProfile;
  feature: string;
}

export interface CaseSelectionResponse {
  specialty: string;
  difficulty: string;
  setting: string;
  why_selected: string;
}

export const profileApi = {
  /**
   * Select case based on student profile
   */
  async selectCase(
    request: CaseSelectionRequest
  ): Promise<CaseSelectionResponse> {
    const response = await api.post<CaseSelectionResponse>(
      '/api/profile/select-case',
      request
    );
    return response.data;
  },
};
