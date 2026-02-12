import React from 'react';

interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'tertiary';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
  type?: 'button' | 'submit';
}

const variantStyles = {
  primary: 'bg-forest-green text-cream-white hover:bg-forest-green-dark shadow-[0_2px_8px_rgba(45,92,63,0.15)] hover:shadow-[0_4px_12px_rgba(45,92,63,0.25)] hover:-translate-y-0.5 active:translate-y-0',
  secondary: 'bg-transparent text-forest-green border-2 border-warm-gray-100 hover:border-forest-green hover:bg-forest-green/[0.04]',
  tertiary: 'bg-transparent text-text-secondary hover:text-forest-green hover:bg-warm-gray-50',
};

const sizeStyles = {
  sm: 'px-4 py-2 text-sm rounded-lg',
  md: 'px-7 py-3.5 text-base rounded-xl',
  lg: 'px-8 py-4 text-lg rounded-xl',
};

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  children,
  onClick,
  disabled = false,
  className = '',
  type = 'button',
}) => {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`font-semibold transition-all duration-300 ease-out cursor-pointer inline-flex items-center justify-center gap-2 ${variantStyles[variant]} ${sizeStyles[size]} ${disabled ? 'opacity-50 cursor-not-allowed' : ''} ${className}`}
    >
      {children}
    </button>
  );
};
