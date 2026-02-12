import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, Badge, StatCard } from '../components/ui';
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip, AreaChart, Area
} from 'recharts';
import {
  fetchPerformance, fetchProfile, fetchBiases, fetchRecommendations,
  type PerformanceData, type StudentProfile, type BiasReport, type RecommendationItem
} from '../hooks/useApi';

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

const priorityColors: Record<string, 'error' | 'warning' | 'info'> = {
  high: 'error',
  medium: 'warning',
  low: 'info',
};

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [performance, setPerformance] = useState<PerformanceData | null>(null);
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [biases, setBiases] = useState<BiasReport | null>(null);
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>([]);

  useEffect(() => {
    fetchPerformance().then(setPerformance).catch(() => {});
    fetchProfile().then(setProfile).catch(() => {});
    fetchBiases().then(setBiases).catch(() => {});
    fetchRecommendations().then(setRecommendations).catch(() => {});
  }, []);

  const biasData = biases?.biases_detected.map((b) => ({
    bias: b.type.charAt(0).toUpperCase() + b.type.slice(1).replace('_', ' '),
    score: b.score,
  })) || [];

  const specialtyScores = profile
    ? Object.entries(profile.specialty_scores).map(([name, score]) => ({
        name: name.charAt(0).toUpperCase() + name.slice(1),
        score,
        cases: Math.round(profile.cases_completed * (score / 400)),
      }))
    : [];

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-forest-green to-sage-green rounded-2xl p-8 text-cream-white">
        <h1 className="text-2xl md:text-3xl font-bold mb-2">
          Welcome back{profile ? `, ${profile.name}` : ''}
        </h1>
        <p className="text-lg opacity-90 mb-4">
          {performance
            ? `You've completed ${performance.cases_completed} cases. Your diagnostic accuracy is ${performance.overall_accuracy}%.`
            : 'Loading your progress...'}
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
        <StatCard
          title="Overall Accuracy"
          value={performance ? `${performance.overall_accuracy}%` : '--'}
          trend={performance ? '+5% from last week' : ''}
          color="green"
        />
        <StatCard
          title="Cases Completed"
          value={performance ? `${performance.cases_completed}` : '--'}
          trend={performance ? '8 this week' : ''}
          color="blue"
        />
        <StatCard
          title="Avg. Time per Case"
          value={performance ? `${performance.avg_time_minutes} min` : '--'}
          trend={performance ? '-2 min improvement' : ''}
          color="green"
        />
        <StatCard
          title="Peer Ranking"
          value={performance ? `Top ${performance.peer_percentile}%` : '--'}
          trend={performance ? 'Moved up 3%' : ''}
          color="terracotta"
        />
      </div>

      {/* Performance Chart + Bias Radar */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Accuracy Over Time */}
        <Card padding="lg">
          <h2 className="text-xl font-semibold text-text-primary mb-6">Performance Trend</h2>
          {performance?.history ? (
            <RContainer width="100%" height={280}>
              <AChart data={performance.history}>
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
          ) : (
            <div className="h-[280px] flex items-center justify-center text-text-tertiary">Loading...</div>
          )}
        </Card>

        {/* Cognitive Bias Radar */}
        <Card padding="lg">
          <h2 className="text-xl font-semibold text-text-primary mb-6">Cognitive Bias Profile</h2>
          {biasData.length > 0 ? (
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
          ) : (
            <div className="h-[280px] flex items-center justify-center text-text-tertiary">Loading...</div>
          )}
          <p className="text-sm text-text-tertiary text-center mt-2">
            Lower scores are better. Score reflects bias frequency in recent cases.
          </p>
        </Card>
      </div>

      {/* Bias Insights */}
      {biases && biases.biases_detected.length > 0 && (
        <Card padding="lg">
          <h2 className="text-xl font-semibold text-text-primary mb-6">Bias Insights</h2>
          <div className="space-y-4">
            {biases.biases_detected.map((insight) => (
              <div key={insight.type} className="bg-warm-gray-50 rounded-xl p-5">
                <div className="flex items-center gap-3 mb-2">
                  <Badge variant={insight.severity === 'moderate' ? 'warning' : insight.severity === 'high' ? 'error' : 'info'}>
                    {insight.severity.charAt(0).toUpperCase() + insight.severity.slice(1)}
                  </Badge>
                  <h3 className="font-semibold text-text-primary">
                    {insight.type.charAt(0).toUpperCase() + insight.type.slice(1).replace('_', ' ')} Bias
                  </h3>
                </div>
                <p className="text-base text-text-secondary mb-2">{insight.evidence}</p>
                <p className="text-sm text-forest-green font-medium">
                  Recommendation: {insight.recommendation}
                </p>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Specialty Breakdown */}
      {specialtyScores.length > 0 && (
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
      )}

      {/* Recommended Cases */}
      {recommendations.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold text-text-primary mb-6">Recommended For You</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {recommendations.map((rec, i) => (
              <Card key={i} hover padding="lg">
                <Badge variant={priorityColors[rec.priority] || 'info'} size="sm">
                  {rec.priority.toUpperCase()} PRIORITY
                </Badge>
                <h3 className="text-lg font-semibold text-text-primary mt-3 mb-1">{rec.type.replace('_', ' ')}</h3>
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
      )}
    </div>
  );
};
