import React, { useEffect, useState, useCallback, useRef } from 'react';

interface UrgentTimerProps {
  totalSeconds: number;
  label: string;
  onExpire: () => void;
  isActive: boolean;
}

/* ── Helpers ── */
function formatCountdown(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

function timerColor(remaining: number): { stroke: string; text: string; pulse: boolean; glow: string } {
  if (remaining <= 120) {
    return {
      stroke: '#DC2626',       /* red-600 */
      text: 'text-red-600',
      pulse: true,
      glow: 'shadow-[0_0_16px_rgba(220,38,38,0.35)]',
    };
  }
  if (remaining <= 300) {
    return {
      stroke: '#D97706',       /* amber-600 */
      text: 'text-amber-600',
      pulse: false,
      glow: 'shadow-[0_0_12px_rgba(217,119,6,0.2)]',
    };
  }
  return {
    stroke: '#2D5C3F',         /* forest-green */
    text: 'text-forest-green',
    pulse: false,
    glow: '',
  };
}

/* ── SVG circle constants ── */
const RADIUS = 42;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

export const UrgentTimer: React.FC<UrgentTimerProps> = ({
  totalSeconds,
  label,
  onExpire,
  isActive,
}) => {
  const [remaining, setRemaining] = useState(totalSeconds);
  const onExpireRef = useRef(onExpire);
  onExpireRef.current = onExpire;

  /* Reset when totalSeconds changes */
  useEffect(() => {
    setRemaining(totalSeconds);
  }, [totalSeconds]);

  /* Countdown interval */
  const tick = useCallback(() => {
    setRemaining((prev) => {
      if (prev <= 1) {
        onExpireRef.current();
        return 0;
      }
      return prev - 1;
    });
  }, []);

  useEffect(() => {
    if (!isActive || remaining <= 0) return;
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [isActive, remaining, tick]);

  /* Derived values */
  const progress = remaining / totalSeconds;
  const dashOffset = CIRCUMFERENCE * (1 - progress);
  const colors = timerColor(remaining);

  return (
    <div
      className={`inline-flex flex-col items-center gap-1.5 p-3 rounded-2xl bg-cream-white border border-warm-gray-100 transition-shadow duration-500 ${
        colors.glow
      } ${colors.pulse ? 'animate-urgent-pulse' : ''}`}
    >
      {/* Circular countdown */}
      <div className="relative w-24 h-24">
        <svg width="96" height="96" viewBox="0 0 96 96" className="-rotate-90">
          {/* Background track */}
          <circle
            cx="48"
            cy="48"
            r={RADIUS}
            fill="none"
            stroke="#E8E5E0"
            strokeWidth="6"
          />
          {/* Progress arc */}
          <circle
            cx="48"
            cy="48"
            r={RADIUS}
            fill="none"
            stroke={colors.stroke}
            strokeWidth="6"
            strokeLinecap="round"
            strokeDasharray={CIRCUMFERENCE}
            strokeDashoffset={dashOffset}
            className="transition-[stroke-dashoffset] duration-1000 ease-linear"
          />
        </svg>

        {/* Centre text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-lg font-bold tabular-nums ${colors.text}`}>
            {formatCountdown(remaining)}
          </span>
        </div>
      </div>

      {/* Label */}
      <span className="text-[11px] font-medium text-text-secondary text-center leading-tight max-w-[120px]">
        {label}
      </span>

      {/* Urgency badge */}
      {remaining <= 120 && remaining > 0 && (
        <span className="text-[10px] font-bold text-red-600 uppercase tracking-wider animate-pulse">
          Critical
        </span>
      )}
      {remaining <= 300 && remaining > 120 && (
        <span className="text-[10px] font-semibold text-amber-600 uppercase tracking-wider">
          Urgent
        </span>
      )}
      {remaining === 0 && (
        <span className="text-[10px] font-bold text-red-700 uppercase tracking-wider">
          Time Expired
        </span>
      )}
    </div>
  );
};
