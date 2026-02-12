/**
 * Reasoning Chain Analysis Page
 * Deep analysis of student diagnostic reasoning using Claude Opus extended thinking
 */
import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import type { StudentProfile } from '../components/ProfileModal';

interface ReasoningStep {
  step_number: number;
  timestamp: string;
  category: string;
  description: string;
  quality: string;
  expert_insight: string;
}

interface DivergencePoint {
  student_action: string;
  expert_action: string;
  impact: string;
  learning_point: string;
}

interface ReasoningAnalysis {
  analysis_id: string;
  student_reasoning_steps: ReasoningStep[];
  expert_reasoning_steps: ReasoningStep[];
  divergence_points: DivergencePoint[];
  overall_assessment: string;
  strengths: string[];
  gaps: string[];
  learning_recommendations: string[];
  thinking_time_seconds: number;
}

const qualityColors: Record<string, string> = {
  excellent: 'bg-forest-green/10 border-forest-green text-forest-green',
  good: 'bg-sage-green/10 border-sage-green text-sage-green',
  acceptable: 'bg-soft-blue/10 border-soft-blue text-soft-blue',
  concerning: 'bg-warning/10 border-warning text-warning',
  critical_gap: 'bg-error/10 border-error text-error',
};

const categoryIcons: Record<string, string> = {
  data_gathering: '📋',
  hypothesis_generation: '💡',
  hypothesis_testing: '🔬',
  testing: '🧪',
  diagnosis: '🎯',
};

const ReasoningStepCard: React.FC<{ step: ReasoningStep; type: 'student' | 'expert' }> = ({
  step,
  type,
}) => {
  return (
    <div
      className={`p-4 rounded-xl border-2 ${
        qualityColors[step.quality] || 'bg-warm-gray-50 border-warm-gray-200'
      }`}
    >
      <div className="flex items-start gap-3 mb-2">
        <span className="text-2xl">{categoryIcons[step.category] || '📌'}</span>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold text-text-tertiary">
              {step.timestamp}
            </span>
            <span className="text-xs px-2 py-0.5 bg-white rounded-full border border-warm-gray-200 text-text-secondary">
              {step.category.replace(/_/g, ' ')}
            </span>
          </div>
          <p className="text-sm font-medium text-text-primary mb-2">{step.description}</p>
          {type === 'student' && (
            <p className="text-xs text-text-secondary italic">{step.expert_insight}</p>
          )}
        </div>
      </div>
    </div>
  );
};

const DivergenceCard: React.FC<{ divergence: DivergencePoint }> = ({ divergence }) => {
  return (
    <div className="bg-warning/5 border-2 border-warning/20 rounded-xl p-6">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-2xl">⚠️</span>
        <h4 className="font-semibold text-text-primary">Divergence Point</h4>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-xs font-semibold text-error mb-1">What You Did:</p>
          <p className="text-sm text-text-secondary">{divergence.student_action}</p>
        </div>
        <div>
          <p className="text-xs font-semibold text-forest-green mb-1">What Expert Would Do:</p>
          <p className="text-sm text-text-secondary">{divergence.expert_action}</p>
        </div>
      </div>

      <div className="bg-white rounded-lg p-3">
        <p className="text-xs font-semibold text-text-primary mb-1">Impact:</p>
        <p className="text-sm text-text-secondary mb-2">{divergence.impact}</p>
        <p className="text-xs font-semibold text-forest-green mb-1">💡 Learning Point:</p>
        <p className="text-sm text-text-primary font-medium">{divergence.learning_point}</p>
      </div>
    </div>
  );
};

