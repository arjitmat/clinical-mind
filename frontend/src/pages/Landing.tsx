import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui';
import { Card } from '../components/ui';

const specialties = [
  { id: 'cardiology', name: 'Cardiology', icon: '\u{1FAC0}', cases: 12, description: 'Heart failure, ACS, arrhythmias' },
  { id: 'respiratory', name: 'Respiratory', icon: '\u{1FAC1}', cases: 10, description: 'Pneumonia, COPD, TB, asthma' },
  { id: 'infectious_diseases', name: 'Infectious Disease', icon: '\u{1F9A0}', cases: 10, description: 'Dengue, malaria, typhoid, HIV' },
  { id: 'neurology', name: 'Neurology', icon: '\u{1F9E0}', cases: 10, description: 'Stroke, meningitis, seizures' },
  { id: 'gastroenterology', name: 'Gastroenterology', icon: '\u{1F52C}', cases: 10, description: 'Liver disease, pancreatitis, GI bleeds' },
  { id: 'emergency', name: 'Emergency Medicine', icon: '\u{1F6A8}', cases: 10, description: 'Acute MI, sepsis, trauma, poisoning' },
  { id: 'endocrinology', name: 'Endocrinology', icon: '\u{1FA78}', cases: 10, description: 'Diabetes, thyroid, adrenal crises' },
  { id: 'nephrology', name: 'Nephrology', icon: '\u{1F9EA}', cases: 10, description: 'AKI, CKD, nephrotic syndrome' },
  { id: 'pediatrics', name: 'Pediatrics', icon: '\u{1F476}', cases: 10, description: 'Neonatal, febrile seizures, pneumonia' },
  { id: 'hematology', name: 'Hematology', icon: '\u{1FA78}', cases: 10, description: 'Anemia, leukemia, bleeding disorders' },
  { id: 'psychiatry', name: 'Psychiatry', icon: '\u{1F4AD}', cases: 10, description: 'Depression, schizophrenia, substance use' },
  { id: 'orthopedics', name: 'Orthopedics', icon: '\u{1F9B4}', cases: 10, description: 'Fractures, joint disorders, spine' },
  { id: 'dermatology', name: 'Dermatology', icon: '\u{1FA7A}', cases: 10, description: 'Psoriasis, infections, drug reactions' },
  { id: 'obstetrics', name: 'Obstetrics & Gynaecology', icon: '\u{1F930}', cases: 10, description: 'Eclampsia, PPH, ectopic pregnancy' },
];

const studentLevels = [
  { id: 'mbbs_2nd', label: 'MBBS 2nd Year', description: 'Pre-clinical phase \u2014 learning foundations', difficulty: 'beginner' },
  { id: 'mbbs_3rd', label: 'MBBS 3rd Year', description: 'Clinical postings \u2014 first patient contact', difficulty: 'intermediate' },
  { id: 'intern', label: 'Intern', description: 'Hands-on ward experience', difficulty: 'intermediate' },
  { id: 'pg_aspirant', label: 'NEET-PG Aspirant', description: 'Exam preparation \u2014 pattern recognition', difficulty: 'advanced' },
  { id: 'pg_resident', label: 'PG Resident', description: 'Advanced clinical reasoning', difficulty: 'advanced' },
];

const features = [
  {
    title: 'Multi-Agent Hospital Simulation',
    description: 'Patient, Nurse, and Senior Doctor AI agents that dynamically learn per case and interact with each other \u2014 like a real Indian hospital ward.',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
        <circle cx="9" cy="7" r="4"/>
        <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
        <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
      </svg>
    ),
  },
  {
    title: 'Real-Time Clinical Simulation',
    description: 'Vitals evolve, investigations take realistic time, treatments have consequences. Order the wrong drug \u2014 the nurse catches it.',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
      </svg>
    ),
  },
  {
    title: 'Socratic Teaching by Dr. Sharma',
    description: 'Never gives you the answer. Guides your reasoning through questions, just like a real ward round at AIIMS or CMC Vellore.',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
    ),
  },
  {
    title: 'India-Centric Medical Cases',
    description: '142 verified cases from Indian medical literature. ICMR, API, IAP guidelines. Government hospital reality \u2014 not textbook fantasy.',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12 22s-8-4.5-8-11.8A8 8 0 0 1 12 2a8 8 0 0 1 8 8.2c0 7.3-8 11.8-8 11.8z"/>
        <circle cx="12" cy="10" r="3"/>
      </svg>
    ),
  },
];

