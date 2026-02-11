import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, Badge, Input } from '../components/ui';
import type { Message, VitalSigns } from '../types';

interface CaseData {
  patient: { age: number; gender: string; location: string };
  chiefComplaint: string;
  initialPresentation: string;
  vitalSigns: VitalSigns;
  stages: { stage: string; info: string; revealed: boolean }[];
  diagnosis: string;
  differentials: string[];
}

const sampleCase: CaseData = {
  patient: { age: 28, gender: 'Male', location: 'Mumbai' },
  chiefComplaint: 'Acute onset chest pain radiating to left arm',
  initialPresentation:
    'A 28-year-old male software engineer presents to the ED at 2 AM with crushing chest pain that started 45 minutes ago while he was sleeping. He appears anxious, diaphoretic, and is clutching his chest. He denies any previous cardiac history but mentions significant work stress and recent cocaine use at a party.',
  vitalSigns: { bp: '160/95', hr: 110, rr: 22, temp: 37.2, spo2: 96 },
  stages: [
    {
      stage: 'history',
      info: 'Pain started suddenly, woke him from sleep. Severity: 8/10, crushing quality. Radiates to left arm and jaw. Associated with nausea and sweating. He admits to cocaine use ~3 hours ago. No prior cardiac history. Family history: father had MI at age 52. Smokes 5 cigarettes/day. No diabetes, hypertension on medications.',
      revealed: false,
    },
    {
      stage: 'physical_exam',
      info: 'Alert, anxious, diaphoretic. Cardiovascular: Tachycardic, regular rhythm, no murmurs. S1/S2 normal. JVP not elevated. Chest: Clear bilateral air entry. Abdomen: Soft, non-tender. Extremities: No edema. Pupils dilated bilaterally (? cocaine effect).',
      revealed: false,
    },
    {
      stage: 'labs',
      info: 'ECG: Sinus tachycardia, ST elevation in leads II, III, aVF (inferior leads). Troponin I: 0.8 ng/mL (elevated, normal <0.04). CBC: Normal. BMP: Normal. Urine drug screen: Positive for cocaine. CXR: Normal cardiac silhouette, clear lung fields.',
      revealed: false,
    },
  ],
  diagnosis: 'Cocaine-induced acute coronary syndrome (inferior STEMI)',
  differentials: [
    'Acute coronary syndrome (STEMI)',
    'Cocaine-induced coronary vasospasm',
    'Aortic dissection',
    'Pulmonary embolism',
    'Pericarditis',
  ],
};

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

const tutorResponses = [
  "Interesting choice. Before we jump to conclusions, what other diagnoses could present with chest pain and ST elevation in a young male?",
  "You're thinking about ACS, which is reasonable given the ECG. But what's unusual about this presentation? What risk factor stands out for a 28-year-old?",
  "Good - you identified the cocaine use. Now, how does cocaine cause myocardial ischemia? And importantly, how does this change your management compared to a typical STEMI?",
  "Exactly. Cocaine causes coronary vasospasm AND increases myocardial oxygen demand. This is critical because beta-blockers - typically used in ACS - are contraindicated here. Why?",
  "Correct. Unopposed alpha stimulation with beta-blockers can worsen coronary vasospasm. Benzodiazepines and nitroglycerin are first-line. You've demonstrated strong reasoning - the key learning point is: always screen for cocaine in young patients with ACS.",
];

