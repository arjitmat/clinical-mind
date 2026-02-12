/**
 * AITutorPanel Component
 * Displays real-time feedback from the AI tutor
 */
import React, { useEffect, useRef } from 'react';
import type { TutorFeedback, FeedbackType } from '../types/simulation';

interface AITutorPanelProps {
  feedback: TutorFeedback[];
}

const AITutorPanel: React.FC<AITutorPanelProps> = ({ feedback }) => {
  const panelRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest feedback
  useEffect(() => {
    if (panelRef.current) {
      panelRef.current.scrollTop = panelRef.current.scrollHeight;
    }
  }, [feedback]);

  return (
    <div className="bg-warm-gray-50 rounded-2xl p-6 shadow-sm border border-warm-gray-100 h-full flex flex-col">
      {/* Header */}
      <div className="mb-4 pb-4 border-b border-warm-gray-200">
        <div className="flex items-center gap-2">
          <span className="text-2xl">💡</span>
          <h3 className="text-lg font-semibold text-text-primary">AI Tutor</h3>
        </div>
        <p className="text-sm text-text-secondary mt-1">
          Real-time guidance on your communication
        </p>
      </div>

      {/* Feedback List */}
      <div
        ref={panelRef}
        className="flex-1 overflow-y-auto space-y-3 pr-2"
        style={{ maxHeight: 'calc(100vh - 300px)' }}
      >
        {feedback.length === 0 ? (
          <div className="text-center py-12 text-text-tertiary">
            <p className="text-sm">Start the conversation to receive feedback</p>
          </div>
        ) : (
          feedback.map((fb, index) => (
            <FeedbackCard key={index} feedback={fb} index={index} />
          ))
        )}
      </div>

      {/* Legend */}
      <div className="mt-4 pt-4 border-t border-warm-gray-200">
        <div className="flex items-center gap-4 text-xs">
          <FeedbackTypeLegend type="positive" label="Good" />
          <FeedbackTypeLegend type="warning" label="Tip" />
          <FeedbackTypeLegend type="critical" label="Alert" />
        </div>
      </div>
    </div>
  );
};

/**
 * Individual Feedback Card
 */
const FeedbackCard: React.FC<{ feedback: TutorFeedback; index: number }> = ({
  feedback,
  index,
}) => {
  const config = getFeedbackConfig(feedback.type);

  return (
    <div
      className={`p-4 rounded-xl border-l-4 ${config.borderColor} ${config.bgColor} animate-fade-in-up`}
      style={{ animationDelay: `${index * 100}ms` }}
    >
      {/* Icon & Type */}
      <div className="flex items-center gap-2 mb-2">
        <span className="text-lg">{config.icon}</span>
        <span className={`text-xs font-semibold uppercase tracking-wide ${config.textColor}`}>
          {config.label}
        </span>
      </div>

      {/* Message */}
      <p className="text-sm text-text-primary leading-relaxed">{feedback.message}</p>

      {/* Timestamp */}
      <div className="mt-2 text-xs text-text-tertiary">
        {new Date(feedback.timestamp).toLocaleTimeString('en-US', {
          hour: '2-digit',
          minute: '2-digit',
        })}
      </div>
    </div>
  );
};

/**
 * Feedback Type Legend Item
 */
const FeedbackTypeLegend: React.FC<{ type: FeedbackType; label: string }> = ({ type, label }) => {
  const config = getFeedbackConfig(type);

  return (
    <div className="flex items-center gap-1.5">
      <span className={`w-2 h-2 rounded-full ${config.dotColor}`} />
      <span className="text-text-tertiary">{label}</span>
    </div>
  );
};

/**
 * Get feedback configuration based on type
 */
function getFeedbackConfig(type: FeedbackType): {
  icon: string;
  label: string;
  borderColor: string;
  bgColor: string;
  textColor: string;
  dotColor: string;
} {
  const configs = {
    positive: {
      icon: '✓',
      label: 'Good',
      borderColor: 'border-success',
      bgColor: 'bg-success/5',
      textColor: 'text-success',
      dotColor: 'bg-success',
    },
    warning: {
      icon: '⚠️',
      label: 'Tip',
      borderColor: 'border-warning',
      bgColor: 'bg-warning/5',
      textColor: 'text-warning',
      dotColor: 'bg-warning',
    },
    critical: {
      icon: '✗',
      label: 'Alert',
      borderColor: 'border-error',
      bgColor: 'bg-error/5',
      textColor: 'text-error',
      dotColor: 'bg-error',
    },
  };

  return configs[type] || configs.warning;
}

export default AITutorPanel;
