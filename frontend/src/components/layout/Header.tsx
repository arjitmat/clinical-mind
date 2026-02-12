import React from 'react';
import { Link } from 'react-router-dom';

export const Header: React.FC = () => {
  return (
    <header className="sticky top-0 z-50 bg-cream-white/80 backdrop-blur-md border-b border-warm-gray-100">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-3 no-underline">
          <div className="w-10 h-10 bg-forest-green rounded-xl flex items-center justify-center">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="#FFFCF7" strokeWidth="2" strokeLinejoin="round"/>
              <path d="M2 17L12 22L22 17" stroke="#FFFCF7" strokeWidth="2" strokeLinejoin="round"/>
              <path d="M2 12L12 17L22 12" stroke="#FFFCF7" strokeWidth="2" strokeLinejoin="round"/>
            </svg>
          </div>
          <div>
            <span className="text-xl font-bold text-text-primary">
              Clinical<span className="text-forest-green">Mind</span>
            </span>
            <p className="text-xs text-text-secondary mt-0.5">AI Patient Simulation</p>
          </div>
        </Link>

        <div className="text-sm text-text-tertiary">
          Powered by Claude Opus 4.6
        </div>
      </div>
    </header>
  );
};
