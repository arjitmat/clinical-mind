import React from 'react';

interface CardProps {
  children: React.ReactNode;
  hover?: boolean;
  padding?: 'sm' | 'md' | 'lg';
  className?: string;
  onClick?: () => void;
}

const paddingStyles = {
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8',
};

export const Card: React.FC<CardProps> = ({
  children,
  hover = false,
  padding = 'md',
  className = '',
  onClick,
}) => {
  return (
    <div
      onClick={onClick}
      className={`bg-cream-white border-[1.5px] border-warm-gray-100 rounded-2xl shadow-[0_2px_8px_rgba(42,37,32,0.04)] transition-all duration-400 ${paddingStyles[padding]} ${hover ? 'cursor-pointer hover:border-forest-green hover:shadow-[0_4px_16px_rgba(45,92,63,0.08)] hover:-translate-y-0.5' : ''} ${className}`}
    >
      {children}
    </div>
  );
};
