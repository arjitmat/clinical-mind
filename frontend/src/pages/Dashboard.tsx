import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, Badge, StatCard } from '../components/ui';
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip, AreaChart, Area
} from 'recharts';

// Recharts v3 type workaround
const RChart = RadarChart as any;
const RGrid = PolarGrid as any;
const RAngleAxis = PolarAngleAxis as any;
const RRadiusAxis = PolarRadiusAxis as any;
const RRadar = Radar as any;
const RContainer = ResponsiveContainer as any;
const AChart = AreaChart as any;
const RXAxis = XAxis as any;
const RYAxis = YAxis as any;
const RCartesianGrid = CartesianGrid as any;
const RTooltip = Tooltip as any;
const RArea = Area as any;

// Sample data
const biasData = [
  { bias: 'Anchoring', score: 65 },
  { bias: 'Premature Closure', score: 40 },
  { bias: 'Availability', score: 55 },
  { bias: 'Confirmation', score: 30 },
];

const performanceHistory = [
  { week: 'W1', accuracy: 55, avgTime: 18 },
  { week: 'W2', accuracy: 60, avgTime: 16 },
  { week: 'W3', accuracy: 58, avgTime: 15 },
  { week: 'W4', accuracy: 68, avgTime: 14 },
  { week: 'W5', accuracy: 72, avgTime: 12 },
  { week: 'W6', accuracy: 75, avgTime: 11 },
  { week: 'W7', accuracy: 78, avgTime: 10 },
];

const specialtyScores = [
  { name: 'Cardiology', score: 82, cases: 12 },
  { name: 'Respiratory', score: 65, cases: 8 },
  { name: 'Infectious', score: 78, cases: 10 },
  { name: 'Neurology', score: 45, cases: 5 },
  { name: 'Gastro', score: 70, cases: 7 },
  { name: 'Emergency', score: 55, cases: 6 },
];

const biasInsights = [
  {
    type: 'Anchoring Bias',
    severity: 'moderate' as const,
    evidence: 'You stuck with your initial diagnosis in 7 out of 10 recent cases, even when new information contradicted it.',
    recommendation: 'Practice cases with atypical presentations. Force yourself to reconsider after each new piece of information.',
  },
  {
    type: 'Availability Bias',
    severity: 'low' as const,
    evidence: 'After studying cardiology, you diagnosed 3 consecutive non-cardiac cases as cardiac. Your recent study focus influenced your diagnoses.',
    recommendation: 'Before diagnosing, list 3 differential diagnoses from different organ systems.',
  },
];

const recommendations = [
  {
    type: 'Weak Area',
    specialty: 'Neurology',
    difficulty: 'beginner',
    reason: 'Your neurology accuracy is only 45%. Let\'s strengthen this foundation.',
    priority: 'high' as const,
  },
  {
    type: 'Bias Counter',
    specialty: 'Mixed',
    difficulty: 'intermediate',
    reason: 'Atypical presentation cases to reduce your anchoring bias pattern.',
    priority: 'medium' as const,
  },
  {
    type: 'Challenge',
    specialty: 'Cardiology',
    difficulty: 'advanced',
    reason: 'Your cardiology accuracy is 82%. Ready for advanced cases!',
    priority: 'low' as const,
  },
];

