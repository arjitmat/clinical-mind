import React from 'react';

interface LanguageToggleProps {
  language: 'en' | 'hi';
  onToggle: (lang: 'en' | 'hi') => void;
}

export const LanguageToggle: React.FC<LanguageToggleProps> = ({ language, onToggle }) => {
  return (
    <div className="inline-flex items-center">
      {/* Pill container */}
      <div className="relative flex items-center bg-warm-gray-100 rounded-full p-0.5 cursor-pointer select-none">
        {/* Sliding highlight */}
        <div
          className={`absolute top-0.5 h-[calc(100%-4px)] w-[calc(50%-2px)] rounded-full bg-forest-green shadow-sm transition-transform duration-300 ease-out ${
            language === 'hi' ? 'translate-x-[calc(100%+4px)]' : 'translate-x-0'
          }`}
        />

        {/* EN button */}
        <button
          type="button"
          onClick={() => onToggle('en')}
          className={`relative z-10 px-3 py-1 text-xs font-semibold rounded-full transition-colors duration-300 ${
            language === 'en' ? 'text-cream-white' : 'text-text-secondary hover:text-text-primary'
          }`}
        >
          EN
        </button>

        {/* Divider */}
        <span className="relative z-10 text-[10px] text-text-tertiary mx-0.5">|</span>

        {/* HI button */}
        <button
          type="button"
          onClick={() => onToggle('hi')}
          className={`relative z-10 px-3 py-1 text-xs font-semibold rounded-full transition-colors duration-300 ${
            language === 'hi' ? 'text-cream-white' : 'text-text-secondary hover:text-text-primary'
          }`}
        >
          HI
        </button>
      </div>

      {/* Translate badge when EN is active */}
      {language === 'en' && (
        <span className="ml-2 inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-soft-blue/10 text-soft-blue text-[10px] font-medium animate-fade-in-up">
          <svg
            width="10"
            height="10"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M5 8l6 6" />
            <path d="M4 14l6-6 2-3" />
            <path d="M2 5h12" />
            <path d="M7 2h1" />
            <path d="M22 22l-5-10-5 10" />
            <path d="M14 18h6" />
          </svg>
          Translate
        </span>
      )}
    </div>
  );
};
