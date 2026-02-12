import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-warm-gray-100 bg-warm-gray-50 mt-auto">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-forest-green rounded-lg flex items-center justify-center">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="#FFFCF7" strokeWidth="2" strokeLinejoin="round"/>
                <path d="M2 17L12 22L22 17" stroke="#FFFCF7" strokeWidth="2" strokeLinejoin="round"/>
                <path d="M2 12L12 17L22 12" stroke="#FFFCF7" strokeWidth="2" strokeLinejoin="round"/>
              </svg>
            </div>
            <span className="text-sm text-text-secondary">
              Clinical<span className="text-forest-green font-semibold">Mind</span> - Master clinical reasoning, one case at a time
            </span>
          </div>
          <div className="text-sm text-text-tertiary">
            Built for Indian medical students
          </div>
        </div>
      </div>
    </footer>
  );
};
