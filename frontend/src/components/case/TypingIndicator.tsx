import React from 'react';

interface TypingIndicatorProps {
  agentName: string;
  agentType: string;
}

const AGENT_BG: Record<string, string> = {
  patient: '#FFF8E1',
  nurse: '#E3F2FD',
  senior_doctor: '#E8F5E9',
  family: '#F3E5F5',
  lab_tech: '#E0F7FA',
};

const AGENT_NAME_COLOR: Record<string, string> = {
  patient: 'text-amber-700',
  nurse: 'text-blue-700',
  senior_doctor: 'text-emerald-700',
  family: 'text-purple-700',
  lab_tech: 'text-cyan-700',
};

export const TypingIndicator: React.FC<TypingIndicatorProps> = ({ agentName, agentType }) => {
  const bg = AGENT_BG[agentType] || '#F5F3F0';
  const nameColor = AGENT_NAME_COLOR[agentType] || 'text-text-secondary';

  return (
    <div className="flex items-end gap-2 mb-2 animate-fade-in-up">
      {/* Spacer to align with avatar column */}
      <div className="w-9 flex-shrink-0" />

      {/* Bubble */}
      <div className="relative max-w-[55%]">
        {/* Tail */}
        <div
          className="absolute top-2 left-[-6px] w-0 h-0 border-t-[6px] border-t-transparent border-b-[6px] border-b-transparent border-r-[6px]"
          style={{ borderRightColor: bg }}
        />

        <div
          className="px-3 py-2 rounded-2xl rounded-tl-sm shadow-sm"
          style={{ backgroundColor: bg }}
        >
          <span className={`text-xs font-bold ${nameColor}`}>{agentName}</span>
          <div className="flex items-center gap-1 mt-1">
            <span className="typing-dot w-[6px] h-[6px] rounded-full bg-text-tertiary inline-block animate-typing-bounce" />
            <span className="typing-dot w-[6px] h-[6px] rounded-full bg-text-tertiary inline-block animate-typing-bounce animate-delay-150" />
            <span className="typing-dot w-[6px] h-[6px] rounded-full bg-text-tertiary inline-block animate-typing-bounce animate-delay-300" />
            <span className="text-[10px] text-text-tertiary ml-1.5">is typing...</span>
          </div>
        </div>
      </div>
    </div>
  );
};
