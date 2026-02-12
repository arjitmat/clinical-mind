/**
 * Adversarial Case Page
 * Cases designed to exploit cognitive biases - "We predict you'll fail, then catch you"
 */
import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

interface AdversarialCaseData {
  case_id: string;
  predicted_bias: string;
  bias_explanation: string;
  trap_description: string;

  patient_name: string;
  age: number;
  gender: string;
  chief_complaint: string;
  setting: string;

  obvious_diagnosis: string;
  actual_diagnosis: string;
  critical_differentiator: string;

  learning_objective: string;
  why_challenging: string;
}

type Stage = 'prediction' | 'challenge' | 'reveal';

export const AdversarialCase: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [stage, setStage] = useState<Stage>('prediction');
  const [adversarialCase, setAdversarialCase] = useState<AdversarialCaseData | null>(null);
  const [studentDiagnosis, setStudentDiagnosis] = useState('');

  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const isNew = searchParams.get('new') === 'true';

    if (isNew) {
      // Load demo adversarial case
      loadDemoCase();
    }
  }, [location]);

  const loadDemoCase = () => {
    setLoading(true);
    // Simulate API call
    setTimeout(() => {
      setAdversarialCase({
        case_id: 'adv-001',
        predicted_bias: 'Anchoring Bias',
        bias_explanation:
          'Based on your past cases, you tend to fixate on diagnoses in your comfortable specialties and miss systemic causes.',
        trap_description:
          'This case presents with classic cardiology symptoms, but the actual cause is an endocrine disorder.',

        patient_name: 'Ramesh Kumar',
        age: 45,
        gender: 'Male',
        chief_complaint: 'Palpitations and chest discomfort for 2 weeks',
        setting: 'Urban Medical College OPD',

        obvious_diagnosis: 'Atrial fibrillation',
        actual_diagnosis: 'Thyrotoxicosis presenting with cardiac symptoms',
        critical_differentiator:
          'Asking about weight loss, heat intolerance, hand tremors, and increased appetite',

        learning_objective:
          'Recognize when cardiac symptoms may be secondary to systemic disease',
        why_challenging:
          'Presents with your comfortable specialty but requires broader differential thinking',
      });
      setLoading(false);
    }, 1500);
  };

  const handleProceedToChallenge = () => {
    setStage('challenge');
  };

  const handleSubmitDiagnosis = () => {
    if (studentDiagnosis.trim()) {
      setStage('reveal');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-cream-white flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="text-6xl mb-6 animate-pulse">🎯</div>
          <h2 className="text-2xl font-bold text-text-primary mb-3">
            Analyzing Your Biases...
          </h2>
          <p className="text-text-secondary">
            Creating a case designed to challenge your cognitive patterns
          </p>
        </div>
      </div>
    );
  }

  if (!adversarialCase) {
    return (
      <div className="min-h-screen bg-cream-white flex items-center justify-center p-8">
        <div className="max-w-md text-center">
          <div className="text-6xl mb-6">🎯</div>
          <h1 className="text-3xl font-bold text-text-primary mb-4">
            Adversarial Cases
          </h1>
          <p className="text-text-secondary mb-6">
            Complete some simulations first, then we'll analyze your biases and create cases
            designed to challenge you.
          </p>
          <button
            onClick={() => navigate('/')}
            className="bg-forest-green hover:bg-forest-green-dark text-cream-white font-semibold py-3 px-8 rounded-xl transition-all duration-300"
          >
            Start a Simulation
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-cream-white">
      {/* Header */}
      <div className="bg-white border-b border-warm-gray-200 px-8 py-6">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center gap-3 mb-2">
            <span className="text-3xl">🎯</span>
            <h1 className="text-2xl font-bold text-text-primary">Adversarial Case</h1>
          </div>
          <p className="text-sm text-text-secondary">
            A case designed to challenge your cognitive biases
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto p-8">
        {/* Stage: Prediction */}
        {stage === 'prediction' && (
          <div className="space-y-6">
            <div className="bg-warning/10 border-2 border-warning/30 rounded-2xl p-8">
              <div className="flex items-center gap-3 mb-4">
                <span className="text-4xl">⚠️</span>
                <h2 className="text-2xl font-bold text-text-primary">We Predict You'll Fail</h2>
              </div>

              <div className="space-y-4">
                <div>
                  <h3 className="font-semibold text-text-primary mb-2">
                    Your Detected Bias:
                  </h3>
                  <p className="text-lg font-bold text-warning">{adversarialCase.predicted_bias}</p>
                </div>

                <div>
                  <h3 className="font-semibold text-text-primary mb-2">Why This Matters:</h3>
                  <p className="text-text-secondary">{adversarialCase.bias_explanation}</p>
                </div>

                <div>
                  <h3 className="font-semibold text-text-primary mb-2">The Trap:</h3>
                  <p className="text-text-secondary">{adversarialCase.trap_description}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl border border-warm-gray-200 p-8">
              <h3 className="text-xl font-bold text-text-primary mb-4">
                Are You Ready for the Challenge?
              </h3>
              <p className="text-text-secondary mb-6">
                This case is specifically designed to exploit your {adversarialCase.predicted_bias.toLowerCase()}. Can you recognize the trap and avoid it?
              </p>
              <button
                onClick={handleProceedToChallenge}
                className="w-full bg-forest-green hover:bg-forest-green-dark text-cream-white font-semibold py-4 px-8 rounded-xl transition-all duration-300"
              >
                Bring It On →
              </button>
            </div>
          </div>
        )}

        {/* Stage: Challenge */}
        {stage === 'challenge' && (
          <div className="space-y-6">
            <div className="bg-white rounded-2xl border border-warm-gray-200 p-8">
              <h2 className="text-2xl font-bold text-text-primary mb-6">The Case</h2>

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-text-tertiary">Patient</p>
                    <p className="font-semibold text-text-primary">
                      {adversarialCase.patient_name}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-text-tertiary">Age / Gender</p>
                    <p className="font-semibold text-text-primary">
                      {adversarialCase.age}yo {adversarialCase.gender}
                    </p>
                  </div>
                  <div className="col-span-2">
                    <p className="text-sm text-text-tertiary">Setting</p>
                    <p className="font-semibold text-text-primary">{adversarialCase.setting}</p>
                  </div>
                </div>

                <div className="bg-warm-gray-50 rounded-xl p-6">
                  <p className="text-sm text-text-tertiary mb-2">Chief Complaint</p>
                  <p className="text-lg font-semibold text-text-primary">
                    {adversarialCase.chief_complaint}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl border border-warm-gray-200 p-8">
              <h3 className="text-xl font-bold text-text-primary mb-4">Your Diagnosis</h3>
              <p className="text-sm text-text-secondary mb-4">
                What is your primary diagnosis? Remember: we predicted you would fall into a
                specific bias trap.
              </p>
              <textarea
                value={studentDiagnosis}
                onChange={(e) => setStudentDiagnosis(e.target.value)}
                placeholder="Enter your diagnosis..."
                className="w-full px-4 py-3 bg-warm-gray-50 border border-warm-gray-200 rounded-xl text-text-primary placeholder-text-tertiary focus:outline-none focus:ring-2 focus:ring-forest-green focus:border-transparent transition-all duration-300 resize-none"
                rows={4}
              />
              <button
                onClick={handleSubmitDiagnosis}
                disabled={!studentDiagnosis.trim()}
                className="w-full mt-4 bg-forest-green hover:bg-forest-green-dark text-cream-white font-semibold py-4 px-8 rounded-xl transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Submit Diagnosis
              </button>
            </div>
          </div>
        )}

        {/* Stage: Reveal */}
        {stage === 'reveal' && (
          <div className="space-y-6">
            {/* Did we catch you? */}
            <div
              className={`rounded-2xl p-8 border-2 ${
                studentDiagnosis.toLowerCase().includes(adversarialCase.obvious_diagnosis.toLowerCase())
                  ? 'bg-error/10 border-error/30'
                  : 'bg-forest-green/10 border-forest-green/30'
              }`}
            >
              <div className="flex items-center gap-3 mb-4">
                <span className="text-5xl">
                  {studentDiagnosis.toLowerCase().includes(adversarialCase.obvious_diagnosis.toLowerCase()) ? '😔' : '🎉'}
                </span>
                <h2 className="text-2xl font-bold text-text-primary">
                  {studentDiagnosis.toLowerCase().includes(adversarialCase.obvious_diagnosis.toLowerCase())
                    ? 'We Caught You!'
                    : 'You Escaped the Trap!'}
                </h2>
              </div>

              <p className="text-text-secondary text-lg">
                {studentDiagnosis.toLowerCase().includes(adversarialCase.obvious_diagnosis.toLowerCase())
                  ? `You fell into the ${adversarialCase.predicted_bias.toLowerCase()} trap by diagnosing "${adversarialCase.obvious_diagnosis}".`
                  : `You successfully avoided the trap! You didn't anchor on "${adversarialCase.obvious_diagnosis}".`}
              </p>
            </div>

            {/* The Reveal */}
            <div className="bg-white rounded-2xl border border-warm-gray-200 p-8">
              <h3 className="text-xl font-bold text-text-primary mb-6">The Reveal</h3>

              <div className="space-y-6">
                <div>
                  <h4 className="font-semibold text-error mb-2">The Trap:</h4>
                  <p className="text-text-secondary">
                    Obvious diagnosis: <span className="font-semibold">{adversarialCase.obvious_diagnosis}</span>
                  </p>
                </div>

                <div>
                  <h4 className="font-semibold text-forest-green mb-2">The Actual Diagnosis:</h4>
                  <p className="text-lg font-bold text-text-primary">
                    {adversarialCase.actual_diagnosis}
                  </p>
                </div>

                <div>
                  <h4 className="font-semibold text-text-primary mb-2">The Critical Differentiator:</h4>
                  <p className="text-text-secondary">{adversarialCase.critical_differentiator}</p>
                </div>
              </div>
            </div>

            {/* Learning Points */}
            <div className="bg-soft-blue/10 rounded-2xl border-2 border-soft-blue/30 p-8">
              <h3 className="text-xl font-bold text-text-primary mb-4 flex items-center gap-2">
                <span>💡</span> Learning Points
              </h3>

              <div className="space-y-4">
                <div>
                  <h4 className="font-semibold text-text-primary mb-2">Learning Objective:</h4>
                  <p className="text-text-secondary">{adversarialCase.learning_objective}</p>
                </div>

                <div>
                  <h4 className="font-semibold text-text-primary mb-2">Why This Was Challenging:</h4>
                  <p className="text-text-secondary">{adversarialCase.why_challenging}</p>
                </div>

                <div className="bg-white rounded-lg p-4">
                  <h4 className="font-semibold text-forest-green mb-2">How to Avoid This Bias:</h4>
                  <ul className="space-y-2 text-sm text-text-secondary">
                    <li className="flex items-start gap-2">
                      <span className="text-forest-green mt-1">•</span>
                      <span>Always generate a broad differential before anchoring on one diagnosis</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-forest-green mt-1">•</span>
                      <span>Ask yourself: "What systemic causes could explain these symptoms?"</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-forest-green mt-1">•</span>
                      <span>Look for clues that don't fit your initial impression</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-4">
              <button
                onClick={() => navigate('/')}
                className="flex-1 bg-forest-green hover:bg-forest-green-dark text-cream-white font-semibold py-3 px-6 rounded-xl transition-all duration-300"
              >
                Try Another Case
              </button>
              <button
                onClick={() => {
                  setStage('prediction');
                  setStudentDiagnosis('');
                  loadDemoCase();
                }}
                className="flex-1 bg-warm-gray-100 hover:bg-warm-gray-200 text-text-primary font-semibold py-3 px-6 rounded-xl transition-all duration-300"
              >
                New Adversarial Case
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
