import React from 'react';

interface SeniorDoctorAvatarProps {
  size?: number;
  isThinking?: boolean;
  className?: string;
}

export const SeniorDoctorAvatar: React.FC<SeniorDoctorAvatarProps> = ({
  size = 40,
  isThinking = false,
  className = '',
}) => {
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
      <circle cx="16" cy="14" r="10" fill="#e8c99b" stroke="#8B7355" strokeWidth="0.5" />

      {/* Hair - grey/distinguished */}
      <path
        d="M 7 14 Q 6 4 16 3 Q 26 4 25 14"
        fill="#888"
        stroke="#666"
        strokeWidth="0.3"
      />
      {/* Slightly receding hairline */}
      <path d="M 9 8 Q 12 6 16 5.5 Q 20 6 23 8" fill="#e8c99b" />

      {/* Glasses */}
      <rect x="9" y="11" width="5.5" height="4" rx="1.5" stroke="#333" strokeWidth="0.6" fill="none" />
      <rect x="17.5" y="11" width="5.5" height="4" rx="1.5" stroke="#333" strokeWidth="0.6" fill="none" />
      <line x1="14.5" y1="13" x2="17.5" y2="13" stroke="#333" strokeWidth="0.5" />
      <line x1="9" y1="12.5" x2="7" y2="12" stroke="#333" strokeWidth="0.4" />
      <line x1="23" y1="12.5" x2="25" y2="12" stroke="#333" strokeWidth="0.4" />

      {/* Eyes behind glasses */}
      <circle cx="12" cy="13" r="0.9" fill="#2C1810" />
      <circle cx="20" cy="13" r="0.9" fill="#2C1810" />

      {/* Slight mustache */}
      <path d="M 13 17.5 Q 16 18.5 19 17.5" stroke="#777" strokeWidth="0.5" fill="none" />

      {/* Confident smile */}
      <path d="M 13 19.5 Q 16 21 19 19.5" stroke="#8B4513" strokeWidth="0.5" fill="none" strokeLinecap="round" />

      {/* White coat collar */}
      <path d="M 8 24 L 12 21 L 16 23 L 20 21 L 24 24" stroke="#fff" strokeWidth="1.5" fill="white" />
      <line x1="16" y1="23" x2="16" y2="28" stroke="#ddd" strokeWidth="0.5" />

      {/* Name badge */}
      <rect x="18" y="24" width="5" height="3" rx="0.5" fill="#4a90d9" stroke="#3a7bc8" strokeWidth="0.3" />
      <text x="20.5" y="26.2" textAnchor="middle" fill="white" fontSize="2">DR</text>

      {/* Thinking bubble when active */}
      {isThinking && (
        <g>
          <circle cx="5" cy="5" r="1" fill="#ddd" opacity="0.6">
            <animate attributeName="opacity" values="0.3;0.8;0.3" dur="1.5s" repeatCount="indefinite" />
          </circle>
          <circle cx="3" cy="3" r="1.8" fill="#ddd" opacity="0.5">
            <animate attributeName="opacity" values="0.2;0.7;0.2" dur="1.5s" repeatCount="indefinite" begin="0.3s" />
          </circle>
          <ellipse cx="0" cy="0" rx="3" ry="2" fill="#eee" stroke="#ccc" strokeWidth="0.3" opacity="0.7">
            <animate attributeName="opacity" values="0.4;0.9;0.4" dur="1.5s" repeatCount="indefinite" begin="0.6s" />
          </ellipse>
          <text x="0" y="1" textAnchor="middle" fill="#666" fontSize="2.5" opacity="0.8">?</text>
        </g>
      )}
    </svg>
  );
};
