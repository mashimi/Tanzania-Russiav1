"use client";

interface ReadinessGaugeProps {
  score: number; // 0 to 100
}

export default function ReadinessGauge({ score }: ReadinessGaugeProps) {
  // Clamp score between 0 and 100
  const clampedScore = Math.max(0, Math.min(100, score));
  
  // Determine color and label based on score
  const getColor = (s: number) => {
    if (s >= 80) return { color: "#10b981", label: "Excellent", bg: "bg-emerald-50", text: "text-emerald-700" };
    if (s >= 60) return { color: "#f59e0b", label: "Moderate", bg: "bg-amber-50", text: "text-amber-700" };
    return { color: "#ef4444", label: "Attention Needed", bg: "bg-red-50", text: "text-red-700" };
  };

  const { color, label, bg, text } = getColor(clampedScore);

  // SVG Circle math
  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (clampedScore / 100) * circumference;

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex flex-col items-center justify-center">
      <h3 className="text-lg font-semibold text-slate-900 mb-2 w-full text-left">
        🎯 Market Readiness Score
      </h3>
      <p className="text-sm text-slate-500 mb-6 w-full text-left">
        Aggregated health based on payment friction, visa clarity, and crisis signals.
      </p>

      <div className="relative flex items-center justify-center">
        {/* Background Circle */}
        <svg className="transform -rotate-90 w-32 h-32">
          <circle
            cx="64"
            cy="64"
            r={radius}
            stroke="#e2e8f0"
            strokeWidth="8"
            fill="transparent"
          />
          {/* Progress Circle */}
          <circle
            cx="64"
            cy="64"
            r={radius}
            stroke={color}
            strokeWidth="8"
            fill="transparent"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-out"
          />
        </svg>
        
        {/* Center Text */}
        <div className="absolute flex flex-col items-center">
          <span className="text-3xl font-bold text-slate-900">{clampedScore}</span>
          <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">/ 100</span>
        </div>
      </div>

      {/* Status Badge */}
      <div className={`mt-6 px-4 py-1.5 rounded-full text-sm font-semibold ${bg} ${text}`}>
        {label}
      </div>
    </div>
  );
}