type OnboardingStep = 'landing' | 'select_level' | 'select_specialty';

export const Landing: React.FC = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState<OnboardingStep>('landing');
  const [selectedLevel, setSelectedLevel] = useState<string | null>(null);
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('intermediate');

  const handleStartCase = () => {
    setStep('select_level');
  };

  const handleLevelSelect = (levelId: string, difficulty: string) => {
    setSelectedLevel(levelId);
    setSelectedDifficulty(difficulty);
    setStep('select_specialty');
  };

  const handleSpecialtySelect = (specialtyId: string) => {
    navigate(`/case/new?specialty=${specialtyId}&difficulty=${selectedDifficulty}&level=${selectedLevel}`);
  };

  const handleSurpriseMe = () => {
    const randomSpec = specialties[Math.floor(Math.random() * specialties.length)];
    navigate(`/case/new?specialty=${randomSpec.id}&difficulty=${selectedDifficulty}&level=${selectedLevel}`);
  };

  // --- Onboarding: Level Selection ---
  if (step === 'select_level') {
    return (
      <div className="max-w-3xl mx-auto px-6 py-16">
        <button onClick={() => setStep('landing')} className="text-sm text-text-tertiary hover:text-text-secondary mb-8 flex items-center gap-1">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
          Back
        </button>

        <div className="text-center mb-10">
          <h2 className="text-2xl md:text-3xl font-bold text-text-primary mb-3">What year are you in?</h2>
          <p className="text-lg text-text-secondary">This adjusts the teaching style and case complexity to match your level.</p>
        </div>

        <div className="space-y-3">
          {studentLevels.map((level) => (
            <Card
              key={level.id}
              hover
              padding="lg"
              onClick={() => handleLevelSelect(level.id, level.difficulty)}
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-text-primary">{level.label}</h3>
                  <p className="text-sm text-text-secondary mt-1">{level.description}</p>
                </div>
                <div>
                  <span className={`text-xs font-medium px-2 py-1 rounded-full ${
                    level.difficulty === 'beginner' ? 'bg-emerald-100 text-emerald-700' :
                    level.difficulty === 'intermediate' ? 'bg-amber-100 text-amber-700' :
                    'bg-red-100 text-red-700'
                  }`}>
                    {level.difficulty}
                  </span>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  // --- Onboarding: Specialty Selection ---
  if (step === 'select_specialty') {
    const levelLabel = studentLevels.find(l => l.id === selectedLevel)?.label || '';
    return (
      <div className="max-w-5xl mx-auto px-6 py-16">
        <button onClick={() => setStep('select_level')} className="text-sm text-text-tertiary hover:text-text-secondary mb-8 flex items-center gap-1">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
          Back
        </button>

        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 bg-forest-green/10 text-forest-green px-3 py-1 rounded-full text-sm font-medium mb-4">
            {levelLabel}
          </div>
          <h2 className="text-2xl md:text-3xl font-bold text-text-primary mb-3">Choose a specialty</h2>
          <p className="text-lg text-text-secondary">Pick a clinical area to practice, or let us surprise you.</p>
        </div>

        <div className="mb-6 text-center">
          <Button variant="secondary" onClick={handleSurpriseMe}>
            Surprise Me (Random Case)
          </Button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {specialties.map((specialty) => (
            <Card
              key={specialty.id}
              hover
              padding="md"
              onClick={() => handleSpecialtySelect(specialty.id)}
            >
              <div className="flex items-start gap-3">
                <span className="text-2xl">{specialty.icon}</span>
                <div>
                  <h3 className="text-base font-semibold text-text-primary">{specialty.name}</h3>
                  <p className="text-xs text-text-secondary mt-1">{specialty.description}</p>
                  <p className="text-xs font-medium text-forest-green mt-2">{specialty.cases} cases</p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  // --- Landing Page ---
  return (
    <div className="overflow-hidden">
      {/* Hero Section */}
      <section className="relative px-6 pt-16 pb-24 max-w-7xl mx-auto">
        <div className="absolute top-20 right-0 w-96 h-96 bg-forest-green/5 rounded-full blur-3xl -z-10" />
        <div className="absolute bottom-0 left-0 w-80 h-80 bg-terracotta/5 rounded-full blur-3xl -z-10" />

        <div className="max-w-3xl mx-auto text-center animate-fade-in-up">
          <div className="inline-flex items-center gap-2 bg-forest-green/10 text-forest-green px-4 py-2 rounded-full text-sm font-medium mb-8">
            <span className="w-2 h-2 bg-forest-green rounded-full animate-scale-pulse" />
            Multi-Agent Hospital Simulation
          </div>

          <h1 className="text-3xl md:text-[3.5rem] font-bold text-text-primary leading-tight mb-6">
            Train Like You&apos;re in a{' '}
            <span className="text-forest-green">Real Indian Hospital</span>
          </h1>

          <p className="text-lg md:text-xl text-text-secondary leading-relaxed mb-10 max-w-2xl mx-auto">
            AI-powered clinical simulation with a patient who speaks Hinglish, a nurse who catches your mistakes,
            and a senior doctor who teaches through questions. Built for Indian medical students.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button size="lg" onClick={handleStartCase}>
              Start a Case
            </Button>
            <Button variant="secondary" size="lg" onClick={() => navigate('/cases')}>
              Browse Cases
            </Button>
          </div>
        </div>

        {/* Stats Bar */}
        <div className="mt-20 grid grid-cols-2 md:grid-cols-4 gap-6 max-w-3xl mx-auto animate-fade-in-up animate-delay-300" style={{ opacity: 0 }}>
          {[
            { label: 'Verified Cases', value: '142' },
            { label: 'Medical Specialties', value: '14' },
            { label: 'AI Hospital Agents', value: '3' },
            { label: 'India-Centric', value: '100%' },
          ].map((stat) => (
            <div key={stat.label} className="text-center">
              <div className="text-2xl font-bold text-forest-green">{stat.value}</div>
              <div className="text-sm text-text-tertiary mt-1">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features Section */}
      <section className="px-6 py-20 bg-warm-gray-50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-14">
            <h2 className="text-2xl md:text-[2.25rem] font-bold text-text-primary mb-4">
              Not Another Quiz App
            </h2>
            <p className="text-lg text-text-secondary max-w-2xl mx-auto">
              A full hospital simulation where time passes, vitals change, and your decisions have consequences.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {features.map((feature) => (
              <Card key={feature.title} hover padding="lg">
                <div className="flex gap-5">
                  <div className="w-12 h-12 bg-forest-green/10 rounded-xl flex items-center justify-center text-forest-green shrink-0">
                    {feature.icon}
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-text-primary mb-2">{feature.title}</h3>
                    <p className="text-base text-text-secondary leading-relaxed">{feature.description}</p>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Specialties Preview */}
      <section className="px-6 py-20">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-14">
            <h2 className="text-2xl md:text-[2.25rem] font-bold text-text-primary mb-4">
              14 Specialties, 142 Verified Cases
            </h2>
            <p className="text-lg text-text-secondary">
              Every case grounded in Indian medical literature and clinical practice
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {specialties.slice(0, 8).map((specialty) => (
              <Card
                key={specialty.id}
                hover
                padding="md"
                onClick={handleStartCase}
              >
                <div className="text-center">
                  <div className="text-3xl mb-2">{specialty.icon}</div>
                  <h3 className="text-sm font-semibold text-text-primary">{specialty.name}</h3>
                  <p className="text-xs text-text-tertiary mt-1">{specialty.cases} cases</p>
                </div>
              </Card>
            ))}
          </div>

          <div className="text-center mt-8">
            <Button variant="secondary" onClick={handleStartCase}>
              View All 14 Specialties
            </Button>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="px-6 py-20 bg-forest-green">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-2xl md:text-[2.25rem] font-bold text-cream-white mb-4">
            Ready to Face Your First Patient?
          </h2>
          <p className="text-lg text-cream-white/80 mb-8">
            Start with a single case. The patient is waiting in the ward. The nurse has done triage.
            Dr. Sharma will be watching your clinical reasoning.
          </p>
          <Button
            size="lg"
            variant="secondary"
            className="!border-cream-white !text-cream-white hover:!bg-cream-white/10"
            onClick={handleStartCase}
          >
            Enter the Ward
          </Button>
        </div>
      </section>
    </div>
  );
};
