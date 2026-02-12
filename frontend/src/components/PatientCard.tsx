/**
 * PatientCard Component
 * Displays patient avatar, emotional state, and rapport meter
 */
import React from 'react';
import type { EmotionalState, RapportLevel, PatientInfo } from '../types/simulation';

interface PatientCardProps {
  patientInfo: PatientInfo;
  emotionalState: EmotionalState;
  rapportLevel: RapportLevel;
  avatarPath: string;
  settingContext: string;
}

const PatientCard: React.FC<PatientCardProps> = ({
  patientInfo,
  emotionalState,
  rapportLevel,
  avatarPath,
  settingContext,
}) => {
  return (
    <div className="bg-warm-gray-50 rounded-2xl p-8 shadow-sm border border-warm-gray-100">
      {/* Setting Context */}
      <div className="mb-6 pb-6 border-b border-warm-gray-200">
        <div className="text-xs uppercase tracking-wide text-text-tertiary font-medium mb-1">
          Setting
        </div>
        <div className="text-sm text-text-secondary">{settingContext}</div>
      </div>

      {/* Avatar */}
      <div className="flex flex-col items-center mb-6">
        <div className="relative">
          {/* Avatar with smooth transition */}
          <div className="w-48 h-48 rounded-2xl overflow-hidden bg-cream-white shadow-md transition-transform duration-300 hover:scale-105">
            <img
              src={avatarPath}
              alt={`${patientInfo.name} - ${emotionalState}`}
              className="w-full h-full object-contain"
              key={avatarPath} // Force re-render on avatar change
            />
          </div>

          {/* Emotional state indicator overlay */}
          <div className="absolute -top-2 -right-2">
            <EmotionalStateIndicator state={emotionalState} />
          </div>
        </div>

        {/* Patient Name & Info */}
        <div className="text-center mt-4">
          <h3 className="text-xl font-semibold text-text-primary mb-1">
            {patientInfo.name}
          </h3>
          <p className="text-sm text-text-secondary">
            {patientInfo.age}yo {patientInfo.gender}
          </p>
        </div>
      </div>

      {/* Chief Complaint */}
      <div className="mb-6 p-4 bg-cream-white rounded-xl border border-warm-gray-100">
        <div className="text-xs uppercase tracking-wide text-text-tertiary font-medium mb-2">
          Chief Complaint
        </div>
        <p className="text-base text-text-primary">{patientInfo.chief_complaint}</p>
      </div>

      {/* Emotional State Gauge */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs uppercase tracking-wide text-text-tertiary font-medium">
            Emotional State
          </span>
          <span className="text-sm font-medium text-text-primary capitalize">
            {emotionalState}
          </span>
        </div>
        <EmotionalStateBar state={emotionalState} />
      </div>

      {/* Rapport Meter */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs uppercase tracking-wide text-text-tertiary font-medium">
            Rapport
          </span>
          <span className="text-sm font-medium text-text-primary">
            {rapportLevel}/5
          </span>
        </div>
        <RapportMeter level={rapportLevel} />
      </div>
    </div>
  );
};

/**
 * Emotional State Indicator (floating badge)
 */
const EmotionalStateIndicator: React.FC<{ state: EmotionalState }> = ({ state }) => {
  const stateConfig: Record<EmotionalState, { color: string; emoji: string }> = {
    calm: { color: 'bg-success', emoji: '😌' },
    concerned: { color: 'bg-warning', emoji: '😟' },
    anxious: { color: 'bg-error', emoji: '😰' },
    defensive: { color: 'bg-terracotta', emoji: '😤' },
  };

  const config = stateConfig[state];

  return (
    <div
      className={`${config.color} w-12 h-12 rounded-full flex items-center justify-center text-2xl shadow-lg animate-scale-pulse`}
    >
      {config.emoji}
    </div>
  );
};

/**
 * Emotional State Bar (visual representation)
 */
const EmotionalStateBar: React.FC<{ state: EmotionalState }> = ({ state }) => {
  const stateOrder: EmotionalState[] = ['calm', 'concerned', 'anxious', 'defensive'];
  const currentIndex = stateOrder.indexOf(state);

  return (
    <div className="flex gap-1.5">
      {stateOrder.map((s, index) => {
        const isActive = index === currentIndex;
        const isPassed = index < currentIndex;

        let colorClass = 'bg-warm-gray-200';
        if (isActive || isPassed) {
          if (s === 'calm') colorClass = 'bg-success';
          else if (s === 'concerned') colorClass = 'bg-warning';
          else if (s === 'anxious') colorClass = 'bg-error';
          else if (s === 'defensive') colorClass = 'bg-terracotta';
        }

        return (
          <div
            key={s}
            className={`flex-1 h-2 rounded-full ${colorClass} transition-all duration-500`}
          />
        );
      })}
    </div>
  );
};

/**
 * Rapport Meter (1-5 dots)
 */
const RapportMeter: React.FC<{ level: RapportLevel }> = ({ level }) => {
  return (
    <div className="flex gap-2">
      {[1, 2, 3, 4, 5].map((dot) => (
        <div
          key={dot}
          className={`flex-1 h-2 rounded-full transition-all duration-500 ${
            dot <= level ? 'bg-forest-green' : 'bg-warm-gray-200'
          }`}
        />
      ))}
    </div>
  );
};

export default PatientCard;
