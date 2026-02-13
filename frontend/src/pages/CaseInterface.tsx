import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { Button, Card, Badge, Input } from '../components/ui';
import { AgentMessage, type AgentMessageData } from '../components/case/AgentMessage';
import {
  fetchCase,
  generateCase,
  submitDiagnosis,
  initializeAgents,
  sendAgentAction,
  advanceSimulationTime,
  type GeneratedCase,
  type DiagnosisResult,
  type VitalsData,
  type InvestigationItem,
  type TimelineEvent,
} from '../hooks/useApi';

const stageLabels: Record<string, string> = {
  history: 'History',
  physical_exam: 'Physical Examination',
  labs: 'Investigations',
};

const stageIcons: Record<string, string> = {
  history: '\u{1F4CB}',
  physical_exam: '\u{1FA7A}',
  labs: '\u{1F52C}',
};

type ActionMode = 'talk_to_patient' | 'ask_nurse' | 'consult_senior' | 'examine_patient' | 'order_investigation' | 'order_treatment' | 'team_huddle';

const ACTION_CONFIG: { key: ActionMode; label: string; shortLabel: string; color: string; placeholder: string }[] = [
  { key: 'talk_to_patient', label: 'Talk to Patient', shortLabel: 'Patient', color: 'amber', placeholder: 'Ask the patient about their symptoms...' },
  { key: 'ask_nurse', label: 'Ask Nurse', shortLabel: 'Nurse', color: 'blue', placeholder: 'Ask Nurse Priya about vitals, observations...' },
  { key: 'consult_senior', label: 'Consult Senior', shortLabel: 'Dr. Sharma', color: 'emerald', placeholder: 'Discuss your clinical reasoning...' },
  { key: 'examine_patient', label: 'Examine', shortLabel: 'Examine', color: 'purple', placeholder: 'What do you want to examine? (e.g., cardiovascular system)' },
  { key: 'order_investigation', label: 'Order Test', shortLabel: 'Investigate', color: 'cyan', placeholder: 'Order investigation (e.g., CBC, ECG, chest X-ray)' },
  { key: 'order_treatment', label: 'Order Treatment', shortLabel: 'Treat', color: 'rose', placeholder: 'Order treatment (e.g., IV NS 1L stat, O2 via nasal cannula)' },
  { key: 'team_huddle', label: 'Team Huddle', shortLabel: 'Huddle', color: 'indigo', placeholder: 'Call a team discussion \u2014 all agents respond...' },
];

function formatTime(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  if (h === 0) return `${m}m`;
  return `${h}h ${m}m`;
}

function vitalColor(key: string, value: number | string): string {
  if (key === 'spo2') {
    const v = Number(value);
    if (v < 90) return 'text-red-600';
    if (v < 94) return 'text-amber-600';
    return 'text-emerald-600';
  }
  if (key === 'hr') {
    const v = Number(value);
    if (v > 120 || v < 50) return 'text-red-600';
    if (v > 100 || v < 60) return 'text-amber-600';
    return 'text-emerald-600';
  }
  if (key === 'temp') {
    const v = Number(value);
    if (v > 39) return 'text-red-600';
    if (v > 38) return 'text-amber-600';
    return 'text-emerald-600';
  }
  return 'text-text-primary';
}

function trendArrow(trend?: string): string {
  if (trend === 'rising') return '\u{2191}';
  if (trend === 'falling') return '\u{2193}';
  return '';
}

