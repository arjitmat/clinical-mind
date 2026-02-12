/**
 * ChatMessage Component
 * Displays individual messages in the patient-student conversation
 */
import React from 'react';
import type { SimulationMessage } from '../types/simulation';

interface ChatMessageProps {
  message: SimulationMessage;
  index: number;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message, index }) => {
  const isStudent = message.role === 'student';

  return (
    <div
      className={`flex ${isStudent ? 'justify-end' : 'justify-start'} mb-6 animate-fade-in-up`}
      style={{ animationDelay: `${index * 100}ms` }}
    >
      <div
        className={`max-w-[70%] rounded-xl px-6 py-4 shadow-sm ${
          isStudent
            ? 'bg-forest-green text-cream-white'
            : 'bg-warm-gray-50 text-text-primary border border-warm-gray-100'
        }`}
      >
        {/* Role label */}
        <div
          className={`text-xs font-medium mb-2 uppercase tracking-wide ${
            isStudent ? 'text-cream-white/70' : 'text-text-tertiary'
          }`}
        >
          {isStudent ? 'You' : 'Patient'}
        </div>

        {/* Message content */}
        <p className="text-base leading-relaxed">{message.content}</p>

        {/* Timestamp */}
        <div
          className={`text-xs mt-2 ${
            isStudent ? 'text-cream-white/60' : 'text-text-tertiary'
          }`}
        >
          {new Date(message.timestamp).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </div>

        {/* Emotional state indicator (patient only) */}
        {!isStudent && message.emotional_state && (
          <div className="mt-3 pt-3 border-t border-warm-gray-200">
            <div className="flex items-center gap-2">
              <span className="text-xs text-text-secondary">Emotional state:</span>
              <EmotionalStateBadge state={message.emotional_state} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * Emotional State Badge
 */
const EmotionalStateBadge: React.FC<{ state: string }> = ({ state }) => {
  const stateConfig: Record<string, { color: string; label: string; emoji: string }> = {
    calm: { color: 'bg-success/10 text-success', label: 'Calm', emoji: '😌' },
    concerned: { color: 'bg-warning/10 text-warning', label: 'Concerned', emoji: '😟' },
    anxious: { color: 'bg-error/10 text-error', label: 'Anxious', emoji: '😰' },
    defensive: { color: 'bg-terracotta/10 text-terracotta', label: 'Defensive', emoji: '😤' },
  };

  const config = stateConfig[state] || stateConfig.calm;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium ${config.color}`}
    >
      <span>{config.emoji}</span>
      <span>{config.label}</span>
    </span>
  );
};

export default ChatMessage;
