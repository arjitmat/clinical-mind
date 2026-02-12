/**
 * SimulationInterface Page
 * Main interface for AI Patient Simulation
 */
import React, { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { simulationApi } from '../services/simulationApi';
import { profileApi } from '../services/profileApi';
import { biasApi } from '../services/biasApi';
import type { StudentProfile } from '../components/ProfileModal';
import ChatMessage from '../components/ChatMessage';
import PatientCard from '../components/PatientCard';
import AITutorPanel from '../components/AITutorPanel';
import { BiasInterruptModal } from '../components/BiasInterruptModal';
import type {
  SimulationMessage,
  TutorFeedback,
  EmotionalState,
  RapportLevel,
  PatientInfo,
} from '../types/simulation';

const SimulationInterface: React.FC = () => {
  const location = useLocation();

  // Simulation state
  const [caseId, setCaseId] = useState<string | null>(null);
  const [patientInfo, setPatientInfo] = useState<PatientInfo | null>(null);
  const [settingContext, setSettingContext] = useState<string>('');
  const [avatarPath, setAvatarPath] = useState<string>('');
  const [emotionalState, setEmotionalState] = useState<EmotionalState>('concerned');
  const [rapportLevel, setRapportLevel] = useState<RapportLevel>(3);

  // Case selection from profile
  const [selectedSpecialty, setSelectedSpecialty] = useState<string>('general_medicine');
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('intermediate');
  const [caseSelectionMessage, setCaseSelectionMessage] = useState<string>('');

  // Messages & feedback
  const [messages, setMessages] = useState<SimulationMessage[]>([]);
  const [tutorFeedback, setTutorFeedback] = useState<TutorFeedback[]>([]);

  // UI state
  const [loading, setLoading] = useState(false);
  const [inputMessage, setInputMessage] = useState('');
  const [isSimulationStarted, setIsSimulationStarted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Bias detection state
  const [biasModalOpen, setBiasModalOpen] = useState(false);
  const [detectedBiasType, setDetectedBiasType] = useState('');
  const [biasInterventionMessage, setBiasInterventionMessage] = useState('');
  const [biasReflectionQuestions, setBiasReflectionQuestions] = useState<string[]>([]);
  const [messageCountSinceLastCheck, setMessageCountSinceLastCheck] = useState(0);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Check for profile-based case selection on mount
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const isNew = searchParams.get('new') === 'true';

    if (isNew) {
      // Read profile from localStorage
      const profileStr = localStorage.getItem('studentProfile');
      if (profileStr) {
        try {
          const profile: StudentProfile = JSON.parse(profileStr);

          // Call profile API to select case
          profileApi
            .selectCase({
              profile: {
                yearLevel: profile.yearLevel,
                comfortableSpecialties: profile.comfortableSpecialties,
                setting: profile.setting,
              },
              feature: 'simulation',
            })
            .then((result) => {
              setSelectedSpecialty(result.specialty);
              setSelectedDifficulty(result.difficulty);
              setCaseSelectionMessage(result.why_selected);
            })
            .catch((err) => {
              console.error('Failed to select case from profile:', err);
              // Fall back to defaults if API fails
            });
        } catch (err) {
          console.error('Failed to parse profile:', err);
        }
      }
    }
  }, [location]);

  /**
   * Start a new simulation
   */
  const handleStartSimulation = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await simulationApi.startSimulation({
        specialty: selectedSpecialty,
        difficulty: selectedDifficulty,
        year_level: 'final_year', // This can be derived from profile if needed
      });

      setCaseId(response.case_id);
      setPatientInfo(response.patient_info);
      setSettingContext(response.setting_context);
      setAvatarPath(response.avatar_path);

      // Add initial patient message
      setMessages([
        {
          role: 'patient',
          content: response.initial_message,
          timestamp: new Date().toISOString(),
          emotional_state: emotionalState,
        },
      ]);

      setIsSimulationStarted(true);

      // Focus input
      setTimeout(() => inputRef.current?.focus(), 100);
    } catch (err: any) {
      setError(err.message || 'Failed to start simulation');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Send student message
   */
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!inputMessage.trim() || !caseId) return;

    const studentMessage = inputMessage.trim();
    setInputMessage('');
    setLoading(true);
    setError(null);

    // Add student message immediately (optimistic update)
    const newStudentMessage: SimulationMessage = {
      role: 'student',
      content: studentMessage,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, newStudentMessage]);

    try {
      const response = await simulationApi.sendMessage({
        case_id: caseId,
        student_message: studentMessage,
      });

      // Update state
      setEmotionalState(response.emotional_state);
      setRapportLevel(response.rapport_level);
      setAvatarPath(response.avatar_path);

      // Add patient response
      const patientMessage: SimulationMessage = {
        role: 'patient',
        content: response.patient_response,
        timestamp: new Date().toISOString(),
        emotional_state: response.emotional_state,
      };

      setMessages((prev) => {
        const updatedMessages = [...prev, patientMessage];

        // Check for bias every 3 messages
        setMessageCountSinceLastCheck((count) => {
          const newCount = count + 1;
          if (newCount >= 3) {
            // Run bias check asynchronously
            checkForBias(updatedMessages);
            return 0;
          }
          return newCount;
        });

        return updatedMessages;
      });

      // Add tutor feedback
      setTutorFeedback((prev) => [...prev, ...response.tutor_feedback]);
    } catch (err: any) {
      setError(err.message || 'Failed to send message');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Complete simulation (for later implementation)
   */
  const handleCompleteSimulation = () => {
    // TODO: Navigate to diagnosis page
    console.log('Complete simulation');
  };

  /**
   * Check for cognitive bias in student's conversation
   */
  const checkForBias = async (conversationHistory: SimulationMessage[]) => {
    if (!caseId || !patientInfo) return;

    try {
      // Convert messages to API format
      const conversationMessages = conversationHistory.map((msg) => ({
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp,
      }));

      const response = await biasApi.detectBias({
        case_id: caseId,
        conversation_history: conversationMessages,
        patient_profile: {
          name: patientInfo.name,
          chief_complaint: patientInfo.chief_complaint,
          actual_diagnosis: 'Withheld', // Not revealed during simulation
        },
      });

      if (response.bias_detected && response.intervention_message && response.reflection_questions) {
        setDetectedBiasType(response.bias_type || 'cognitive_bias');
        setBiasInterventionMessage(response.intervention_message);
        setBiasReflectionQuestions(response.reflection_questions);
        setBiasModalOpen(true);
      }
    } catch (err) {
      console.error('Bias detection failed:', err);
      // Don't block simulation on bias detection errors
    }
  };

  /**
   * Handle student's reflection on detected bias
   */
  const handleBiasReflection = (reflections: string[]) => {
    console.log('Student reflections:', reflections);
    // TODO: Log reflections to backend for analytics
    setBiasModalOpen(false);
    setMessageCountSinceLastCheck(0);
  };

  // Render loading state
  if (!isSimulationStarted) {
    return (
      <div className="min-h-screen bg-cream-white flex items-center justify-center p-8">
        <div className="max-w-md w-full text-center">
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-text-primary mb-4">
              AI Patient Simulation
            </h1>
            <p className="text-lg text-text-secondary">
              Practice clinical communication with realistic AI patients
            </p>
          </div>

          {caseSelectionMessage && (
            <div className="mb-6 p-4 bg-forest-green/10 border border-forest-green/20 rounded-xl text-text-secondary text-sm">
              <p className="font-semibold text-forest-green mb-1">Case Selected for You:</p>
              <p>{caseSelectionMessage}</p>
            </div>
          )}

          <button
            onClick={handleStartSimulation}
            disabled={loading}
            className="w-full bg-forest-green hover:bg-forest-green-dark text-cream-white font-semibold py-4 px-8 rounded-xl transition-all duration-300 hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Starting Simulation...' : 'Start New Case'}
          </button>

          {error && (
            <div className="mt-4 p-4 bg-error/10 border border-error/20 rounded-xl text-error text-sm">
              {error}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Render simulation interface
  return (
    <div className="min-h-screen bg-cream-white">
      {/* Header */}
      <header className="bg-white border-b border-warm-gray-200 px-8 py-4 shadow-sm">
        <div className="max-w-screen-2xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-text-primary">AI Patient Simulation</h1>
            {patientInfo && (
              <p className="text-sm text-text-secondary mt-1">
                Case: {patientInfo.chief_complaint}
              </p>
            )}
          </div>
          <button
            onClick={handleCompleteSimulation}
            className="bg-terracotta hover:bg-terracotta/90 text-cream-white font-medium py-2 px-6 rounded-lg transition-all duration-300"
          >
            Complete Case
          </button>
        </div>
      </header>

      {/* Main Layout */}
      <div className="max-w-screen-2xl mx-auto p-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left: Patient Card (1/3) */}
          <div className="lg:col-span-1">
            {patientInfo && (
              <div className="sticky top-8">
                <PatientCard
                  patientInfo={patientInfo}
                  emotionalState={emotionalState}
                  rapportLevel={rapportLevel}
                  avatarPath={avatarPath}
                  settingContext={settingContext}
                />
              </div>
            )}
          </div>

          {/* Middle: Chat (1/3) */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-2xl shadow-sm border border-warm-gray-100 h-[calc(100vh-200px)] flex flex-col">
              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-6">
                {messages.map((msg, index) => (
                  <ChatMessage key={index} message={msg} index={index} />
                ))}
                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <div className="border-t border-warm-gray-200 p-6">
                <form onSubmit={handleSendMessage} className="flex gap-3">
                  <input
                    ref={inputRef}
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    placeholder="Type your message to the patient..."
                    disabled={loading}
                    className="flex-1 px-4 py-3 bg-warm-gray-50 border border-warm-gray-200 rounded-xl text-text-primary placeholder-text-tertiary focus:outline-none focus:ring-2 focus:ring-forest-green focus:border-transparent transition-all duration-300"
                  />
                  <button
                    type="submit"
                    disabled={loading || !inputMessage.trim()}
                    className="bg-forest-green hover:bg-forest-green-dark text-cream-white font-medium px-6 py-3 rounded-xl transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? '...' : 'Send'}
                  </button>
                </form>
              </div>
            </div>
          </div>

          {/* Right: AI Tutor (1/3) */}
          <div className="lg:col-span-1">
            <div className="sticky top-8">
              <AITutorPanel feedback={tutorFeedback} />
            </div>
          </div>
        </div>
      </div>

      {/* Error Toast */}
      {error && (
        <div className="fixed bottom-8 right-8 max-w-md p-4 bg-error text-cream-white rounded-xl shadow-lg animate-fade-in-up">
          <div className="flex items-center gap-2">
            <span className="text-lg">✗</span>
            <span className="font-medium">{error}</span>
          </div>
        </div>
      )}

      {/* Bias Interrupt Modal */}
      <BiasInterruptModal
        isOpen={biasModalOpen}
        biasType={detectedBiasType}
        interventionMessage={biasInterventionMessage}
        reflectionQuestions={biasReflectionQuestions}
        onContinue={handleBiasReflection}
      />
    </div>
  );
};

export default SimulationInterface;
