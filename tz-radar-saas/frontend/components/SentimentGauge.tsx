"use client";

import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface SentimentGaugeProps {
  sentiment: string; // "Positive" | "Negative" | "Neutral"
  label?: string;
}

const sentimentConfig: Record<
  string,
  { color: string; bg: string; icon: React.ReactNode; text: string }
> = {
  Positive: {
    color: "text-emerald-700",
    bg: "bg-emerald-100",
    icon: <TrendingUp className="w-4 h-4" />,
    text: "Positive",
  },
  Negative: {
    color: "text-red-700",
    bg: "bg-red-100",
    icon: <TrendingDown className="w-4 h-4" />,
    text: "Negative",
  },
  Neutral: {
    color: "text-amber-700",
    bg: "bg-amber-100",
    icon: <Minus className="w-4 h-4" />,
    text: "Neutral",
  },
};

export default function SentimentGauge({
  sentiment,
  label,
}: SentimentGaugeProps) {
  const config = sentimentConfig[sentiment] || sentimentConfig["Neutral"];

  return (
    <div className="flex items-center gap-2">
      {label && <span className="text-xs text-slate-500">{label}:</span>}
      <span
        className={`inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full ${config.bg} ${config.color}`}
      >
        {config.icon}
        {config.text}
      </span>
    </div>
  );
}