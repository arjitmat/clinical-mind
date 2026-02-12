import React from 'react';
import { Link, useLocation } from 'react-router-dom';

export const Header: React.FC = () => {
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

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
          <span className="text-xl font-bold text-text-primary">
            Clinical<span className="text-forest-green">Mind</span>
          </span>
        </Link>

        <nav className="hidden md:flex items-center gap-8">
          <Link
            to="/cases"
            className={`text-base font-medium no-underline transition-colors duration-300 ${isActive('/cases') ? 'text-forest-green' : 'text-text-secondary hover:text-forest-green'}`}
          >
            Cases
          </Link>
          <Link
            to="/dashboard"
            className={`text-base font-medium no-underline transition-colors duration-300 ${isActive('/dashboard') ? 'text-forest-green' : 'text-text-secondary hover:text-forest-green'}`}
          >
            Dashboard
          </Link>
          <Link
            to="/knowledge-graph"
            className={`text-base font-medium no-underline transition-colors duration-300 ${isActive('/knowledge-graph') ? 'text-forest-green' : 'text-text-secondary hover:text-forest-green'}`}
          >
            Knowledge Map
          </Link>
        </nav>

        <div className="flex items-center gap-4">
          <div className="w-9 h-9 bg-sage-green/20 rounded-full flex items-center justify-center">
            <span className="text-sm font-semibold text-forest-green">SM</span>
          </div>
        </div>
      </div>
    </header>
  );
};
