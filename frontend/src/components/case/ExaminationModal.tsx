import React, { useState } from 'react';

export interface ExaminationFindings {
  inspection?: string;
  palpation?: string;
  percussion?: string;
  auscultation?: string;
  special_tests?: string;
  images?: { label: string; description: string }[];
  sounds?: { label: string; description: string }[];
}

interface ExaminationModalProps {
  isOpen: boolean;
  onClose: () => void;
  findings: ExaminationFindings;
}

/* ── Section header icons ── */
const SECTION_META: Record<string, { icon: string; label: string }> = {
  inspection: { icon: '\uD83D\uDC41\uFE0F', label: 'Inspection' },
  palpation: { icon: '\u270B', label: 'Palpation' },
  percussion: { icon: '\uD83E\uDD1C', label: 'Percussion' },
  auscultation: { icon: '\uD83E\uDE7A', label: 'Auscultation' },
  special_tests: { icon: '\uD83E\uDDEA', label: 'Special Tests' },
};

/* ── Collapsible finding section ── */
const FindingSection: React.FC<{
  sectionKey: string;
  content: string;
}> = ({ sectionKey, content }) => {
  const [revealed, setRevealed] = useState(false);
  const meta = SECTION_META[sectionKey] || { icon: '\uD83D\uDCCB', label: sectionKey };

  return (
    <div className="border border-warm-gray-100 rounded-xl overflow-hidden transition-all duration-300">
      <button
        type="button"
        onClick={() => setRevealed((prev) => !prev)}
        className="w-full flex items-center justify-between px-4 py-3 bg-warm-gray-50 hover:bg-warm-gray-100/60 transition-colors cursor-pointer"
      >
        <div className="flex items-center gap-2">
          <span className="text-base">{meta.icon}</span>
          <span className="text-sm font-semibold text-text-primary">{meta.label}</span>
        </div>
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className={`text-text-tertiary transition-transform duration-300 ${
            revealed ? 'rotate-180' : ''
          }`}
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {revealed && (
        <div className="px-4 py-3 animate-fade-in-up">
          <p className="text-sm text-text-secondary leading-relaxed whitespace-pre-line font-serif">
            {content}
          </p>
        </div>
      )}

      {!revealed && (
        <div className="px-4 py-2">
          <span className="text-xs text-text-tertiary italic">Click to reveal findings</span>
        </div>
      )}
    </div>
  );
};

/* ── Image placeholder ── */
const ImageFinding: React.FC<{ label: string; description: string }> = ({ label, description }) => (
  <div className="border border-warm-gray-100 rounded-xl overflow-hidden">
    {/* Placeholder image area */}
    <div className="bg-warm-gray-50 h-36 flex flex-col items-center justify-center gap-2">
      <svg
        width="32"
        height="32"
        viewBox="0 0 24 24"
        fill="none"
        stroke="#8A8179"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
        <circle cx="8.5" cy="8.5" r="1.5" />
        <polyline points="21 15 16 10 5 21" />
      </svg>
      <span className="text-xs text-text-tertiary">Visual Finding</span>
    </div>
    <div className="px-3 py-2">
      <span className="text-xs font-semibold text-text-primary block">{label}</span>
      <p className="text-xs text-text-secondary mt-0.5 leading-relaxed">{description}</p>
    </div>
  </div>
);

/* ── Sound placeholder ── */
const SoundFinding: React.FC<{ label: string; description: string }> = ({ label, description }) => (
  <div className="flex items-start gap-3 p-3 border border-warm-gray-100 rounded-xl">
    {/* Play button icon */}
    <button
      type="button"
      className="flex-shrink-0 w-10 h-10 rounded-full bg-forest-green/10 flex items-center justify-center hover:bg-forest-green/20 transition-colors cursor-pointer"
      title={`Play: ${label}`}
    >
      <svg
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="#2D5C3F"
        stroke="none"
      >
        <polygon points="5 3 19 12 5 21 5 3" />
      </svg>
    </button>
    <div className="flex-1 min-w-0">
      <span className="text-xs font-semibold text-text-primary block">{label}</span>
      <p className="text-xs text-text-secondary mt-0.5 leading-relaxed">{description}</p>
    </div>
  </div>
);

/* ── Main Modal ── */
export const ExaminationModal: React.FC<ExaminationModalProps> = ({
  isOpen,
  onClose,
  findings,
}) => {
  if (!isOpen) return null;

  const textSections = (['inspection', 'palpation', 'percussion', 'auscultation', 'special_tests'] as const).filter(
    (key) => findings[key]
  );

  return (
    /* Overlay */
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-warm-gray-900/50 backdrop-blur-sm animate-fade-in"
        onClick={onClose}
      />

      {/* Modal panel */}
      <div className="relative w-full max-w-lg max-h-[85vh] bg-cream-white rounded-2xl shadow-xl border border-warm-gray-100 flex flex-col animate-fade-in-up overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-warm-gray-100">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-forest-green/10 flex items-center justify-center">
              <span className="text-base">{'\uD83E\uDE7A'}</span>
            </div>
            <div>
              <h2 className="text-sm font-bold text-text-primary">Physical Examination</h2>
              <p className="text-[10px] text-text-tertiary">Click each section to reveal findings</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-warm-gray-50 hover:bg-warm-gray-100 flex items-center justify-center transition-colors cursor-pointer"
            aria-label="Close"
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3">
          {/* Text-based finding sections */}
          {textSections.map((key) => (
            <FindingSection key={key} sectionKey={key} content={findings[key]!} />
          ))}

          {/* Visual findings */}
          {findings.images && findings.images.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold text-text-tertiary uppercase tracking-wider mb-2">
                Visual Findings
              </h3>
              <div className="grid grid-cols-2 gap-3">
                {findings.images.map((img, i) => (
                  <ImageFinding key={i} label={img.label} description={img.description} />
                ))}
              </div>
            </div>
          )}

          {/* Audio findings */}
          {findings.sounds && findings.sounds.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold text-text-tertiary uppercase tracking-wider mb-2">
                Audio Findings
              </h3>
              <div className="space-y-2">
                {findings.sounds.map((snd, i) => (
                  <SoundFinding key={i} label={snd.label} description={snd.description} />
                ))}
              </div>
            </div>
          )}

          {/* Empty state */}
          {textSections.length === 0 &&
            (!findings.images || findings.images.length === 0) &&
            (!findings.sounds || findings.sounds.length === 0) && (
              <div className="text-center py-8">
                <p className="text-sm text-text-tertiary">No examination findings available.</p>
              </div>
            )}
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-warm-gray-100">
          <button
            type="button"
            onClick={onClose}
            className="w-full py-2.5 rounded-xl bg-forest-green text-cream-white text-sm font-semibold hover:bg-forest-green-dark transition-colors cursor-pointer"
          >
            Close Examination
          </button>
        </div>
      </div>
    </div>
  );
};
