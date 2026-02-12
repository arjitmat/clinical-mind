import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Button, Card, Badge, Input } from '../components/ui';
import type { Message } from '../types';
import { generateCase, submitDiagnosis, sendTutorMessage, type GeneratedCase, type DiagnosisResult } from '../hooks/useApi';

const stageLabels: Record<string, string> = {
  history: 'History',
  physical_exam: 'Physical Examination',
  labs: 'Investigations',
};

const stageIcons: Record<string, string> = {
  history: '📋',
  physical_exam: '🩺',
  labs: '🔬',
};

export const CaseInterface: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [caseData, setCaseData] = useState<GeneratedCase | null>(null);
  const [loadingCase, setLoadingCase] = useState(true);
  const [revealedStages, setRevealedStages] = useState<Set<number>>(new Set());
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'ai',
      content: "I see you've started a new case. Take a look at the patient presentation and vital signs. What's your initial assessment? What differential diagnoses come to mind?",
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [sendingMessage, setSendingMessage] = useState(false);
  const [showDiagnosis, setShowDiagnosis] = useState(false);
  const [studentDiagnosis, setStudentDiagnosis] = useState('');
  const [showDiagnosisInput, setShowDiagnosisInput] = useState(false);
  const [diagnosisResult, setDiagnosisResult] = useState<DiagnosisResult | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Load or generate case
  useEffect(() => {
    setLoadingCase(true);
    // Generate a new case from the backend (the id is just a route param)
    const specialty = 'cardiology'; // default
    const difficulty = 'intermediate';
    generateCase(specialty, difficulty)
      .then((data) => setCaseData(data))
      .catch(() => setCaseData(null))
      .finally(() => setLoadingCase(false));
  }, [id]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const revealStage = (index: number) => {
    setRevealedStages((prev) => new Set(prev).add(index));
  };

  const sendMessage = async () => {
    if (!inputValue.trim() || !caseData) return;

    const studentMsg: Message = {
      id: Date.now().toString(),
      role: 'student',
      content: inputValue,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, studentMsg]);
    setInputValue('');
    setSendingMessage(true);

    try {
      const res = await sendTutorMessage(caseData.id, inputValue);
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: 'ai',
        content: res.response,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiResponse]);
    } catch {
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: 'ai',
        content: "Good thinking. Can you explain your reasoning further? What evidence supports your hypothesis?",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiResponse]);
    } finally {
      setSendingMessage(false);
    }
  };

  const handleSubmitDiagnosis = async () => {
    if (!studentDiagnosis.trim() || !caseData) return;
    setShowDiagnosis(true);

    try {
      const result = await submitDiagnosis(caseData.id, studentDiagnosis, '');
      setDiagnosisResult(result);

      const aiMsg: Message = {
        id: Date.now().toString(),
        role: 'ai',
        content: result.feedback,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch {
      const aiMsg: Message = {
        id: Date.now().toString(),
        role: 'ai',
        content: `You diagnosed: "${studentDiagnosis}". Review the case details and learning points for feedback.`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiMsg]);
    }
  };

  if (loadingCase) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-20 text-center">
        <div className="animate-pulse text-lg text-text-tertiary">Generating your case...</div>
      </div>
    );
  }

  if (!caseData) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-20 text-center">
        <p className="text-lg text-terracotta mb-4">Failed to load case</p>
        <Button onClick={() => navigate('/cases')}>Back to Cases</Button>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      {/* Case Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <Badge variant={caseData.difficulty === 'beginner' ? 'success' : caseData.difficulty === 'advanced' ? 'error' : 'warning'}>
              {caseData.difficulty.charAt(0).toUpperCase() + caseData.difficulty.slice(1)}
            </Badge>
            <Badge variant="info">{caseData.specialty}</Badge>
          </div>
          <h1 className="text-xl md:text-2xl font-bold text-text-primary">
            {caseData.chief_complaint}
          </h1>
        </div>
        <Button variant="tertiary" onClick={() => navigate('/cases')}>
          Exit Case
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Case Area (2/3) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Patient Card */}
          <Card padding="lg">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-14 h-14 bg-soft-blue/10 rounded-2xl flex items-center justify-center text-2xl">
                👤
              </div>
              <div>
                <h2 className="text-lg font-semibold text-text-primary">
                  {caseData.patient.age}-year-old {caseData.patient.gender}
                </h2>
                <p className="text-sm text-text-tertiary">{caseData.patient.location}</p>
              </div>
            </div>
            <div className="bg-warm-gray-50 rounded-xl p-4 mb-4">
              <span className="text-sm font-medium text-text-tertiary block mb-1">Chief Complaint</span>
              <p className="text-base text-text-primary font-medium">{caseData.chief_complaint}</p>
            </div>
            <p className="text-base text-text-secondary leading-relaxed">
              {caseData.initial_presentation}
            </p>
          </Card>

          {/* Vital Signs */}
          <Card padding="md">
            <h3 className="text-base font-semibold text-text-primary mb-4">Vital Signs</h3>
            <div className="grid grid-cols-5 gap-4">
              {[
                { label: 'BP', value: caseData.vital_signs.bp, unit: 'mmHg' },
                { label: 'HR', value: caseData.vital_signs.hr, unit: 'bpm' },
                { label: 'RR', value: caseData.vital_signs.rr, unit: '/min' },
                { label: 'Temp', value: caseData.vital_signs.temp, unit: '°C' },
                { label: 'SpO2', value: caseData.vital_signs.spo2, unit: '%' },
              ].map((vital) => (
                <div key={vital.label} className="text-center bg-warm-gray-50 rounded-xl p-3">
                  <div className="text-sm text-text-tertiary mb-1">{vital.label}</div>
                  <div className="text-lg font-bold text-text-primary">{vital.value}</div>
                  <div className="text-xs text-text-tertiary">{vital.unit}</div>
                </div>
              ))}
            </div>
          </Card>

          {/* Action Buttons - Reveal Stages */}
          <div className="space-y-4">
            {caseData.stages.map((stage, index) => (
              <div key={stage.stage}>
                {!revealedStages.has(index) ? (
                  <Button
                    variant="secondary"
                    className="w-full justify-start"
                    onClick={() => revealStage(index)}
                  >
                    <span className="mr-2">{stageIcons[stage.stage] || '📄'}</span>
                    {stageLabels[stage.stage] || stage.stage}
                  </Button>
                ) : (
                  <Card padding="md" className="animate-fade-in-up">
                    <h3 className="text-base font-semibold text-text-primary mb-3 flex items-center gap-2">
                      <span>{stageIcons[stage.stage] || '📄'}</span>
                      {stageLabels[stage.stage] || stage.stage}
                    </h3>
                    <p className="text-base text-text-secondary leading-relaxed whitespace-pre-line">
                      {stage.info}
                    </p>
                  </Card>
                )}
              </div>
            ))}
          </div>

          {/* Diagnosis Section */}
          {revealedStages.size >= 2 && !showDiagnosis && (
            <Card padding="lg" className="border-forest-green/30">
              {!showDiagnosisInput ? (
                <div className="text-center">
                  <h3 className="text-lg font-semibold text-text-primary mb-2">Ready to diagnose?</h3>
                  <p className="text-base text-text-secondary mb-4">
                    You've gathered enough information. Make your diagnosis.
                  </p>
                  <Button onClick={() => setShowDiagnosisInput(true)}>Make Diagnosis</Button>
                </div>
              ) : (
                <div>
                  <h3 className="text-lg font-semibold text-text-primary mb-4">Your Diagnosis</h3>
                  <Input
                    placeholder="Enter your diagnosis..."
                    value={studentDiagnosis}
                    onChange={setStudentDiagnosis}
                    onKeyPress={(e) => e.key === 'Enter' && handleSubmitDiagnosis()}
                  />
                  <div className="mt-4 flex gap-3">
                    <Button onClick={handleSubmitDiagnosis}>Submit Diagnosis</Button>
                    <Button variant="tertiary" onClick={() => setShowDiagnosisInput(false)}>
                      Gather More Info
                    </Button>
                  </div>
                </div>
              )}
            </Card>
          )}

          {/* Diagnosis Result */}
          {showDiagnosis && (
            <Card padding="lg" className="border-forest-green animate-fade-in-up">
              <h3 className="text-lg font-semibold text-forest-green mb-4">Case Complete</h3>
              <div className="space-y-4">
                {diagnosisResult && (
                  <div className="bg-warm-gray-50 rounded-xl p-4">
                    <div className="flex items-center gap-3 mb-2">
                      <Badge variant={diagnosisResult.is_correct ? 'success' : 'warning'}>
                        {diagnosisResult.accuracy_score}% Accuracy
                      </Badge>
                    </div>
                    <p className="text-base text-text-secondary">{diagnosisResult.feedback}</p>

                    {diagnosisResult.reasoning_strengths?.length > 0 && (
                      <div className="mt-3">
                        <span className="text-sm font-medium text-forest-green">Strengths:</span>
                        <ul className="text-sm text-text-secondary mt-1 list-disc list-inside">
                          {diagnosisResult.reasoning_strengths.map((s, i) => <li key={i}>{s}</li>)}
                        </ul>
                      </div>
                    )}

                    {diagnosisResult.reasoning_gaps?.length > 0 && (
                      <div className="mt-3">
                        <span className="text-sm font-medium text-terracotta">Gaps to review:</span>
                        <ul className="text-sm text-text-secondary mt-1 list-disc list-inside">
                          {diagnosisResult.reasoning_gaps.map((g, i) => <li key={i}>{g}</li>)}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

                <div className="bg-forest-green/5 rounded-xl p-4">
                  <span className="text-sm font-medium text-forest-green block mb-1">Correct Diagnosis</span>
                  <p className="text-base font-semibold text-text-primary">
                    {diagnosisResult?.correct_diagnosis || caseData.diagnosis}
                  </p>
                </div>
                <div>
                  <span className="text-sm font-medium text-text-tertiary block mb-2">Key Differentials</span>
                  <div className="flex flex-wrap gap-2">
                    {(diagnosisResult?.differentials || caseData.differentials).map((d) => (
                      <Badge key={d} variant="default">{d}</Badge>
                    ))}
                  </div>
                </div>

                {caseData.learning_points && caseData.learning_points.length > 0 && (
                  <div>
                    <span className="text-sm font-medium text-text-tertiary block mb-2">Learning Points</span>
                    <ul className="text-sm text-text-secondary list-disc list-inside space-y-1">
                      {caseData.learning_points.map((lp, i) => <li key={i}>{lp}</li>)}
                    </ul>
                  </div>
                )}

                <div className="flex gap-3 pt-2">
                  <Button onClick={() => navigate('/cases')}>Next Case</Button>
                  <Button variant="secondary" onClick={() => navigate('/dashboard')}>
                    View Dashboard
                  </Button>
                </div>
              </div>
            </Card>
          )}
        </div>

        {/* AI Tutor Sidebar (1/3) */}
        <div className="lg:col-span-1">
          <div className="sticky top-24">
            <Card padding="md" className="h-[calc(100vh-8rem)] flex flex-col">
              <div className="flex items-center gap-3 mb-4 pb-4 border-b border-warm-gray-100">
                <div className="w-10 h-10 bg-forest-green/10 rounded-xl flex items-center justify-center">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2D5C3F" strokeWidth="2">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                  </svg>
                </div>
                <div>
                  <h3 className="text-base font-semibold text-text-primary">AI Tutor</h3>
                  <p className="text-xs text-text-tertiary">Socratic reasoning coach</p>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto space-y-3 mb-4">
                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`p-3 rounded-xl text-sm leading-relaxed ${
                      msg.role === 'ai'
                        ? 'bg-forest-green/5 border border-forest-green/10 text-text-primary'
                        : 'bg-warm-gray-50 border border-warm-gray-100 text-text-primary ml-4'
                    }`}
                  >
                    {msg.content}
                  </div>
                ))}
                {sendingMessage && (
                  <div className="p-3 rounded-xl text-sm bg-forest-green/5 border border-forest-green/10 text-text-tertiary animate-pulse">
                    Thinking...
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>

              <div className="mt-auto">
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Type your reasoning..."
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                    disabled={sendingMessage}
                    className="flex-1 p-3 rounded-xl border-[1.5px] border-warm-gray-100 bg-cream-white text-sm text-text-primary placeholder:text-text-tertiary focus:outline-none focus:border-forest-green transition-colors disabled:opacity-50"
                  />
                  <Button size="sm" onClick={sendMessage} disabled={sendingMessage}>
                    Send
                  </Button>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};