export const CaseInterface: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const [caseData, setCaseData] = useState<GeneratedCase | null>(null);
  const [loadingCase, setLoadingCase] = useState(true);
  const [revealedStages, setRevealedStages] = useState<Set<number>>(new Set());

  // Multi-agent simulation state
  const [agentSessionId, setAgentSessionId] = useState<string | null>(null);
  const [agentMessages, setAgentMessages] = useState<AgentMessageData[]>([]);
  const [activeAction, setActiveAction] = useState<ActionMode>('talk_to_patient');
  const [inputValue, setInputValue] = useState('');
  const [sendingMessage, setSendingMessage] = useState(false);

  // Simulation state
  const [vitalsData, setVitalsData] = useState<VitalsData | null>(null);
  const [investigations, setInvestigations] = useState<InvestigationItem[]>([]);
  const [, setTimeline] = useState<TimelineEvent[]>([]);

  // Diagnosis state
  const [showDiagnosis, setShowDiagnosis] = useState(false);
  const [studentDiagnosis, setStudentDiagnosis] = useState('');
  const [showDiagnosisInput, setShowDiagnosisInput] = useState(false);
  const [diagnosisResult, setDiagnosisResult] = useState<DiagnosisResult | null>(null);

  const chatEndRef = useRef<HTMLDivElement>(null);

  // Load existing case by ID, or generate new one
  useEffect(() => {
    setLoadingCase(true);
    const specialty = searchParams.get('specialty') || 'cardiology';
    const difficulty = searchParams.get('difficulty') || 'intermediate';

    if (id && id !== 'new') {
      fetchCase(id)
        .then((data) => setCaseData(data))
        .catch(() => generateCase(specialty, difficulty).then((data) => setCaseData(data)))
        .catch(() => setCaseData(null))
        .finally(() => setLoadingCase(false));
    } else {
      generateCase(specialty, difficulty)
        .then((data) => setCaseData(data))
        .catch(() => setCaseData(null))
        .finally(() => setLoadingCase(false));
    }
  }, [id, searchParams]);

  // Initialize multi-agent session once case loads
  useEffect(() => {
    if (!caseData) return;
    const studentLevel = searchParams.get('level') || 'intern';

    initializeAgents(caseData.id, studentLevel)
      .then((res) => {
        setAgentSessionId(res.session_id);
        setVitalsData(res.vitals);
        setTimeline(res.timeline || []);
        setInvestigations(res.investigations || []);
        const initialMsgs: AgentMessageData[] = res.messages.map((m, i) => ({
          id: `init-${i}`,
          agent_type: m.agent_type,
          display_name: m.display_name,
          content: m.content,
          distress_level: m.distress_level,
          urgency_level: m.urgency_level,
          timestamp: new Date(),
        }));
        setAgentMessages(initialMsgs);
      })
      .catch(() => {
        setAgentMessages([{
          id: 'fallback-1',
          agent_type: 'senior_doctor',
          display_name: 'Dr. Sharma',
          content: "Let's work through this case together. Start by examining the patient's presentation and vitals. What catches your attention?",
          timestamp: new Date(),
        }]);
      });
  }, [caseData, searchParams]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [agentMessages]);

  const updateSimState = (res: { vitals: VitalsData; timeline?: TimelineEvent[]; investigations?: InvestigationItem[] }) => {
    if (res.vitals) setVitalsData(res.vitals);
    if (res.timeline) setTimeline(res.timeline);
    if (res.investigations) setInvestigations(res.investigations);
  };

  const revealStage = (index: number) => {
    setRevealedStages((prev) => new Set(prev).add(index));
  };

  const sendMessage = async () => {
    if (!inputValue.trim() || !agentSessionId) return;

    const studentMsg: AgentMessageData = {
      id: Date.now().toString(),
      agent_type: 'student',
      display_name: 'You',
      content: inputValue,
      timestamp: new Date(),
    };
    setAgentMessages((prev) => [...prev, studentMsg]);
    const currentInput = inputValue;
    setInputValue('');
    setSendingMessage(true);

    try {
      const res = await sendAgentAction(agentSessionId, activeAction, currentInput);
      const newMsgs: AgentMessageData[] = res.messages.map((m, i) => ({
        id: `${Date.now()}-${i}`,
        agent_type: m.agent_type,
        display_name: m.display_name,
        content: m.content,
        distress_level: m.distress_level,
        urgency_level: m.urgency_level,
        timestamp: new Date(),
      }));
      setAgentMessages((prev) => [...prev, ...newMsgs]);
      updateSimState(res);
    } catch {
      setAgentMessages((prev) => [...prev, {
        id: (Date.now() + 1).toString(),
        agent_type: 'senior_doctor',
        display_name: 'Dr. Sharma',
        content: 'Good thinking. Can you explain your reasoning further?',
        timestamp: new Date(),
      }]);
    } finally {
      setSendingMessage(false);
    }
  };

  const handleWaitForResults = async () => {
    if (!agentSessionId) return;
    setSendingMessage(true);
    try {
      const res = await advanceSimulationTime(agentSessionId, 30);
      const newMsgs: AgentMessageData[] = res.messages.map((m, i) => ({
        id: `wait-${Date.now()}-${i}`,
        agent_type: m.agent_type,
        display_name: m.display_name,
        content: m.content,
        timestamp: new Date(),
      }));
      if (newMsgs.length > 0) {
        setAgentMessages((prev) => [...prev, ...newMsgs]);
      }
      updateSimState(res);
    } catch {
      // silent
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
      setAgentMessages((prev) => [...prev, {
        id: Date.now().toString(),
        agent_type: 'senior_doctor',
        display_name: 'Dr. Sharma',
        content: result.feedback,
        timestamp: new Date(),
      }]);
    } catch {
      setAgentMessages((prev) => [...prev, {
        id: Date.now().toString(),
        agent_type: 'senior_doctor',
        display_name: 'Dr. Sharma',
        content: `You diagnosed: "${studentDiagnosis}". Review the case details and learning points for feedback.`,
        timestamp: new Date(),
      }]);
    }
  };

  if (loadingCase) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-20 text-center">
        <div className="animate-pulse text-lg text-text-tertiary">Setting up the hospital ward...</div>
        <p className="text-sm text-text-tertiary mt-2">Agents are learning about this case...</p>
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

  const pendingInvestigations = investigations.filter(i => i.status !== 'ready');
  const activeConfig = ACTION_CONFIG.find(a => a.key === activeAction) || ACTION_CONFIG[0];

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      {/* Case Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <Badge variant={caseData.difficulty === 'beginner' ? 'success' : caseData.difficulty === 'advanced' ? 'error' : 'warning'}>
              {caseData.difficulty.charAt(0).toUpperCase() + caseData.difficulty.slice(1)}
            </Badge>
            <Badge variant="info">{caseData.specialty}</Badge>
            {vitalsData && (
              <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                vitalsData.trajectory === 'improving' ? 'bg-emerald-100 text-emerald-700' :
                vitalsData.trajectory === 'deteriorating' ? 'bg-red-100 text-red-700' :
                vitalsData.trajectory === 'critical' ? 'bg-red-200 text-red-800' :
                'bg-gray-100 text-gray-600'
              }`}>
                {vitalsData.trajectory}
              </span>
            )}
            {vitalsData && (
              <span className="text-xs text-text-tertiary">
                {formatTime(vitalsData.elapsed_minutes)} elapsed
              </span>
            )}
          </div>
          <h1 className="text-lg md:text-xl font-bold text-text-primary">
            {caseData.chief_complaint}
          </h1>
        </div>
        <Button variant="tertiary" onClick={() => navigate('/')}>
          Exit Case
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Main Case Area (5/12) */}
        <div className="lg:col-span-5 space-y-4">
          {/* Live Vitals Monitor */}
          <Card padding="md">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-text-primary">Live Vitals</h3>
              {vitalsData && (
                <span className={`text-xs font-medium ${
                  vitalsData.urgency_level === 'critical' ? 'text-red-600' :
                  vitalsData.urgency_level === 'urgent' ? 'text-amber-600' :
                  'text-emerald-600'
                }`}>
                  {vitalsData.urgency_level.toUpperCase()}
                </span>
              )}
            </div>
            <div className="grid grid-cols-5 gap-2">
              {[
                { label: 'BP', key: 'bp', unit: 'mmHg' },
                { label: 'HR', key: 'hr', unit: 'bpm' },
                { label: 'RR', key: 'rr', unit: '/min' },
                { label: 'Temp', key: 'temp', unit: '\u00B0C' },
                { label: 'SpO2', key: 'spo2', unit: '%' },
              ].map((vital) => {
                const v = vitalsData?.vitals || caseData.vital_signs;
                const val = (v as Record<string, unknown>)[vital.key];
                const trend = vitalsData?.trends?.[vital.key === 'bp' ? 'bp_systolic' : vital.key];
                return (
                  <div key={vital.label} className="text-center bg-warm-gray-50 rounded-lg p-2">
                    <div className="text-[10px] text-text-tertiary">{vital.label}</div>
                    <div className={`text-sm font-bold ${vitalColor(vital.key, val as number)}`}>
                      {String(val)} {trendArrow(trend)}
                    </div>
                    <div className="text-[9px] text-text-tertiary">{vital.unit}</div>
                  </div>
                );
              })}
            </div>
          </Card>

          {/* Patient Card */}
          <Card padding="md">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 bg-soft-blue/10 rounded-xl flex items-center justify-center text-xl">
                {'\u{1F464}'}
              </div>
              <div>
                <h2 className="text-sm font-semibold text-text-primary">
                  {caseData.patient.age}y {caseData.patient.gender}
                </h2>
                <p className="text-xs text-text-tertiary">{caseData.patient.location}</p>
              </div>
            </div>
            <p className="text-sm text-text-secondary leading-relaxed">
              {caseData.initial_presentation}
            </p>
          </Card>

          {/* Stage Buttons */}
          <div className="space-y-2">
            {caseData.stages.map((stage, index) => (
              <div key={stage.stage}>
                {!revealedStages.has(index) ? (
                  <Button variant="secondary" className="w-full justify-start text-sm" onClick={() => revealStage(index)}>
                    <span className="mr-2">{stageIcons[stage.stage] || '\u{1F4C4}'}</span>
                    {stageLabels[stage.stage] || stage.stage}
                  </Button>
                ) : (
                  <Card padding="sm" className="animate-fade-in-up">
                    <h3 className="text-xs font-semibold text-text-primary mb-2 flex items-center gap-1">
                      <span>{stageIcons[stage.stage] || '\u{1F4C4}'}</span>
                      {stageLabels[stage.stage] || stage.stage}
                    </h3>
                    <p className="text-xs text-text-secondary leading-relaxed whitespace-pre-line">
                      {stage.info}
                    </p>
                  </Card>
                )}
              </div>
            ))}
          </div>

          {/* Investigations Panel */}
          {investigations.length > 0 && (
            <Card padding="md">
              <h3 className="text-sm font-semibold text-text-primary mb-3">Investigations</h3>
              <div className="space-y-2">
                {investigations.map((inv) => (
                  <div key={inv.id} className={`text-xs p-2 rounded-lg ${
                    inv.status === 'ready' ? 'bg-emerald-50 border border-emerald-200' : 'bg-warm-gray-50'
                  }`}>
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{inv.label}</span>
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                        inv.status === 'ready' ? 'bg-emerald-100 text-emerald-700' :
                        inv.status === 'processing' ? 'bg-amber-100 text-amber-700' :
                        'bg-gray-100 text-gray-600'
                      }`}>
                        {inv.status === 'ready' ? 'READY' : inv.status === 'processing' ? 'Processing...' : `ETA: ${inv.remaining_minutes}m`}
                      </span>
                    </div>
                    {inv.status === 'ready' && inv.result && (
                      <p className="mt-1 text-text-secondary whitespace-pre-line">{inv.result}</p>
                    )}
                  </div>
                ))}
              </div>
              {pendingInvestigations.length > 0 && (
                <Button variant="tertiary" size="sm" className="mt-2 w-full text-xs" onClick={handleWaitForResults} disabled={sendingMessage}>
                  Wait for Results (advance 30 min)
                </Button>
              )}
            </Card>
          )}

          {/* Diagnosis Section */}
          {revealedStages.size >= 2 && !showDiagnosis && (
            <Card padding="md" className="border-forest-green/30">
              {!showDiagnosisInput ? (
                <div className="text-center">
                  <h3 className="text-sm font-semibold text-text-primary mb-1">Ready to diagnose?</h3>
                  <p className="text-xs text-text-secondary mb-3">You have gathered enough information.</p>
                  <Button size="sm" onClick={() => setShowDiagnosisInput(true)}>Make Diagnosis</Button>
                </div>
              ) : (
                <div>
                  <h3 className="text-sm font-semibold text-text-primary mb-3">Your Diagnosis</h3>
                  <Input
                    placeholder="Enter your diagnosis..."
                    value={studentDiagnosis}
                    onChange={setStudentDiagnosis}
                    onKeyPress={(e) => e.key === 'Enter' && handleSubmitDiagnosis()}
                  />
                  <div className="mt-3 flex gap-2">
                    <Button size="sm" onClick={handleSubmitDiagnosis}>Submit</Button>
                    <Button variant="tertiary" size="sm" onClick={() => setShowDiagnosisInput(false)}>
                      Back
                    </Button>
                  </div>
                </div>
              )}
            </Card>
          )}

          {/* Diagnosis Result */}
          {showDiagnosis && (
            <Card padding="md" className="border-forest-green animate-fade-in-up">
              <h3 className="text-sm font-semibold text-forest-green mb-3">Case Complete</h3>
              <div className="space-y-3">
                {diagnosisResult && (
                  <div className="bg-warm-gray-50 rounded-lg p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant={diagnosisResult.is_correct ? 'success' : 'warning'}>
                        {diagnosisResult.accuracy_score}% Accuracy
                      </Badge>
                    </div>
                    <p className="text-xs text-text-secondary">{diagnosisResult.feedback}</p>
                    {diagnosisResult.reasoning_strengths?.length > 0 && (
                      <div className="mt-2">
                        <span className="text-xs font-medium text-forest-green">Strengths:</span>
                        <ul className="text-xs text-text-secondary mt-1 list-disc list-inside">
                          {diagnosisResult.reasoning_strengths.map((s, i) => <li key={i}>{s}</li>)}
                        </ul>
                      </div>
                    )}
                    {diagnosisResult.reasoning_gaps?.length > 0 && (
                      <div className="mt-2">
                        <span className="text-xs font-medium text-terracotta">Gaps:</span>
                        <ul className="text-xs text-text-secondary mt-1 list-disc list-inside">
                          {diagnosisResult.reasoning_gaps.map((g, i) => <li key={i}>{g}</li>)}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

                <div className="bg-forest-green/5 rounded-lg p-3">
                  <span className="text-xs font-medium text-forest-green block mb-1">Correct Diagnosis</span>
                  <p className="text-sm font-semibold text-text-primary">
                    {diagnosisResult?.correct_diagnosis || caseData.diagnosis}
                  </p>
                </div>

                {caseData.learning_points && caseData.learning_points.length > 0 && (
                  <div>
                    <span className="text-xs font-medium text-text-tertiary block mb-1">Learning Points</span>
                    <ul className="text-xs text-text-secondary list-disc list-inside space-y-0.5">
                      {caseData.learning_points.map((lp, i) => <li key={i}>{lp}</li>)}
                    </ul>
                  </div>
                )}

                <div className="flex gap-2 pt-1">
                  <Button size="sm" onClick={() => navigate('/')}>Next Case</Button>
                  <Button variant="secondary" size="sm" onClick={() => navigate('/dashboard')}>Dashboard</Button>
                </div>
              </div>
            </Card>
          )}
        </div>

        {/* Multi-Agent Hospital Chat (7/12) */}
        <div className="lg:col-span-7">
          <div className="sticky top-20">
            <Card padding="md" className="h-[calc(100vh-7rem)] flex flex-col">
              {/* Header */}
              <div className="flex items-center justify-between mb-3 pb-3 border-b border-warm-gray-100">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-forest-green/10 rounded-lg flex items-center justify-center">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2D5C3F" strokeWidth="2">
                      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                      <circle cx="9" cy="7" r="4"/>
                      <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                      <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-text-primary">Hospital Ward</h3>
                    <p className="text-[10px] text-text-tertiary">Patient + Nurse Priya + Dr. Sharma</p>
                  </div>
                </div>
                {vitalsData && (
                  <div className="text-right">
                    <span className="text-[10px] text-text-tertiary block">Sim Time</span>
                    <span className="text-xs font-medium text-text-primary">{formatTime(vitalsData.elapsed_minutes)}</span>
                  </div>
                )}
              </div>

              {/* Clinical Action Tabs */}
              <div className="flex flex-wrap gap-1 mb-3 p-1 bg-warm-gray-50 rounded-lg">
                {ACTION_CONFIG.map((action) => (
                  <button
                    key={action.key}
                    onClick={() => setActiveAction(action.key)}
                    className={`text-[10px] font-medium py-1 px-2 rounded-md transition-colors ${
                      activeAction === action.key
                        ? action.color === 'amber' ? 'bg-amber-100 text-amber-800'
                        : action.color === 'blue' ? 'bg-blue-100 text-blue-800'
                        : action.color === 'emerald' ? 'bg-emerald-100 text-emerald-800'
                        : action.color === 'purple' ? 'bg-purple-100 text-purple-800'
                        : action.color === 'cyan' ? 'bg-cyan-100 text-cyan-800'
                        : action.color === 'rose' ? 'bg-rose-100 text-rose-800'
                        : 'bg-indigo-100 text-indigo-800'
                        : 'text-text-tertiary hover:text-text-secondary'
                    }`}
                  >
                    {action.shortLabel}
                  </button>
                ))}
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto space-y-2 mb-3">
                {agentMessages.map((msg) => (
                  <AgentMessage key={msg.id} message={msg} />
                ))}
                {sendingMessage && (
                  <div className="p-2 rounded-lg text-xs bg-forest-green/5 border border-forest-green/10 text-text-tertiary animate-pulse">
                    Agents are responding...
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>

              {/* Input */}
              <div className="mt-auto pt-2 border-t border-warm-gray-100">
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder={activeConfig.placeholder}
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                    disabled={sendingMessage}
                    className="flex-1 p-2.5 rounded-lg border-[1.5px] border-warm-gray-100 bg-cream-white text-sm text-text-primary placeholder:text-text-tertiary focus:outline-none focus:border-forest-green transition-colors disabled:opacity-50"
                  />
                  <Button size="sm" onClick={sendMessage} disabled={sendingMessage || !inputValue.trim()}>
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