export const CaseInterface: React.FC = () => {
  const navigate = useNavigate();
  const [caseData] = useState<CaseData>(sampleCase);
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
  const [tutorIndex, setTutorIndex] = useState(0);
  const [showDiagnosis, setShowDiagnosis] = useState(false);
  const [studentDiagnosis, setStudentDiagnosis] = useState('');
  const [showDiagnosisInput, setShowDiagnosisInput] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const revealStage = (index: number) => {
    setRevealedStages((prev) => new Set(prev).add(index));
  };

  const sendMessage = () => {
    if (!inputValue.trim()) return;

    const studentMsg: Message = {
      id: Date.now().toString(),
      role: 'student',
      content: inputValue,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, studentMsg]);
    setInputValue('');

    // Simulate AI response
    setTimeout(() => {
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: 'ai',
        content: tutorResponses[tutorIndex] || "Excellent reasoning. You've identified the key features of this case. Ready to make your diagnosis?",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiResponse]);
      setTutorIndex((prev) => prev + 1);
    }, 1200);
  };

  const submitDiagnosis = () => {
    if (!studentDiagnosis.trim()) return;
    setShowDiagnosis(true);

    const aiMsg: Message = {
      id: Date.now().toString(),
      role: 'ai',
      content: `You diagnosed: "${studentDiagnosis}". The correct diagnosis is: ${caseData.diagnosis}. ${
        studentDiagnosis.toLowerCase().includes('cocaine')
          ? "Excellent work! You correctly identified the cocaine-induced etiology, which is critical for management."
          : "Close, but the key differentiator here is the cocaine use. Always screen for substance use in young patients with ACS - it fundamentally changes your management approach."
      }`,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, aiMsg]);
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      {/* Case Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <Badge variant="warning">Intermediate</Badge>
            <Badge variant="info">Cardiology</Badge>
          </div>
          <h1 className="text-xl md:text-2xl font-bold text-text-primary">
            Chest Pain in a Young Male
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
              <p className="text-base text-text-primary font-medium">{caseData.chiefComplaint}</p>
            </div>
            <p className="text-base text-text-secondary leading-relaxed">
              {caseData.initialPresentation}
            </p>
          </Card>

          {/* Vital Signs */}
          <Card padding="md">
            <h3 className="text-base font-semibold text-text-primary mb-4">Vital Signs</h3>
            <div className="grid grid-cols-5 gap-4">
              {[
                { label: 'BP', value: caseData.vitalSigns.bp, unit: 'mmHg' },
                { label: 'HR', value: caseData.vitalSigns.hr, unit: 'bpm' },
                { label: 'RR', value: caseData.vitalSigns.rr, unit: '/min' },
                { label: 'Temp', value: caseData.vitalSigns.temp, unit: '°C' },
                { label: 'SpO2', value: caseData.vitalSigns.spo2, unit: '%' },
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
                    <span className="mr-2">{stageIcons[stage.stage]}</span>
                    {stageLabels[stage.stage] || stage.stage}
                  </Button>
                ) : (
                  <Card padding="md" className="animate-fade-in-up">
                    <h3 className="text-base font-semibold text-text-primary mb-3 flex items-center gap-2">
                      <span>{stageIcons[stage.stage]}</span>
                      {stageLabels[stage.stage]}
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
                    onKeyPress={(e) => e.key === 'Enter' && submitDiagnosis()}
                  />
                  <div className="mt-4 flex gap-3">
                    <Button onClick={submitDiagnosis}>Submit Diagnosis</Button>
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
                <div className="bg-forest-green/5 rounded-xl p-4">
                  <span className="text-sm font-medium text-forest-green block mb-1">Correct Diagnosis</span>
                  <p className="text-base font-semibold text-text-primary">{caseData.diagnosis}</p>
                </div>
                <div>
                  <span className="text-sm font-medium text-text-tertiary block mb-2">Key Differentials</span>
                  <div className="flex flex-wrap gap-2">
                    {caseData.differentials.map((d) => (
                      <Badge key={d} variant="default">{d}</Badge>
                    ))}
                  </div>
                </div>
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
                    className="flex-1 p-3 rounded-xl border-[1.5px] border-warm-gray-100 bg-cream-white text-sm text-text-primary placeholder:text-text-tertiary focus:outline-none focus:border-forest-green transition-colors"
                  />
                  <Button size="sm" onClick={sendMessage}>
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
