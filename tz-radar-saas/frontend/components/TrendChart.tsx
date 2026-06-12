"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

interface TrendDataPoint {
  date: string;
  mentions: number;
  sentiment: number; // 0 to 100 scale for visual consistency
}

interface TrendChartProps {
  data: TrendDataPoint[];
}

export default function TrendChart({ data }: TrendChartProps) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-slate-900">
          📈 Market Pulse (Last 7 Days)
        </h3>
        <p className="text-sm text-slate-500 mt-1">
          Tracking mention volume and overall sentiment trends.
        </p>
      </div>

      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
            <XAxis 
              dataKey="date" 
              stroke="#64748b" 
              fontSize={12} 
              tickLine={false} 
              axisLine={false} 
            />
            <YAxis 
              yAxisId="left"
              stroke="#3b82f6" 
              fontSize={12} 
              tickLine={false} 
              axisLine={false} 
            />
            <YAxis 
              yAxisId="right" 
              orientation="right" 
              stroke="#10b981" 
              fontSize={12} 
              tickLine={false} 
              axisLine={false}
              domain={[0, 100]}
            />
            <Tooltip 
              contentStyle={{ 
                background: "#ffffff", 
                border: "1px solid #e2e8f0", 
                borderRadius: "8px",
                boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)"
              }}
              labelStyle={{ color: "#0f172a", fontWeight: 600 }}
            />
            <Legend verticalAlign="top" height={36} />
            
            {/* Mentions Line */}
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="mentions"
              name="Mentions"
              stroke="#3b82f6"
              strokeWidth={3}
              dot={{ r: 4, fill: "#3b82f6", strokeWidth: 2, stroke: "#ffffff" }}
              activeDot={{ r: 6, fill: "#3b82f6" }}
            />
            
            {/* Sentiment Line (Scaled to 0-100) */}
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="sentiment"
              name="Sentiment Score"
              stroke="#10b981"
              strokeWidth={3}
              strokeDasharray="5 5"
              dot={{ r: 4, fill: "#10b981", strokeWidth: 2, stroke: "#ffffff" }}
              activeDot={{ r: 6, fill: "#10b981" }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}