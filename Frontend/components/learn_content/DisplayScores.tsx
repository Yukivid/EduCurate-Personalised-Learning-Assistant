"use client";

import React, { useEffect, useState } from "react";

interface EvalResult {
  question: string;
  answer: string;
  score: number;
  feedback: string;
  confidence: number;
}

export default function ScoresPage() {
  const [results, setResults] = useState<EvalResult[]>([]);
  const [userName, setUserName] = useState("");
  const [topic, setTopic] = useState("");

  useEffect(() => {
    const data = sessionStorage.getItem("scoresData");
    if (data) {
      const parsed = JSON.parse(data);
      setResults(parsed.results || []);
      setUserName(parsed.user_name || "");
      setTopic(parsed.topic || "");
    }
  }, []);

  if (results.length === 0)
    return (
      <div className="p-8 text-center text-gray-200">
        <h2 className="text-2xl font-semibold mb-4">No Evaluation Results</h2>
        <p>Try answering questions and click “Evaluate Scores”.</p>
      </div>
    );

  return (
    <div className="min-h-screen p-8 bg-gradient-to-br from-gray-900 via-purple-900 to-black text-white">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">
          🧮 Evaluation Results for {userName} ({topic})
        </h1>
        <ul className="space-y-6">
          {results.map((r, idx) => (
            <li
              key={idx}
              className="bg-white/10 p-4 rounded-lg shadow-md border border-purple-700"
            >
              <p className="text-lg font-semibold mb-2">{r.question}</p>
              <p className="text-sm mb-2 text-gray-300">
                <strong>Answer:</strong> {r.answer}
              </p>
              <p className="text-sm">
                <strong>Score:</strong>{" "}
                <span className="text-green-400 font-bold">{r.score}</span>/100
              </p>
              <p className="text-sm mt-1 text-yellow-300">
                <strong>Feedback:</strong> {r.feedback}
              </p>
              <p className="text-xs text-gray-400 mt-1">
                Confidence: {(r.confidence * 100).toFixed(1)}%
              </p>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
