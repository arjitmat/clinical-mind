import React from 'react';

interface NurseAvatarProps {
  size?: number;
  urgencyLevel?: 'routine' | 'attention' | 'urgent' | 'critical';
  className?: string;
}

export const NurseAvatar: React.FC<NurseAvatarProps> = ({
  size = 40,
  urgencyLevel = 'routine',
  className = '',
}) => {
  const isAlert = urgencyLevel === 'urgent' || urgencyLevel === 'critical';

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Head */}
      <circle cx="16" cy="14" r="10" fill="#f0d9b5" stroke="#8B7355" strokeWidth="0.5" />

      {/* Hair - tied back */}
      <path
        d="M 7 13 Q 6 5 16 4 Q 26 5 25 13"
        fill="#1a0a00"
        stroke="#0d0500"
        strokeWidth="0.3"
      />
      {/* Hair bun */}
      <circle cx="22" cy="7" r="3" fill="#1a0a00" />

      {/* Nurse cap */}
      <rect x="10" y="3" width="12" height="4" rx="1" fill="white" stroke="#4a90d9" strokeWidth="0.5" />
      <line x1="14" y1="3" x2="14" y2="7" stroke="#e74c3c" strokeWidth="0.4" />
      <line x1="18" y1="3" x2="18" y2="7" stroke="#e74c3c" strokeWidth="0.4" />
      <line x1="12" y1="5" x2="20" y2="5" stroke="#e74c3c" strokeWidth="0.4" />

      {/* Eyes */}
      <circle cx="12" cy="13" r="1.1" fill="#2C1810" />
      <circle cx="20" cy="13" r="1.1" fill="#2C1810" />

      {/* Friendly smile */}
      <path d="M 13 19 Q 16 21 19 19" stroke="#8B4513" strokeWidth="0.6" fill="none" strokeLinecap="round" />

      {/* Scrubs collar */}
      <path d="M 9 24 L 12 22 L 16 24 L 20 22 L 23 24" stroke="#4a90d9" strokeWidth="1.2" fill="none" />

      {/* Stethoscope */}
      <path
        d="M 14 24 Q 12 27 14 29 Q 16 30 18 29 Q 20 27 18 24"
        stroke="#555"
        strokeWidth="0.7"
        fill="none"
      />
      <circle cx="16" cy="30" r="1.2" fill="#666" stroke="#444" strokeWidth="0.3" />

      {/* Alert indicator for urgent/critical */}
      {isAlert && (
        <g>
          <circle cx="27" cy="5" r="4" fill={urgencyLevel === 'critical' ? '#e74c3c' : '#f39c12'}>
            <animate attributeName="r" values="3.5;4.5;3.5" dur="1s" repeatCount="indefinite" />
          </circle>
          <text
            x="27"
            y="7"
            textAnchor="middle"
            fill="white"
            fontSize="5"
            fontWeight="bold"
          >
            !
          </text>
        </g>
      )}
    </svg>
  );
};
