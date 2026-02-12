/**
 * Bias Interrupt Modal
 * Real-time intervention when cognitive bias is detected during simulation
 */
import React, { useState } from 'react';

interface BiasInterruptModalProps {
  isOpen: boolean;
  biasType: string;
  interventionMessage: string;
  reflectionQuestions: string[];
  onContinue: (reflections: string[]) => void;
}

export const BiasInterruptModal: React.FC<BiasInterruptModalProps> = ({
  isOpen,
  biasType,
  interventionMessage,
  reflectionQuestions,
  onContinue,
}) => {
  const [reflections, setReflections] = useState<string[]>(
    reflectionQuestions.map(() => '')
  );

  if (!isOpen) return null;

  const handleReflectionChange = (index: number, value: string) => {
    const updated = [...reflections];
    updated[index] = value;
    setReflections(updated);
  };

  const handleContinue = () => {
    // Check if all reflections have been answered
    const allAnswered = reflections.every((r) => r.trim().length > 0);
    if (allAnswered) {
      onContinue(reflections);
      // Reset for next time
      setReflections(reflectionQuestions.map(() => ''));
    }
  };

  const allAnswered = reflections.every((r) => r.trim().length > 0);

  // Bias type emoji mapping
  const biasEmoji: Record<string, string> = {
    anchoring: '⚓',
    premature_closure: '🚪',
    confirmation_bias: '✅',
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="max-w-2xl w-full mx-4 bg-white rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="bg-warning/10 border-b-2 border-warning/30 px-8 py-6">
          <div className="flex items-center gap-3 mb-2">
            <span className="text-4xl">{biasEmoji[biasType] || '🧠'}</span>
            <h2 className="text-2xl font-bold text-text-primary">
              Hold On — Cognitive Bias Detected
            </h2>
          </div>
          <p className="text-sm text-text-secondary">
            We've noticed a potential {biasType.replace('_', ' ')} in your reasoning. Let's
            pause and reflect.
          </p>
        </div>

        {/* Intervention Message */}
        <div className="px-8 py-6 border-b border-warm-gray-200">
          <div className="bg-warning/5 rounded-xl p-6 border border-warning/20">
            <h3 className="font-semibold text-text-primary mb-2 flex items-center gap-2">
              <span>💡</span> Our Observation:
            </h3>
            <p className="text-text-secondary">{interventionMessage}</p>
          </div>
        </div>

        {/* Reflection Questions */}
        <div className="px-8 py-6">
          <h3 className="font-semibold text-text-primary mb-4">
            Reflection Questions (Answer all to continue):
          </h3>
          <div className="space-y-4">
            {reflectionQuestions.map((question, index) => (
              <div key={index}>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  {index + 1}. {question}
                </label>
                <textarea
                  value={reflections[index]}
                  onChange={(e) => handleReflectionChange(index, e.target.value)}
                  placeholder="Type your reflection..."
                  className="w-full px-4 py-3 bg-warm-gray-50 border border-warm-gray-200 rounded-xl text-text-primary placeholder-text-tertiary focus:outline-none focus:ring-2 focus:ring-forest-green focus:border-transparent transition-all duration-300 resize-none"
                  rows={3}
                />
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="px-8 py-6 bg-warm-gray-50 border-t border-warm-gray-200">
          <button
            onClick={handleContinue}
            disabled={!allAnswered}
            className="w-full bg-forest-green hover:bg-forest-green-dark text-cream-white font-semibold py-4 px-8 rounded-xl transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-forest-green"
          >
            {allAnswered ? 'Continue Interview →' : 'Please answer all questions above'}
          </button>
          <p className="text-xs text-text-tertiary text-center mt-3">
            This intervention is designed to improve your metacognitive awareness
          </p>
        </div>
      </div>
    </div>
  );
};
