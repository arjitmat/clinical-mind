import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui';
import { Card } from '../components/ui';

const specialties = [
  { id: 'cardiology', name: 'Cardiology', icon: '🫀', cases: 30, description: 'Heart failure, ACS, arrhythmias' },
  { id: 'respiratory', name: 'Respiratory', icon: '🫁', cases: 25, description: 'Pneumonia, COPD, TB' },
  { id: 'infectious', name: 'Infectious Disease', icon: '🦠', cases: 28, description: 'Dengue, malaria, typhoid' },
  { id: 'neurology', name: 'Neurology', icon: '🧠', cases: 20, description: 'Stroke, meningitis, seizures' },
  { id: 'gastro', name: 'Gastroenterology', icon: '🔬', cases: 22, description: 'Liver disease, pancreatitis, GI bleeds' },
  { id: 'emergency', name: 'Emergency Medicine', icon: '🚨', cases: 35, description: 'Acute MI, sepsis, trauma' },
];

const features = [
  {
    title: 'Socratic AI Tutor',
    description: 'Multi-turn dialogue that keeps asking "why" until you demonstrate deep understanding. Like having a senior attending in your pocket.',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
    ),
  },
  {
    title: 'Cognitive Bias Detection',
    description: 'Tracks your decision patterns across 20+ cases. Identifies anchoring, premature closure, and availability bias you didn\'t know you had.',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="10"/>
        <path d="M12 16v-4M12 8h.01"/>
      </svg>
    ),
  },
  {
    title: 'Knowledge Graph',
    description: 'Visual map of your medical knowledge. See which concepts you\'ve mastered and where the weak connections are hiding.',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="6" cy="6" r="3"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="18" r="3"/>
        <path d="M9 6h6M6 9v6M18 9v6M9 18h6"/>
      </svg>
    ),
  },
  {
    title: 'India-Centric Cases',
    description: 'Cases built from Indian medical journals. Dengue in monsoon, TB in PHC settings, resource-constrained decision making.',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12 22s-8-4.5-8-11.8A8 8 0 0 1 12 2a8 8 0 0 1 8 8.2c0 7.3-8 11.8-8 11.8z"/>
        <circle cx="12" cy="10" r="3"/>
      </svg>
    ),
  },
];

export const Landing: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="overflow-hidden">
      {/* Hero Section */}
      <section className="relative px-6 pt-16 pb-24 max-w-7xl mx-auto">
        <div className="absolute top-20 right-0 w-96 h-96 bg-forest-green/5 rounded-full blur-3xl -z-10" />
        <div className="absolute bottom-0 left-0 w-80 h-80 bg-terracotta/5 rounded-full blur-3xl -z-10" />

        <div className="max-w-3xl mx-auto text-center animate-fade-in-up">
          <div className="inline-flex items-center gap-2 bg-forest-green/10 text-forest-green px-4 py-2 rounded-full text-sm font-medium mb-8">
            <span className="w-2 h-2 bg-forest-green rounded-full animate-scale-pulse" />
            Powered by Claude Opus 4.6
          </div>

          <h1 className="text-3xl md:text-[3.5rem] font-bold text-text-primary leading-tight mb-6">
            Master Clinical Reasoning,{' '}
            <span className="text-forest-green">One Case at a Time</span>
          </h1>

          <p className="text-lg md:text-xl text-text-secondary leading-relaxed mb-10 max-w-2xl mx-auto">
            An AI-powered clinical reasoning simulator that exposes your cognitive biases, 
            sharpens diagnostic thinking, and trains you like an expert clinician would.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button size="lg" onClick={() => navigate('/cases')}>
              Start Your First Case
            </Button>
            <Button variant="secondary" size="lg" onClick={() => navigate('/dashboard')}>
              View Dashboard
            </Button>
          </div>
        </div>

        {/* Stats Bar */}
        <div className="mt-20 grid grid-cols-2 md:grid-cols-4 gap-6 max-w-3xl mx-auto animate-fade-in-up animate-delay-300" style={{ opacity: 0 }}>
          {[
            { label: 'Clinical Cases', value: '180+' },
            { label: 'Medical Specialties', value: '6' },
            { label: 'Cognitive Biases Tracked', value: '4' },
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
              We focus on <span className="font-semibold text-text-primary">how you think</span>, 
              not just what you diagnose. Six layers of AI-powered clinical training.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {features.map((feature, index) => (
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

      {/* Specialties Section */}
      <section className="px-6 py-20">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-14">
            <h2 className="text-2xl md:text-[2.25rem] font-bold text-text-primary mb-4">
              Choose Your Specialty
            </h2>
            <p className="text-lg text-text-secondary">
              Cases grounded in Indian medical literature and clinical practice
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {specialties.map((specialty) => (
              <Card
                key={specialty.id}
                hover
                padding="lg"
                onClick={() => navigate(`/cases?specialty=${specialty.id}`)}
              >
                <div className="text-4xl mb-4">{specialty.icon}</div>
                <h3 className="text-lg font-semibold text-text-primary mb-1">{specialty.name}</h3>
                <p className="text-sm text-text-secondary mb-3">{specialty.description}</p>
                <div className="text-sm font-medium text-forest-green">{specialty.cases} cases available</div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="px-6 py-20 bg-forest-green">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-2xl md:text-[2.25rem] font-bold text-cream-white mb-4">
            Ready to Think Like an Expert?
          </h2>
          <p className="text-lg text-cream-white/80 mb-8">
            Start with a single case. Our AI will analyze your reasoning, 
            expose hidden biases, and help you develop clinical intuition.
          </p>
          <Button
            size="lg"
            variant="secondary"
            className="!border-cream-white !text-cream-white hover:!bg-cream-white/10"
            onClick={() => navigate('/cases')}
          >
            Begin Your Journey
          </Button>
        </div>
      </section>
    </div>
  );
};
