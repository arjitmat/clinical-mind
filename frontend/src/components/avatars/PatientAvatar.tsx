import React from 'react';

interface PatientAvatarProps {
  size?: number;
  distressLevel?: 'low' | 'moderate' | 'high' | 'critical';
  className?: string;
}

export const PatientAvatar: React.FC<PatientAvatarProps> = ({
  size = 40,
  distressLevel = 'moderate',
  className = '',
}) => {
  const faceColor = distressLevel === 'critical' ? '#e8d5d0' : distressLevel === 'high' ? '#edd9c5' : '#f0d9b5';
  const mouthPath =
    distressLevel === 'critical'
      ? 'M 14 22 Q 16 20 18 22' // grimace
      : distressLevel === 'high'
        ? 'M 14 21 Q 16 19 18 21' // frown
        : distressLevel === 'moderate'
          ? 'M 14 20 L 18 20' // flat
          : 'M 14 20 Q 16 22 18 20'; // slight smile

  const eyeY = distressLevel === 'critical' ? '14' : '13';
  const browOffset = distressLevel === 'high' || distressLevel === 'critical' ? -1 : 0;

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
      <circle cx="16" cy="14" r="10" fill={faceColor} stroke="#8B7355" strokeWidth="0.5" />

      {/* Hair */}
      <path
        d="M 6 14 Q 6 5 16 4 Q 26 5 26 14"
        fill="#2C1810"
        stroke="#1a0f09"
        strokeWidth="0.3"
      />

      {/* Eyes */}
      <circle cx="12" cy={eyeY} r="1.2" fill="#2C1810" />
      <circle cx="20" cy={eyeY} r="1.2" fill="#2C1810" />

      {/* Eyebrows */}
      <line x1="10" y1={10 + browOffset} x2="14" y2={9.5 + browOffset} stroke="#2C1810" strokeWidth="0.6" strokeLinecap="round" />
      <line x1="18" y1={9.5 + browOffset} x2="22" y2={10 + browOffset} stroke="#2C1810" strokeWidth="0.6" strokeLinecap="round" />

      {/* Mouth */}
      <path d={mouthPath} stroke="#8B4513" strokeWidth="0.7" fill="none" strokeLinecap="round" />

      {/* Hospital gown collar */}
      <path d="M 10 24 Q 16 26 22 24" stroke="#6B9BD2" strokeWidth="1.5" fill="none" />

      {/* Distress indicators */}
      {(distressLevel === 'high' || distressLevel === 'critical') && (
        <>
          {/* Sweat drops */}
          <ellipse cx="7" cy="12" rx="0.6" ry="1" fill="#87CEEB" opacity="0.7">
            <animate attributeName="cy" values="12;14;12" dur="1.5s" repeatCount="indefinite" />
          </ellipse>
          <ellipse cx="25" cy="11" rx="0.5" ry="0.8" fill="#87CEEB" opacity="0.6">
            <animate attributeName="cy" values="11;13;11" dur="1.8s" repeatCount="indefinite" />
          </ellipse>
        </>
      )}

      {distressLevel === 'critical' && (
        <>
          {/* Pain lines */}
          <line x1="3" y1="8" x2="5" y2="9" stroke="#cc0000" strokeWidth="0.5" opacity="0.6">
            <animate attributeName="opacity" values="0.6;0.2;0.6" dur="0.8s" repeatCount="indefinite" />
          </line>
          <line x1="27" y1="8" x2="29" y2="9" stroke="#cc0000" strokeWidth="0.5" opacity="0.6">
            <animate attributeName="opacity" values="0.6;0.2;0.6" dur="0.8s" repeatCount="indefinite" />
          </line>
        </>
      )}
    </svg>
  );
};
