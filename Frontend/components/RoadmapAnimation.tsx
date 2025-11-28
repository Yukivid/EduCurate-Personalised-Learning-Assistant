"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";

interface Props {
  topics: string[];
  onTopicSelect: (topic: string) => void;
  initialIndex?: number;
}

export default function RoadmapAnimation({
  topics,
  onTopicSelect,
  initialIndex = 0,
}: Props) {
  const [current, setCurrent] = useState<number>(initialIndex);

  useEffect(() => {
    setCurrent(initialIndex);
  }, [topics, initialIndex]);

  const handleClick = (idx: number) => {
    setCurrent(idx);
    onTopicSelect(topics[idx]);
  };

  if (!topics || topics.length === 0) {
    return null;
  }

  const steps = topics.length;
  const clamp = (v: number) => Math.max(0, Math.min(v, steps - 1));
  const percent = (i: number) =>
    steps === 1 ? 50 : (i / Math.max(steps - 1, 1)) * 100;

  return (
    <div className="w-full flex flex-col items-center py-6">
      {/* Timeline container */}
      <div className="relative w-full max-w-4xl px-4">
        {/* horizontal line */}
        <div className="absolute left-0 right-0 top-1/2 -translate-y-1/2 h-1 bg-gray-300 rounded" />

        {/* moving car */}
        <motion.div
          className="absolute -top-8 text-3xl"
          animate={{
            left: `${percent(clamp(current))}%`,
            translateX: "-50%",
          }}
          transition={{ type: "spring", stiffness: 90, damping: 14 }}
        >
          🚗
        </motion.div>

        {/* Checkpoints */}
        <div className="relative min-h-[72px]">
          {topics.map((topic, i) => (
            <div
              key={i}
              onClick={() => handleClick(i)}
              style={{ left: `${percent(i)}%`, transform: "translateX(-50%)" }}
              className="absolute top-1/2 -translate-y-1/2 flex flex-col items-center cursor-pointer"
            >
              <div
                className={`w-8 h-8 rounded-full mb-2 transition-colors flex items-center justify-center text-sm font-semibold ${
                  i <= current
                    ? "bg-green-500 border-2 border-green-600 text-white"
                    : "bg-white border-2 border-gray-300 text-gray-700"
                }`}
              >
                {i + 1}
              </div>
              <div className="max-w-[120px] text-center text-xs text-white break-words">
                {topic}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
