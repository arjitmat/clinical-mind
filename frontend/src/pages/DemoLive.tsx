import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, Badge } from '../components/ui';

// Same student levels as main app
const STUDENT_LEVELS = [
  { value: 'mbbs_1st', label: 'MBBS 1st Year', description: 'Basic anatomy and physiology' },
  { value: 'mbbs_2nd', label: 'MBBS 2nd Year', description: 'Pathology and pharmacology' },
  { value: 'mbbs_3rd', label: 'MBBS 3rd Year', description: 'Clinical subjects introduction' },
  { value: 'mbbs_final', label: 'MBBS Final Year', description: 'Advanced clinical medicine' },
  { value: 'intern', label: 'Intern', description: 'Hands-on clinical training' },
  { value: 'resident', label: 'Resident', description: 'Specialized practice' },
];

// Only 2 curated cases for demo
const DEMO_CASES = [
  {
    id: 'demo-case-001',
    chief_complaint: 'Severe crushing chest pain for 2 hours',
    specialty: 'cardiology',
    difficulty: 'intermediate',
    patient: {
      age: 55,
      gender: 'Male',
      location: 'Mumbai',
    },
    presentation: '55-year-old businessman presents with severe central chest pain radiating to left arm, started while climbing stairs. Associated with profuse sweating and nausea.',
    initial_vitals: {
      bp: '90/60',
      hr: 110,
      rr: 24,
      temp: 37.2,
      spo2: 94,
    },
  },
  {
    id: 'demo-case-002',
    chief_complaint: 'High fever with body aches for 4 days',
    specialty: 'infectious_disease',
    difficulty: 'beginner',
    patient: {
      age: 28,
      gender: 'Female',
      location: 'Delhi',
    },
    presentation: '28-year-old teacher with high-grade fever, severe retro-orbital headache, myalgia. Developed petechial rash today. Multiple mosquito bites last week.',
    initial_vitals: {
      bp: '100/70',
      hr: 95,
      rr: 18,
      temp: 39.2,
      spo2: 98,
    },
  },
];

export const DemoLive: React.FC = () => {
  const navigate = useNavigate();
  const [studentName, setStudentName] = useState('');
  const [studentLevel, setStudentLevel] = useState('');
  const [showCases, setShowCases] = useState(false);

  const handleStudentSubmit = () => {
    if (!studentName.trim() || !studentLevel) return;

    // Store student info
    localStorage.setItem('studentName', studentName);
    localStorage.setItem('studentLevel', studentLevel);

    setShowCases(true);
  };

  const handleSelectCase = (caseData: typeof DEMO_CASES[0]) => {
    // Navigate to case interface with parameters
    const params = new URLSearchParams({
      specialty: caseData.specialty,
      difficulty: caseData.difficulty,
      level: studentLevel,
    });

    navigate(`/case/new?${params.toString()}`);
  };

  // Student Profile Form (same as main app)
  if (!showCases) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-20">
        <div className="text-center mb-12">
          <div className="w-20 h-20 bg-forest-green/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#2D5C3F" strokeWidth="2">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" />
              <path d="M2 17L12 22L22 17" />
              <path d="M2 12L12 17L22 12" />
            </svg>
          </div>
          <h1 className="text-4xl font-bold text-text-primary mb-4">
            Clinical<span className="text-forest-green">Mind</span>
          </h1>
          <p className="text-lg text-text-secondary">
            AI-powered medical simulation for clinical education
          </p>
        </div>

        <Card padding="lg" className="max-w-md mx-auto">
          <h2 className="text-xl font-semibold text-text-primary mb-6">Student Profile</h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">
                Your Name
              </label>
              <input
                type="text"
                value={studentName}
                onChange={(e) => setStudentName(e.target.value)}
                placeholder="Enter your name..."
                className="w-full p-3 rounded-lg border-[1.5px] border-warm-gray-100 bg-cream-white text-text-primary placeholder:text-text-tertiary focus:outline-none focus:border-forest-green transition-colors"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">
                Academic Level
              </label>
              <div className="space-y-2">
                {STUDENT_LEVELS.map((level) => (
                  <button
                    key={level.value}
                    onClick={() => setStudentLevel(level.value)}
                    className={`w-full text-left p-3 rounded-lg border-[1.5px] transition-all ${
                      studentLevel === level.value
                        ? 'border-forest-green bg-forest-green/5'
                        : 'border-warm-gray-100 hover:border-forest-green/30'
                    }`}
                  >
                    <div className="font-medium text-text-primary">{level.label}</div>
                    <div className="text-xs text-text-tertiary mt-0.5">{level.description}</div>
                  </button>
                ))}
              </div>
            </div>

            <Button
              className="w-full"
              disabled={!studentName.trim() || !studentLevel}
              onClick={handleStudentSubmit}
            >
              Continue to Cases
            </Button>
          </div>
        </Card>

        <div className="text-center mt-8">
          <p className="text-sm text-text-tertiary">
            Your progress will be tracked throughout the simulation
          </p>
        </div>
      </div>
    );
  }

  // Case Selection (limited to 2 demo cases)
  return (
    <div className="max-w-7xl mx-auto px-6 py-12">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-text-primary mb-2">Select a Case</h1>
        <p className="text-lg text-text-secondary">
          Choose a clinical case to begin your simulation
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {DEMO_CASES.map((caseData) => (
          <Card
            key={caseData.id}
            padding="lg"
            className="hover:shadow-xl transition-shadow cursor-pointer"
            onClick={() => handleSelectCase(caseData)}
          >
            <div className="flex items-start justify-between mb-4">
              <div>
                <Badge variant={caseData.difficulty === 'beginner' ? 'success' : 'warning'}>
                  {caseData.difficulty.charAt(0).toUpperCase() + caseData.difficulty.slice(1)}
                </Badge>
                <span className="ml-2">
                  <Badge variant="info">
                    {caseData.specialty.replace('_', ' ').charAt(0).toUpperCase() + caseData.specialty.replace('_', ' ').slice(1)}
                  </Badge>
                </span>
              </div>
            </div>

            <h3 className="text-lg font-semibold text-text-primary mb-3">
              {caseData.chief_complaint}
            </h3>

            <div className="space-y-2 mb-4">
              <div className="flex items-center gap-2 text-sm text-text-secondary">
                <span className="font-medium">Patient:</span>
                <span>{caseData.patient.age}y {caseData.patient.gender}, {caseData.patient.location}</span>
              </div>
              <p className="text-sm text-text-secondary">
                {caseData.presentation}
              </p>
            </div>

            <div className="border-t border-warm-gray-100 pt-3">
              <div className="text-xs text-text-tertiary">
                <span className="font-medium">Initial Vitals:</span>
                <div className="flex flex-wrap gap-2 mt-1">
                  <span>BP: {caseData.initial_vitals.bp}</span>
                  <span>•</span>
                  <span>HR: {caseData.initial_vitals.hr}</span>
                  <span>•</span>
                  <span>Temp: {caseData.initial_vitals.temp}°C</span>
                  <span>•</span>
                  <span>SpO2: {caseData.initial_vitals.spo2}%</span>
                </div>
              </div>
            </div>

            <Button variant="secondary" className="w-full mt-4">
              Start This Case
            </Button>
          </Card>
        ))}
      </div>

      <div className="mt-8 text-center">
        <Button variant="tertiary" onClick={() => setShowCases(false)}>
          Back to Profile
        </Button>
      </div>
    </div>
  );
};