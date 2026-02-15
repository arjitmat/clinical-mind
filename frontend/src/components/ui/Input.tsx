import React from 'react';

interface InputProps {
  placeholder?: string;
  value: string;
  onChange: (value: string) => void;
  onKeyPress?: (e: React.KeyboardEvent) => void;
  onKeyDown?: (e: React.KeyboardEvent) => void;
  label?: string;
  className?: string;
  multiline?: boolean;
  rows?: number;
}

export const Input: React.FC<InputProps> = ({
  placeholder,
  value,
  onChange,
  onKeyPress,
  onKeyDown,
  label,
  className = '',
  multiline = false,
  rows = 3,
}) => {
  const baseStyles = 'w-full p-3.5 rounded-xl border-[1.5px] border-warm-gray-100 bg-cream-white text-text-primary text-base placeholder:text-text-tertiary focus:outline-none focus:border-forest-green focus:ring-2 focus:ring-forest-green/10 transition-all duration-300';

  return (
    <div className={className}>
      {label && (
        <label className="block text-sm font-medium text-text-secondary mb-2">
          {label}
        </label>
      )}
      {multiline ? (
        <textarea
          placeholder={placeholder}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyPress={onKeyPress}
          onKeyDown={onKeyDown}
          rows={rows}
          className={`${baseStyles} resize-none`}
        />
      ) : (
        <input
          type="text"
          placeholder={placeholder}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyPress={onKeyPress}
          onKeyDown={onKeyDown}
          className={baseStyles}
        />
      )}
    </div>
  );
};
