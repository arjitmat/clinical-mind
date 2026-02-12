/**
 * Landing Page - Feature Showcase
 * Premium, warm design with 4 main features
 */
import React, { useState } from 'react';
import { ProfileModal } from '../components/ProfileModal';

interface FeatureCardProps {
  emoji: string;
  title: string;
  description: string;
  whatYouLearn: string;
  featureId: 'simulation' | 'reasoning-chain' | 'adversarial' | 'bias-interruption';
  onTryNow: (featureId: string) => void;
}

const FeatureCard: React.FC<FeatureCardProps> = ({
  emoji,
  title,
  description,
  whatYouLearn,
  featureId,
  onTryNow,
}) => {
  return (
    <div className="bg-white rounded-2xl p-8 border border-warm-gray-100 hover:shadow-lg hover:-translate-y-1 transition-all duration-300">
      <div className="text-5xl mb-4">{emoji}</div>
      <h3 className="text-xl font-semibold text-text-primary mb-3">{title}</h3>
      <p className="text-base text-text-secondary leading-relaxed mb-4">
        {description}
      </p>
      <div className="bg-warm-gray-50 rounded-xl p-4 mb-6">
        <p className="text-sm text-text-secondary">
          <span className="font-semibold text-forest-green">What you'll learn:</span>
          <br />
          {whatYouLearn}
        </p>
      </div>
      <button
        onClick={() => onTryNow(featureId)}
        className="w-full bg-forest-green hover:bg-forest-green-dark text-cream-white font-semibold py-3 px-6 rounded-xl transition-all duration-300"
      >
        Try Now →
      </button>
    </div>
  );
};

export const NewLanding: React.FC = () => {
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [selectedFeature, setSelectedFeature] = useState<string>('');

  const handleTryNow = (featureId: string) => {
    setSelectedFeature(featureId);
    setShowProfileModal(true);
  };

  const features = [
    {
      emoji: '🩺',
      title: 'AI Patient Simulation',
      description: 'Practice clinical communication with realistic AI patients that respond to your bedside manner.',
      whatYouLearn: 'How your tone and empathy affect patient rapport. See how experts build trust.',
      featureId: 'simulation' as const,
    },
    {
      emoji: '🧠',
      title: 'Clinical Reasoning Chain',
      description: 'Watch Claude Opus spend 10 minutes analyzing your diagnostic approach using extended thinking.',
      whatYouLearn: 'See how experts think step-by-step. Identify gaps in your reasoning process.',
      featureId: 'reasoning-chain' as const,
    },
    {
      emoji: '🎯',
      title: 'Adversarial Cases',
      description: 'Cases designed to exploit your cognitive biases. We predict you\'ll fail, then catch you.',
      whatYouLearn: 'Discover your blind spots. Learn which biases you\'re most susceptible to.',
      featureId: 'adversarial' as const,
    },
    {
      emoji: '🛑',
      title: 'Bias Interruption',
      description: 'Real-time metacognitive training. AI interrupts when it detects anchoring or premature closure.',
      whatYouLearn: 'Build awareness of your thinking patterns. Practice deliberate System 2 thinking.',
      featureId: 'bias-interruption' as const,
    },
  ];

  return (
    <div className="min-h-screen bg-cream-white">
      {/* Hero Section */}
      <section className="px-6 pt-16 pb-12 max-w-6xl mx-auto text-center">
        <div className="inline-flex items-center gap-2 bg-forest-green/10 text-forest-green px-4 py-2 rounded-full text-sm font-medium mb-6">
          <span className="w-2 h-2 bg-forest-green rounded-full animate-scale-pulse" />
          Powered by Claude Opus 4.6
        </div>

        <h1 className="text-4xl md:text-5xl font-bold text-text-primary leading-tight mb-6">
          Train Your Clinical Mind with{' '}
          <span className="text-forest-green">AI-Powered Simulations</span>
        </h1>

        <p className="text-xl text-text-secondary leading-relaxed mb-8 max-w-3xl mx-auto">
          Designed for Indian Medical Students. Master clinical reasoning, communication,
          and metacognitive skills through realistic AI simulations.
        </p>

        <div className="flex items-center justify-center gap-8 text-sm text-text-tertiary mb-12">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-forest-green"></div>
            <span>100+ India-specific cases</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-forest-green"></div>
            <span>Real-time AI feedback</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-forest-green"></div>
            <span>Bias detection</span>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="px-6 pb-20 max-w-6xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {features.map((feature) => (
            <FeatureCard
              key={feature.featureId}
              {...feature}
              onTryNow={handleTryNow}
            />
          ))}
        </div>
      </section>

      {/* Profile Modal */}
      <ProfileModal
        isOpen={showProfileModal}
        onClose={() => setShowProfileModal(false)}
        selectedFeature={selectedFeature}
      />
    </div>
  );
};
