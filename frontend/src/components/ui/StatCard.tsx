import React from 'react';

interface StatCardProps {
  title: string;
  value: string;
  trend?: string;
  color?: 'green' | 'blue' | 'terracotta';
  icon?: React.ReactNode;
}

const colorStyles = {
  green: 'border-l-forest-green',
  blue: 'border-l-soft-blue',
  terracotta: 'border-l-terracotta',
};

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  trend,
  color = 'green',
  icon,
}) => {
  return (
    <div className={`bg-cream-white border-[1.5px] border-warm-gray-100 rounded-2xl p-6 border-l-4 ${colorStyles[color]} shadow-[0_2px_8px_rgba(42,37,32,0.04)]`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-text-tertiary font-medium">{title}</span>
        {icon && <span className="text-text-tertiary">{icon}</span>}
      </div>
      <div className="text-2xl font-bold text-text-primary mb-1">{value}</div>
      {trend && (
        <div className="text-sm text-sage-green font-medium">{trend}</div>
      )}
    </div>
  );
};
