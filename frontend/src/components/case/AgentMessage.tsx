import React from 'react';
import { PatientAvatar, NurseAvatar, SeniorDoctorAvatar } from '../avatars';

export interface AgentMessageData {
  id: string;
  agent_type: 'patient' | 'nurse' | 'senior_doctor' | 'family' | 'lab_tech' | 'student' | 'system';
  display_name: string;
  content: string;
  distress_level?: string;
  urgency_level?: string;
  timestamp: Date;
  is_event?: boolean;
  is_teaching?: boolean;
  is_intervention?: boolean;
  event_type?: string;
}

interface AgentMessageProps {
  message: AgentMessageData;
}

/* ── Per-agent colour and name styling ── */
const AGENT_COLORS: Record<string, { bg: string; nameColor: string; tailColor: string }> = {
  patient: {
    bg: '#FFF8E1',
    nameColor: 'text-amber-700',
    tailColor: '#FFF8E1',
  },
  nurse: {
    bg: '#E3F2FD',
    nameColor: 'text-blue-700',
    tailColor: '#E3F2FD',
  },
  senior_doctor: {
    bg: '#E8F5E9',
    nameColor: 'text-emerald-700',
    tailColor: '#E8F5E9',
  },
  family: {
    bg: '#F3E5F5',
    nameColor: 'text-purple-700',
    tailColor: '#F3E5F5',
  },
  lab_tech: {
    bg: '#E0F7FA',
    nameColor: 'text-cyan-700',
    tailColor: '#E0F7FA',
  },
  student: {
    bg: '#DCF8C6',
    nameColor: 'text-text-primary',
    tailColor: '#DCF8C6',
  },
};

/* ── Avatar resolver ── */
const AgentAvatar: React.FC<{
  agentType: string;
  distressLevel?: string;
  urgencyLevel?: string;
}> = ({ agentType, distressLevel, urgencyLevel }) => {
  const SIZE = 36;
  const wrapperClass =
    'w-9 h-9 rounded-full flex items-center justify-center text-lg flex-shrink-0 shadow-sm';

  switch (agentType) {
    case 'patient':
      return (
        <div className={wrapperClass}>
          <PatientAvatar
            size={SIZE}
            distressLevel={
              (distressLevel as 'low' | 'moderate' | 'high' | 'critical') || 'moderate'
            }
          />
        </div>
      );
    case 'nurse':
      return (
        <div className={wrapperClass}>
          <NurseAvatar
            size={SIZE}
            urgencyLevel={
              (urgencyLevel as 'routine' | 'attention' | 'urgent' | 'critical') || 'routine'
            }
          />
        </div>
      );
    case 'senior_doctor':
      return (
        <div className={wrapperClass}>
          <SeniorDoctorAvatar size={SIZE} />
        </div>
      );
    case 'family':
      return (
        <div
          className={wrapperClass}
          style={{ backgroundColor: '#F3E5F5' }}
          aria-label="Family member"
        >
          <span role="img" aria-label="family">
            {'\uD83D\uDC68\u200D\uD83D\uDC69\u200D\uD83D\uDC66'}
          </span>
        </div>
      );
    case 'lab_tech':
      return (
        <div
          className={wrapperClass}
          style={{ backgroundColor: '#E0F7FA' }}
          aria-label="Lab technician"
        >
          <span role="img" aria-label="lab">
            {'\uD83E\uDDEA'}
          </span>
        </div>
      );
    default:
      return null;
  }
};

/* ── Timestamp formatter ── */
function formatTimestamp(date: Date): string {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true });
}

/* ── Urgency border class ── */
function urgencyBorderClass(level?: string): string {
  if (level === 'critical') return 'border-l-[3px] border-l-red-500';
  if (level === 'urgent') return 'border-l-[3px] border-l-amber-500';
  return '';
}

/* ── Event (system) message ── */
const EventMessage: React.FC<{ message: AgentMessageData }> = ({ message }) => (
  <div className="flex justify-center my-3 animate-fade-in-up">
    <div className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full bg-warm-gray-100/80 backdrop-blur-sm shadow-sm max-w-[85%]">
      <span className="text-xs text-text-secondary text-center leading-snug">
        {message.content}
      </span>
      <span className="text-[10px] text-text-tertiary ml-1 whitespace-nowrap">
        {formatTimestamp(message.timestamp)}
      </span>
    </div>
  </div>
);

/* ── Main component ── */
export const AgentMessage: React.FC<AgentMessageProps> = ({ message }) => {
  /* Event / system messages get a centred pill style */
  if (message.is_event) {
    return <EventMessage message={message} />;
  }

  const isStudent = message.agent_type === 'student';
  const colors = AGENT_COLORS[message.agent_type] || AGENT_COLORS.student;

  /* Urgency border */
  const urgencyBorder = !isStudent ? urgencyBorderClass(message.urgency_level) : '';

  /* Teaching highlight */
  const teachingRing =
    message.is_teaching && message.agent_type === 'senior_doctor'
      ? 'ring-2 ring-emerald-300/60 ring-offset-1'
      : '';

  /* Intervention alert border */
  const interventionBorder = message.is_intervention
    ? 'border-2 border-terracotta/60 shadow-md'
    : '';

  return (
    <div
      className={`flex items-end gap-2 mb-2 animate-fade-in-up ${
        isStudent ? 'flex-row-reverse' : 'flex-row'
      }`}
    >
      {/* Avatar — only for non-student (left side) */}
      {!isStudent && (
        <div className="flex-shrink-0 mb-1">
          <AgentAvatar
            agentType={message.agent_type}
            distressLevel={message.distress_level}
            urgencyLevel={message.urgency_level}
          />
        </div>
      )}

      {/* Bubble + tail container */}
      <div className={`relative max-w-[75%] ${isStudent ? 'items-end' : 'items-start'}`}>
        {/* CSS triangle tail */}
        <div
          className={`absolute top-2 w-0 h-0 ${
            isStudent
              ? 'right-[-6px] border-t-[6px] border-t-transparent border-b-[6px] border-b-transparent border-l-[6px]'
              : 'left-[-6px] border-t-[6px] border-t-transparent border-b-[6px] border-b-transparent border-r-[6px]'
          }`}
          style={
            isStudent
              ? { borderLeftColor: colors.bg }
              : { borderRightColor: colors.bg }
          }
        />

        {/* Message bubble */}
        <div
          className={`relative px-3 py-2 text-sm leading-relaxed shadow-sm ${
            isStudent ? 'rounded-2xl rounded-tr-sm' : 'rounded-2xl rounded-tl-sm'
          } ${urgencyBorder} ${teachingRing} ${interventionBorder}`}
          style={{ backgroundColor: colors.bg }}
        >
          {/* Agent name (not shown for student) */}
          {!isStudent && (
            <div className={`text-xs font-bold mb-0.5 ${colors.nameColor}`}>
              {message.display_name}
            </div>
          )}

          {/* Teaching badge */}
          {message.is_teaching && (
            <span className="inline-block text-[10px] font-semibold px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-700 mb-1">
              Teaching
            </span>
          )}

          {/* Intervention badge */}
          {message.is_intervention && (
            <span className="inline-block text-[10px] font-semibold px-1.5 py-0.5 rounded bg-red-100 text-red-700 mb-1 ml-1">
              Intervention
            </span>
          )}

          {/* Content */}
          <div className="text-text-primary whitespace-pre-line">{message.content}</div>

          {/* Timestamp — bottom right, WhatsApp style */}
          <div className="flex justify-end mt-1">
            <span className="text-[10px] text-text-tertiary leading-none">
              {formatTimestamp(message.timestamp)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
