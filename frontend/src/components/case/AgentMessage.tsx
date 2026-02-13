import React from 'react';
import { PatientAvatar, NurseAvatar, SeniorDoctorAvatar } from '../avatars';

export interface AgentMessageData {
  id: string;
  agent_type: 'patient' | 'nurse' | 'senior_doctor' | 'student';
  display_name: string;
  content: string;
  distress_level?: string;
  urgency_level?: string;
  timestamp: Date;
}

interface AgentMessageProps {
  message: AgentMessageData;
}

const agentStyles: Record<string, { bg: string; border: string; nameColor: string }> = {
  patient: {
    bg: 'bg-amber-50',
    border: 'border-amber-200',
    nameColor: 'text-amber-700',
  },
  nurse: {
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    nameColor: 'text-blue-700',
  },
  senior_doctor: {
    bg: 'bg-emerald-50',
    border: 'border-emerald-200',
    nameColor: 'text-emerald-700',
  },
  student: {
    bg: 'bg-warm-gray-50',
    border: 'border-warm-gray-200',
    nameColor: 'text-text-primary',
  },
};

const AgentAvatarIcon: React.FC<{ agentType: string; distressLevel?: string; urgencyLevel?: string }> = ({
  agentType,
  distressLevel,
  urgencyLevel,
}) => {
  switch (agentType) {
    case 'patient':
      return (
        <PatientAvatar
          size={28}
          distressLevel={(distressLevel as 'low' | 'moderate' | 'high' | 'critical') || 'moderate'}
        />
      );
    case 'nurse':
      return (
        <NurseAvatar
          size={28}
          urgencyLevel={(urgencyLevel as 'routine' | 'attention' | 'urgent' | 'critical') || 'routine'}
        />
      );
    case 'senior_doctor':
      return <SeniorDoctorAvatar size={28} />;
    default:
      return (
        <div className="w-7 h-7 rounded-full bg-warm-gray-200 flex items-center justify-center text-xs font-bold text-text-primary">
          You
        </div>
      );
  }
};

export const AgentMessage: React.FC<AgentMessageProps> = ({ message }) => {
  const isStudent = message.agent_type === 'student';
  const style = agentStyles[message.agent_type] || agentStyles.student;

  return (
    <div className={`flex gap-2 ${isStudent ? 'flex-row-reverse' : 'flex-row'}`}>
      <div className="flex-shrink-0 mt-1">
        <AgentAvatarIcon
          agentType={message.agent_type}
          distressLevel={message.distress_level}
          urgencyLevel={message.urgency_level}
        />
      </div>
      <div
        className={`p-3 rounded-xl text-sm leading-relaxed border max-w-[85%] ${style.bg} ${style.border}`}
      >
        {!isStudent && (
          <div className={`text-xs font-semibold mb-1 ${style.nameColor}`}>
            {message.display_name}
          </div>
        )}
        <div className="text-text-primary">{message.content}</div>
      </div>
    </div>
  );
};