export const ReasoningChain: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<ReasoningAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Check for profile and trigger case selection
    const searchParams = new URLSearchParams(location.search);
    const isNew = searchParams.get('new') === 'true';

    if (isNew) {
      // For now, show demo analysis
      // In production, this would start a simulation and then analyze it
      loadDemoAnalysis();
    }
  }, [location]);

  const loadDemoAnalysis = () => {
    setLoading(true);
    // Simulate extended thinking time
    setTimeout(() => {
      setAnalysis({
        analysis_id: 'demo-001',
        thinking_time_seconds: 45.3,
        student_reasoning_steps: [
          {
            step_number: 1,
            timestamp: '0:30',
            category: 'data_gathering',
            description: 'Asked about chest pain characteristics and duration',
            quality: 'excellent',
            expert_insight:
              'Excellent first question - characterizing chest pain is critical for cardiac differential diagnosis',
          },
          {
            step_number: 2,
            timestamp: '1:15',
            category: 'data_gathering',
            description: 'Asked about associated symptoms (sweating, nausea)',
            quality: 'good',
            expert_insight:
              'Good follow-up - these are important cardiac symptoms',
          },
          {
            step_number: 3,
            timestamp: '2:00',
            category: 'hypothesis_generation',
            description: 'Considered anxiety as primary diagnosis',
            quality: 'concerning',
            expert_insight:
              'Concerning - anchored too early on benign diagnosis without ruling out life-threatening causes',
          },
          {
            step_number: 4,
            timestamp: '4:30',
            category: 'data_gathering',
            description: 'Asked about substance use (cocaine)',
            quality: 'good',
            expert_insight:
              'Important question, but should have been asked earlier given young patient with chest pain',
          },
        ],
        expert_reasoning_steps: [
          {
            step_number: 1,
            timestamp: '0:00',
            category: 'hypothesis_generation',
            description:
              'Generate broad differential: ACS, PE, aortic dissection, cocaine-induced, anxiety',
            quality: 'excellent',
            expert_insight:
              'Expert immediately considers life-threatening causes before benign diagnoses',
          },
          {
            step_number: 2,
            timestamp: '0:30',
            category: 'data_gathering',
            description: 'Characterize chest pain (OPQRST) and cardiac risk factors',
            quality: 'excellent',
            expert_insight:
              'Systematic approach to chest pain evaluation',
          },
          {
            step_number: 3,
            timestamp: '1:00',
            category: 'data_gathering',
            description: 'Screen for substance use immediately (given young age)',
            quality: 'excellent',
            expert_insight:
              'Early screening for cocaine use in young chest pain patient is critical',
          },
          {
            step_number: 4,
            timestamp: '2:00',
            category: 'hypothesis_testing',
            description: 'Order ECG and troponin to rule out ACS',
            quality: 'excellent',
            expert_insight:
              'Appropriate testing to differentiate life-threatening vs benign causes',
          },
        ],
        divergence_points: [
          {
            student_action: 'Anchored on anxiety diagnosis early in interview',
            expert_action: 'Considered multiple life-threatening causes before benign diagnoses',
            impact: 'Risk of missing serious diagnosis',
            learning_point:
              'Always rule out life-threatening causes first (ACS, PE, dissection) before diagnosing anxiety',
          },
          {
            student_action: 'Did not ask about substance use until 4:30 into interview',
            expert_action: 'Asked about substance use within first minute',
            impact: 'Delayed critical diagnostic information',
            learning_point:
              'Substance use (especially cocaine) should be screened early in young patients with chest pain',
          },
        ],
        overall_assessment:
          'The student demonstrated good basic history-taking skills and eventually asked the right questions. However, there was significant anchoring bias toward a benign diagnosis (anxiety) early in the interview, which could have led to missing a serious condition. The student also delayed asking about substance use, which is critical in young chest pain patients. With more practice on systematic differential diagnosis generation and avoiding premature closure, the student can significantly improve their diagnostic accuracy.',
        strengths: [
          'Good rapport with patient',
          'Asked about associated symptoms',
          'Eventually covered important risk factors',
        ],
        gaps: [
          'Anchoring bias - fixated on anxiety diagnosis too early',
          'Did not generate broad differential diagnosis initially',
          'Delayed substance use screening',
          'No mention of ECG or troponin testing',
        ],
        learning_recommendations: [
          'Review systematic approach to chest pain (always consider life-threatening causes first)',
          'Practice generating broad differential diagnoses before narrowing',
          'Study substance-induced acute coronary syndrome',
          'Learn to recognize and interrupt anchoring bias',
        ],
      });
      setLoading(false);
    }, 2000);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-cream-white flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="text-6xl mb-6 animate-pulse">🧠</div>
          <h2 className="text-2xl font-bold text-text-primary mb-3">
            Analyzing Your Reasoning...
          </h2>
          <p className="text-text-secondary mb-6">
            Claude Opus is spending deep thinking time analyzing your diagnostic approach.
            This may take up to 10 minutes for thorough analysis.
          </p>
          <div className="flex items-center justify-center gap-2">
            <div className="w-2 h-2 bg-forest-green rounded-full animate-bounce"></div>
            <div
              className="w-2 h-2 bg-forest-green rounded-full animate-bounce"
              style={{ animationDelay: '0.2s' }}
            ></div>
            <div
              className="w-2 h-2 bg-forest-green rounded-full animate-bounce"
              style={{ animationDelay: '0.4s' }}
            ></div>
          </div>
        </div>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="min-h-screen bg-cream-white flex items-center justify-center p-8">
        <div className="max-w-md text-center">
          <div className="text-6xl mb-6">🧠</div>
          <h1 className="text-3xl font-bold text-text-primary mb-4">
            Clinical Reasoning Chain
          </h1>
          <p className="text-text-secondary mb-6">
            Complete a patient simulation first, then come here to see Claude Opus analyze
            your diagnostic reasoning process.
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
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center gap-3 mb-2">
            <span className="text-3xl">🧠</span>
            <h1 className="text-2xl font-bold text-text-primary">
              Reasoning Chain Analysis
            </h1>
          </div>
          <p className="text-sm text-text-secondary">
            Extended thinking analysis completed in {analysis.thinking_time_seconds.toFixed(1)}s
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto p-8">
        {/* Overall Assessment */}
        <div className="bg-white rounded-2xl border border-warm-gray-200 p-8 mb-8">
          <h2 className="text-xl font-bold text-text-primary mb-4">Overall Assessment</h2>
          <p className="text-base text-text-secondary leading-relaxed">
            {analysis.overall_assessment}
          </p>
        </div>

        {/* Strengths and Gaps */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-forest-green/5 border-2 border-forest-green/20 rounded-2xl p-6">
            <h3 className="text-lg font-bold text-forest-green mb-4 flex items-center gap-2">
              <span>✅</span> Strengths
            </h3>
            <ul className="space-y-2">
              {analysis.strengths.map((strength, idx) => (
                <li key={idx} className="text-sm text-text-primary flex items-start gap-2">
                  <span className="text-forest-green mt-1">•</span>
                  <span>{strength}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="bg-error/5 border-2 border-error/20 rounded-2xl p-6">
            <h3 className="text-lg font-bold text-error mb-4 flex items-center gap-2">
              <span>⚠️</span> Gaps to Address
            </h3>
            <ul className="space-y-2">
              {analysis.gaps.map((gap, idx) => (
                <li key={idx} className="text-sm text-text-primary flex items-start gap-2">
                  <span className="text-error mt-1">•</span>
                  <span>{gap}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Divergence Points */}
        {analysis.divergence_points.length > 0 && (
          <div className="mb-8">
            <h2 className="text-xl font-bold text-text-primary mb-4">
              Critical Divergence Points
            </h2>
            <div className="space-y-4">
              {analysis.divergence_points.map((divergence, idx) => (
                <DivergenceCard key={idx} divergence={divergence} />
              ))}
            </div>
          </div>
        )}

        {/* Side-by-Side Reasoning Steps */}
        <div className="mb-8">
          <h2 className="text-xl font-bold text-text-primary mb-4">
            Reasoning Process Comparison
          </h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Student Timeline */}
            <div>
              <h3 className="text-lg font-semibold text-text-primary mb-4 flex items-center gap-2">
                <span className="w-3 h-3 bg-soft-blue rounded-full"></span>
                Your Reasoning
              </h3>
              <div className="space-y-3">
                {analysis.student_reasoning_steps.map((step) => (
                  <ReasoningStepCard key={step.step_number} step={step} type="student" />
                ))}
              </div>
            </div>

            {/* Expert Timeline */}
            <div>
              <h3 className="text-lg font-semibold text-text-primary mb-4 flex items-center gap-2">
                <span className="w-3 h-3 bg-forest-green rounded-full"></span>
                Expert Reasoning
              </h3>
              <div className="space-y-3">
                {analysis.expert_reasoning_steps.map((step) => (
                  <ReasoningStepCard key={step.step_number} step={step} type="expert" />
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Learning Recommendations */}
        <div className="bg-soft-blue/5 border-2 border-soft-blue/20 rounded-2xl p-8">
          <h2 className="text-xl font-bold text-text-primary mb-4 flex items-center gap-2">
            <span>📚</span> Learning Recommendations
          </h2>
          <ul className="space-y-3">
            {analysis.learning_recommendations.map((rec, idx) => (
              <li
                key={idx}
                className="text-base text-text-primary flex items-start gap-3 p-3 bg-white rounded-lg"
              >
                <span className="text-soft-blue font-bold">{idx + 1}.</span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Actions */}
        <div className="mt-8 flex gap-4">
          <button
            onClick={() => navigate('/')}
            className="flex-1 bg-forest-green hover:bg-forest-green-dark text-cream-white font-semibold py-3 px-6 rounded-xl transition-all duration-300"
          >
            Try Another Case
          </button>
          <button
            onClick={() => window.print()}
            className="flex-1 bg-warm-gray-100 hover:bg-warm-gray-200 text-text-primary font-semibold py-3 px-6 rounded-xl transition-all duration-300"
          >
            Print Analysis
          </button>
        </div>
      </div>
    </div>
  );
};
