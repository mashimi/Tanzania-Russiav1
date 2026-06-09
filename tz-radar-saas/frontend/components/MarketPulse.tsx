"use client";

import { useState } from "react";
import { Globe, Lightbulb, MessageSquare } from "lucide-react";
import SentimentGauge from "./SentimentGauge";
import type { MarketInsight } from "@/lib/api";

interface MarketPulseProps {
  chinaInsights: MarketInsight[];
  russiaInsights: MarketInsight[];
}

export default function MarketPulse({
  chinaInsights,
  russiaInsights,
}: MarketPulseProps) {
  const [activeTab, setActiveTab] = useState<"china" | "russia">("china");

  const insights =
    activeTab === "china" ? chinaInsights : russiaInsights;

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Tabs */}
      <div className="flex border-b border-slate-200">
        <button
          onClick={() => setActiveTab("china")}
          className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
            activeTab === "china"
              ? "text-blue-600 border-b-2 border-blue-600 bg-blue-50 bg-opacity-50"
              : "text-slate-500 hover:text-slate-700 hover:bg-slate-50"
          }`}
        >
          <span className="mr-2">🇨🇳</span> China Market
        </button>
        <button
          onClick={() => setActiveTab("russia")}
          className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
            activeTab === "russia"
              ? "text-blue-600 border-b-2 border-blue-600 bg-blue-50 bg-opacity-50"
              : "text-slate-500 hover:text-slate-700 hover:bg-slate-50"
          }`}
        >
          <span className="mr-2">🇷🇺</span> Russia Market
        </button>
      </div>

      {/* Insights Content */}
      <div className="p-5">
        {insights.length > 0 ? (
          <div className="space-y-4">
            {insights.map((insight, idx) => (
              <div
                key={idx}
                className="bg-slate-50 rounded-lg p-4 border border-slate-100"
              >
                {/* Trend Header */}
                <div className="flex items-start justify-between mb-2">
                  <h4 className="font-semibold text-slate-900 text-sm flex items-center gap-2">
                    <Lightbulb className="w-4 h-4 text-amber-500" />
                    {insight.trend}
                  </h4>
                  <SentimentGauge sentiment={insight.sentiment} />
                </div>

                {/* Action Item */}
                <div className="bg-blue-50 border-l-2 border-blue-400 pl-3 py-2 mb-3 rounded-r text-sm">
                  <span className="text-xs font-semibold text-blue-700 uppercase tracking-wider">
                    Recommended Action
                  </span>
                  <p className="text-blue-800 text-sm mt-0.5">
                    {insight.action}
                  </p>
                </div>

                {/* Source Posts */}
                <div className="space-y-2">
                  {insight.posts.map((post, pIdx) => (
                    <div
                      key={pIdx}
                      className="bg-white rounded-lg p-3 border border-slate-200 text-xs"
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <MessageSquare className="w-3 h-3 text-slate-400" />
                        <span className="font-semibold text-blue-600">
                          [{post.platform}]
                        </span>
                        <span className="text-slate-400">@</span>
                        <span className="text-slate-600">{post.author}</span>
                        {post.engagement > 0 && (
                          <span className="ml-auto text-slate-400">
                            🔥 {post.engagement}
                          </span>
                        )}
                      </div>
                      <p className="text-slate-700 leading-relaxed">
                        {post.content_snippet.length > 180
                          ? post.content_snippet.slice(0, 180) + "..."
                          : post.content_snippet}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <Globe className="w-10 h-10 text-slate-300 mx-auto mb-3" />
            <p className="text-slate-500 text-sm">
              No significant trends detected in the{" "}
              {activeTab === "china" ? "China" : "Russia"} market today.
            </p>
            <p className="text-slate-400 text-xs mt-1">
              Run a new scan to refresh market intelligence.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}