const priorityColors: Record<string, 'error' | 'warning' | 'info'> = {
  high: 'error',
  medium: 'warning',
  low: 'info',
};

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-forest-green to-sage-green rounded-2xl p-8 text-cream-white">
        <h1 className="text-2xl md:text-3xl font-bold mb-2">Welcome back, Student</h1>
        <p className="text-lg opacity-90 mb-4">
          You've completed 48 cases across 6 specialties. Your diagnostic accuracy has improved 23% this month.
        </p>
        <Button
          variant="secondary"
          className="!border-cream-white !text-cream-white hover:!bg-cream-white/10"
          onClick={() => navigate('/cases')}
        >
          Continue Learning
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatCard title="Overall Accuracy" value="75%" trend="+5% from last week" color="green" />
        <StatCard title="Cases Completed" value="48" trend="8 this week" color="blue" />
        <StatCard title="Avg. Time per Case" value="10 min" trend="-2 min improvement" color="green" />
        <StatCard title="Peer Ranking" value="Top 15%" trend="Moved up 3%" color="terracotta" />
      </div>

      {/* Performance Chart + Bias Radar */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Accuracy Over Time */}
        <Card padding="lg">
          <h2 className="text-xl font-semibold text-text-primary mb-6">Performance Trend</h2>
          <RContainer width="100%" height={280}>
            <AChart data={performanceHistory}>
              <defs>
                <linearGradient id="colorAccuracy" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#2D5C3F" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#2D5C3F" stopOpacity={0} />
                </linearGradient>
              </defs>
              <RCartesianGrid strokeDasharray="3 3" stroke="#E8E5E0" />
              <RXAxis dataKey="week" stroke="#8A8179" fontSize={13} />
              <RYAxis stroke="#8A8179" fontSize={13} domain={[0, 100]} />
              <RTooltip
                contentStyle={{
                  background: '#FFFCF7',
                  border: '1.5px solid #E8E5E0',
                  borderRadius: '12px',
                  fontSize: '14px',
                }}
              />
              <RArea
                type="monotone"
                dataKey="accuracy"
                stroke="#2D5C3F"
                strokeWidth={2.5}
                fill="url(#colorAccuracy)"
              />
            </AChart>
          </RContainer>
        </Card>

        {/* Cognitive Bias Radar */}
        <Card padding="lg">
          <h2 className="text-xl font-semibold text-text-primary mb-6">Cognitive Bias Profile</h2>
          <RContainer width="100%" height={280}>
            <RChart data={biasData}>
              <RGrid stroke="#E8E5E0" />
              <RAngleAxis dataKey="bias" stroke="#5A5147" fontSize={13} />
              <RRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
              <RRadar
                dataKey="score"
                stroke="#2D5C3F"
                fill="#2D5C3F"
                fillOpacity={0.2}
                strokeWidth={2}
              />
            </RChart>
          </RContainer>
          <p className="text-sm text-text-tertiary text-center mt-2">
            Lower scores are better. Score reflects bias frequency in recent cases.
          </p>
        </Card>
      </div>

      {/* Bias Insights */}
      <Card padding="lg">
        <h2 className="text-xl font-semibold text-text-primary mb-6">Bias Insights</h2>
        <div className="space-y-4">
          {biasInsights.map((insight) => (
            <div key={insight.type} className="bg-warm-gray-50 rounded-xl p-5">
              <div className="flex items-center gap-3 mb-2">
                <Badge variant={insight.severity === 'moderate' ? 'warning' : 'info'}>
                  {insight.severity.charAt(0).toUpperCase() + insight.severity.slice(1)}
                </Badge>
                <h3 className="font-semibold text-text-primary">{insight.type}</h3>
              </div>
              <p className="text-base text-text-secondary mb-2">{insight.evidence}</p>
              <p className="text-sm text-forest-green font-medium">
                Recommendation: {insight.recommendation}
              </p>
            </div>
          ))}
        </div>
      </Card>

      {/* Specialty Breakdown */}
      <Card padding="lg">
        <h2 className="text-xl font-semibold text-text-primary mb-6">Specialty Performance</h2>
        <div className="space-y-4">
          {specialtyScores.map((s) => (
            <div key={s.name} className="flex items-center gap-4">
              <span className="text-sm font-medium text-text-secondary w-28 shrink-0">{s.name}</span>
              <div className="flex-1 bg-warm-gray-100 rounded-full h-3 overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{
                    width: `${s.score}%`,
                    backgroundColor: s.score >= 70 ? '#2D5C3F' : s.score >= 50 ? '#D4803F' : '#C85835',
                  }}
                />
              </div>
              <span className="text-sm font-semibold text-text-primary w-12 text-right">{s.score}%</span>
              <span className="text-xs text-text-tertiary w-16 text-right">{s.cases} cases</span>
            </div>
          ))}
        </div>
      </Card>

      {/* Recommended Cases */}
      <div>
        <h2 className="text-xl font-semibold text-text-primary mb-6">Recommended For You</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {recommendations.map((rec, i) => (
            <Card key={i} hover padding="lg">
              <Badge variant={priorityColors[rec.priority]} size="sm">
                {rec.priority.toUpperCase()} PRIORITY
              </Badge>
              <h3 className="text-lg font-semibold text-text-primary mt-3 mb-1">{rec.type}</h3>
              <p className="text-sm text-text-secondary mb-2">
                {rec.specialty} - {rec.difficulty}
              </p>
              <p className="text-base text-text-secondary mb-4">{rec.reason}</p>
              <Button size="sm" onClick={() => navigate('/cases')}>
                Start Case
              </Button>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
};
