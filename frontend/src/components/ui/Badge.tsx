import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info';
  size?: 'sm' | 'md';
}

const variantStyles = {
  default: 'bg-warm-gray-50 text-text-secondary border-warm-gray-100',
  success: 'bg-forest-green/10 text-forest-green border-forest-green/20',
  warning: 'bg-warning/10 text-warning border-warning/20',
  error: 'bg-terracotta/10 text-terracotta border-terracotta/20',
  info: 'bg-soft-blue/10 text-soft-blue border-soft-blue/20',
};

const sizeStyles = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-3 py-1 text-sm',
};

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  size = 'md',
}) => {
  return (
    <span className={`inline-flex items-center rounded-full border font-medium ${variantStyles[variant]} ${sizeStyles[size]}`}>
      {children}
    </span>
  );
};
