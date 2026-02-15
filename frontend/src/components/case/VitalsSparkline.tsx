import React, { useMemo } from 'react';

interface SparklineProps {
  data: number[];
  label: string;
  unit: string;
  color?: 'green' | 'amber' | 'red';
  width?: number;
  height?: number;
  showValue?: boolean;
}

export const VitalsSparkline: React.FC<SparklineProps> = ({
  data,
  label,
  unit,
  color = 'green',
  width = 60,
  height = 20,
  showValue = true,
}) => {
  const pathData = useMemo(() => {
    if (data.length < 2) return '';

    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;

    // Calculate points
    const points = data.map((value, index) => {
      const x = (index / (data.length - 1)) * width;
      const y = height - ((value - min) / range) * height;
      return `${x},${y}`;
    });

    return `M ${points.join(' L ')}`;
  }, [data, width, height]);

  const currentValue = data[data.length - 1];
  const previousValue = data[data.length - 2];
  const trend = currentValue > previousValue ? '↑' : currentValue < previousValue ? '↓' : '';

  const colorClasses = {
    green: 'stroke-green-500',
    amber: 'stroke-amber-500',
    red: 'stroke-red-500',
  };

  const textColorClasses = {
    green: 'text-green-600',
    amber: 'text-amber-600',
    red: 'text-red-600',
  };

  return (
    <div className="flex items-center gap-1">
      <div className="flex-shrink-0">
        <svg width={width} height={height} className="overflow-visible">
          {/* Background grid */}
          <line
            x1="0"
            y1={height / 2}
            x2={width}
            y2={height / 2}
            stroke="#e5e7eb"
            strokeWidth="0.5"
            strokeDasharray="2,2"
          />

          {/* Sparkline path */}
          {pathData && (
            <path
              d={pathData}
              fill="none"
              className={colorClasses[color]}
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          )}

          {/* Current value dot */}
          {data.length > 0 && (
            <circle
              cx={width}
              cy={height - ((currentValue - Math.min(...data)) / (Math.max(...data) - Math.min(...data) || 1)) * height}
              r="2"
              className={`fill-current ${textColorClasses[color]}`}
            />
          )}
        </svg>
      </div>

      {showValue && (
        <div className="flex items-baseline gap-0.5 min-w-[45px]">
          <span className={`text-[11px] font-medium ${textColorClasses[color]}`}>
            {currentValue}
          </span>
          <span className="text-[9px] text-text-tertiary">
            {unit}
          </span>
          {trend && (
            <span className={`text-[10px] ml-0.5 ${textColorClasses[color]}`}>
              {trend}
            </span>
          )}
        </div>
      )}
    </div>
  );
};

interface VitalsHistoryPanelProps {
  vitalsHistory: Array<{
    bp_systolic: number;
    bp_diastolic: number;
    hr: number;
    rr: number;
    temp: number;
    spo2: number;
  }>;
}

export const VitalsHistoryPanel: React.FC<VitalsHistoryPanelProps> = ({ vitalsHistory }) => {
  // Extract individual vital histories
  const hrHistory = vitalsHistory.map(v => v.hr);
  const bpSystolicHistory = vitalsHistory.map(v => v.bp_systolic);
  const bpDiastolicHistory = vitalsHistory.map(v => v.bp_diastolic);
  const rrHistory = vitalsHistory.map(v => v.rr);
  const tempHistory = vitalsHistory.map(v => v.temp);
  const spo2History = vitalsHistory.map(v => v.spo2);

  // Determine colors based on current values
  const getHRColor = (hr: number) => {
    if (hr > 120 || hr < 50) return 'red';
    if (hr > 100 || hr < 60) return 'amber';
    return 'green';
  };

  const getSpO2Color = (spo2: number) => {
    if (spo2 < 90) return 'red';
    if (spo2 < 94) return 'amber';
    return 'green';
  };

  const getBPColor = (systolic: number) => {
    if (systolic > 180 || systolic < 90) return 'red';
    if (systolic > 140 || systolic < 100) return 'amber';
    return 'green';
  };

  const getRRColor = (rr: number) => {
    if (rr > 30 || rr < 8) return 'red';
    if (rr > 24 || rr < 12) return 'amber';
    return 'green';
  };

  const getTempColor = (temp: number) => {
    if (temp > 39 || temp < 35) return 'red';
    if (temp > 38 || temp < 36) return 'amber';
    return 'green';
  };

  const currentVitals = vitalsHistory[vitalsHistory.length - 1];

  if (!currentVitals) return null;

  return (
    <div className="space-y-1.5">
      <div className="text-[10px] font-semibold text-text-tertiary uppercase tracking-wide mb-1">
        Vitals Trends (Last {vitalsHistory.length} readings)
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div className="bg-warm-gray-50 rounded p-1.5">
          <div className="text-[9px] text-text-tertiary">HR</div>
          <VitalsSparkline
            data={hrHistory}
            label="HR"
            unit="bpm"
            color={getHRColor(currentVitals.hr)}
          />
        </div>

        <div className="bg-warm-gray-50 rounded p-1.5">
          <div className="text-[9px] text-text-tertiary">SpO2</div>
          <VitalsSparkline
            data={spo2History}
            label="SpO2"
            unit="%"
            color={getSpO2Color(currentVitals.spo2)}
          />
        </div>

        <div className="bg-warm-gray-50 rounded p-1.5">
          <div className="text-[9px] text-text-tertiary">BP</div>
          <div className="flex items-center gap-0.5">
            <VitalsSparkline
              data={bpSystolicHistory}
              label="Sys"
              unit=""
              color={getBPColor(currentVitals.bp_systolic)}
              width={30}
              showValue={false}
            />
            <span className={`text-[11px] font-medium ${
              getBPColor(currentVitals.bp_systolic) === 'red' ? 'text-red-600' :
              getBPColor(currentVitals.bp_systolic) === 'amber' ? 'text-amber-600' :
              'text-green-600'
            }`}>
              {currentVitals.bp_systolic}/{currentVitals.bp_diastolic}
            </span>
          </div>
        </div>

        <div className="bg-warm-gray-50 rounded p-1.5">
          <div className="text-[9px] text-text-tertiary">RR</div>
          <VitalsSparkline
            data={rrHistory}
            label="RR"
            unit="/min"
            color={getRRColor(currentVitals.rr)}
          />
        </div>
      </div>

      <div className="bg-warm-gray-50 rounded p-1.5">
        <div className="text-[9px] text-text-tertiary">Temperature</div>
        <VitalsSparkline
          data={tempHistory}
          label="Temp"
          unit="°C"
          color={getTempColor(currentVitals.temp)}
          width={120}
        />
      </div>
    </div>
  );
};

export default VitalsSparkline;