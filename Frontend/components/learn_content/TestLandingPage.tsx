"use client";

import React, { useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";

// -----------------------
// TYPES
// -----------------------
interface Question {
  question: string;
  level: string;
  answer?: string;
  options?: string[];
  source?: string;
}

interface JobStatus {
  job_id: string;
  status: string;
  message: string;
  questions?: Question[];
}

// -----------------------
// COMPONENT
// -----------------------
export default function TestLandingPage() {
  const searchParams = useSearchParams();
  const videoUrl = searchParams.get("videoUrl") || "";
  const userParam = searchParams.get("userName") || "";
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

  // -----------------------
  // STATE
  // -----------------------
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(false);
  const [polling, setPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progressMessage, setProgressMessage] = useState<string | null>(null);
  const [userName, setUserName] = useState<string>("guest_user");
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);

  const controllerRef = useRef<AbortController | null>(null);
  const pollTimerRef = useRef<number | null>(null);
  const timeoutTimerRef = useRef<number | null>(null);

  const [answersState, setAnswersState] = useState<
    Record<number, { open: boolean; text: string; saving: boolean; saved: boolean }>
  >({});

  // -----------------------
  // SESSION INITIALIZATION (SAFE)
  // -----------------------
  useEffect(() => {
    if (typeof window === "undefined") return;

    const storedUser = sessionStorage.getItem("userName");
    if (userParam) {
      setUserName(userParam);
      sessionStorage.setItem("userName", userParam);
    } else if (storedUser) {
      setUserName(storedUser);
    }

    // Restore cached questions if available
    const cacheKey = `generatedQuestions:${videoUrl}`;
    const cached = sessionStorage.getItem(cacheKey);
    if (cached) {
      try {
        const parsed = JSON.parse(cached);
        if (Array.isArray(parsed) && parsed.length > 0) {
          console.log("✅ Loaded questions from session cache");
          setQuestions(parsed);
        }
      } catch (err) {
        console.error("Failed to parse cached questions:", err);
      }
    }
  }, [userParam, videoUrl]);

  // -----------------------
  // QUESTION & ANSWER HANDLERS
  // -----------------------
  const toggleQuestionOpen = (idx: number) => {
    setAnswersState((prev) => {
      const cur = prev[idx] || { open: false, text: "", saving: false, saved: false };
      return { ...prev, [idx]: { ...cur, open: !cur.open } };
    });
  };

  const updateAnswerText = (idx: number, text: string) => {
    setAnswersState((prev) => {
      const cur = prev[idx] || { open: true, text: "", saving: false, saved: false };
      return { ...prev, [idx]: { ...cur, text } };
    });
  };

  const submitAnswer = async (idx: number) => {
    const q = questions[idx];
    if (!q) return;
    const st = answersState[idx];
    if (!st || !st.text.trim()) {
      alert("Please type an answer before submitting.");
      return;
    }

    setAnswersState((prev) => ({ ...prev, [idx]: { ...(prev[idx] || {}), saving: true } }));

    try {
      const payload = {
        user_name: userName,
        topic: videoUrl || "unknown",
        question: q.question,
        answer: st.text.trim(),
      };

      const res = await fetch(`${API_BASE}/submit-answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail || `Server error ${res.status}`);
      }

      setAnswersState((prev) => ({
        ...prev,
        [idx]: { ...(prev[idx] || {}), saving: false, saved: true, open: false },
      }));
    } catch (err: any) {
      console.error("submitAnswer error:", err);
      alert("❌ Failed to save answer: " + (err?.message || "unknown error"));
      setAnswersState((prev) => ({ ...prev, [idx]: { ...(prev[idx] || {}), saving: false } }));
    }
  };

  // -----------------------
  // LONG-RUNNING JOB UI HINTS
  // -----------------------
  const startLongRunningHint = (ms = 45000) => {
    if (timeoutTimerRef.current) clearTimeout(timeoutTimerRef.current);
    timeoutTimerRef.current = window.setTimeout(() => {
      setProgressMessage(
        "⏳ This is taking longer than usual. Please wait — video processing might take time."
      );
    }, ms);
  };

  const clearLongRunningHint = () => {
    if (timeoutTimerRef.current) clearTimeout(timeoutTimerRef.current);
    timeoutTimerRef.current = null;
    setProgressMessage(null);
  };

  // -----------------------
  // FETCH QUESTIONS
  // -----------------------
  const fetchQuestions = async (videoUrlParam?: string) => {
    const url = videoUrlParam || videoUrl;
    if (!url) {
      setError("No video URL provided.");
      return;
    }
    if (loading || polling) return;

    if (typeof window !== "undefined") {
      sessionStorage.removeItem(`generatedQuestions:${url}`);
    }

    setLoading(true);
    setError(null);
    setQuestions([]);
    setProgressMessage("Starting question generation job...");

    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    startLongRunningHint(45000);

    try {
      const res = await fetch(
        `${API_BASE}/generate-questions?video_url=${encodeURIComponent(url)}&num_qs=10`,
        { method: "GET", signal: controller.signal }
      );

      if (!res.ok) throw new Error(`Server responded ${res.status}`);
      const data = await res.json();
      if (!data.job_id) throw new Error("Backend did not return job_id.");

      setCurrentJobId(data.job_id);
      setProgressMessage("Job queued — processing in background...");
      startPolling(data.job_id, url);
    } catch (err: any) {
      console.error("fetchQuestions error:", err);
      setError(err.message || "Unexpected error while starting job.");
    } finally {
      clearLongRunningHint();
      setLoading(false);
    }
  };

  // -----------------------
  // POLLING JOB STATUS
  // -----------------------
  const startPolling = (jobId: string, url: string) => {
    setPolling(true);
    pollTimerRef.current = window.setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/status/${jobId}`);
        const data: JobStatus = await res.json();

        if (data.status === "processing") {
          setProgressMessage(data.message || "Processing...");
        } else if (data.status === "completed") {
          clearInterval(pollTimerRef.current!);
          setPolling(false);
          setProgressMessage("✅ Job complete!");
          if (Array.isArray(data.questions)) {
            setQuestions(data.questions);
            if (typeof window !== "undefined") {
              sessionStorage.setItem(`generatedQuestions:${url}`, JSON.stringify(data.questions));
            }
          } else {
            setError("No questions returned from backend.");
          }
        } else if (data.status === "error") {
          clearInterval(pollTimerRef.current!);
          setPolling(false);
          setError(`Backend error: ${data.message}`);
        }
      } catch (err) {
        console.error("Polling error:", err);
        clearInterval(pollTimerRef.current!);
        setPolling(false);
        setError("Polling failed — backend stopped responding.");
      }
    }, 5000);
  };

  // -----------------------
  // EVALUATE ANSWERS
  // -----------------------
  const handleEvaluateScores = async () => {
    try {
      setProgressMessage("🔎 Evaluating your answers...");
      const res = await fetch(
        `${API_BASE}/evaluate-answers?user_name=${encodeURIComponent(
          userName
        )}&topic=${encodeURIComponent(videoUrl)}`,
        { method: "POST" }
      );

      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail || "Evaluation failed.");
      }

      const data = await res.json();
      if (typeof window !== "undefined") {
        sessionStorage.setItem("scoresData", JSON.stringify(data));
        sessionStorage.removeItem(`generatedQuestions:${videoUrl}`);
      }
      window.location.href = "/course/test/results";
    } catch (err: any) {
      alert("❌ Evaluation failed: " + (err.message || "unknown error"));
    } finally {
      setProgressMessage(null);
    }
  };

  // -----------------------
  // CANCEL REQUEST
  // -----------------------
  const cancelRequest = () => {
    controllerRef.current?.abort();
    if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    setPolling(false);
    setLoading(false);
    setProgressMessage(null);
    setError("Request cancelled by user.");
  };

  // RENDER QUESTIONS
  const renderQuestions = () => (
    <ul className="space-y-4">
      {questions.map((q, idx) => {
        const state = answersState[idx] || { open: false, text: "", saving: false, saved: false };
        return (
          <li
            key={idx}
            className="bg-white text-black rounded-lg p-4 shadow-md hover:shadow-lg transition-shadow duration-200 cursor-pointer"
          >
            <div onClick={() => toggleQuestionOpen(idx)} className="flex justify-between items-start">
              <div>
                <p className="font-medium">{q.question}</p>
                <p className="text-sm text-gray-700 mt-1">
                  Bloom Level:{" "}
                  <span className="font-semibold text-blue-700">{q.level}</span> • Source:{" "}
                  <span className="font-semibold">{q.source || "AI"}</span>
                </p>
              </div>

              {state.saved ? (
                <span className="bg-green-100 text-green-800 text-sm px-3 py-1 rounded">
                  ✅ Saved
                </span>
              ) : (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleQuestionOpen(idx);
                  }}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded"
                >
                  {state.open ? "Close" : "Answer"}
                </button>
              )}
            </div>

            {state.open && (
              <div className="mt-3">
                <textarea
                  value={state.text}
                  onChange={(e) => updateAnswerText(idx, e.target.value)}
                  placeholder="Type your answer here..."
                  rows={3}
                  disabled={state.saving || state.saved}
                  className="w-full p-2 rounded border"
                />
                <div className="mt-2 flex gap-2">
                  <button
                    onClick={() => submitAnswer(idx)}
                    disabled={state.saving || state.saved}
                    className={`px-3 py-2 rounded ${
                      state.saving || state.saved
                        ? "bg-gray-400"
                        : "bg-green-600 hover:bg-green-700 text-white"
                    }`}
                  >
                    {state.saving ? "Saving..." : state.saved ? "Saved" : "Submit Answer"}
                  </button>
                  <button
                    onClick={() =>
                      setAnswersState((prev) => ({
                        ...prev,
                        [idx]: { ...(prev[idx] || {}), open: false },
                      }))
                    }
                    className="px-3 py-2 rounded bg-gray-300 text-black"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </li>
        );
      })}
    </ul>
  );

  // -----------------------
  // MAIN RENDER
  // -----------------------
  return (
    <div className="p-6 min-h-screen bg-gradient-to-br from-pink-500 via-red-500 to-orange-400 text-white">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-4">🎓 AI-Generated Test</h1>

        {progressMessage && <div className="mb-4 p-3 bg-yellow-700 rounded">⏳ {progressMessage}</div>}

        {(loading || polling) && (
          <div className="mb-4">
            <p className="animate-pulse">
              Processing video — please wait, this may take a few minutes...
            </p>
            <div className="flex gap-2 mt-2">
              <button onClick={cancelRequest} className="bg-red-700 hover:bg-red-800 px-4 py-2 rounded">
                ✖ Cancel
              </button>
            </div>
          </div>
        )}

        {error && (
          <div className="mb-4 p-4 rounded bg-red-600">
            <p>⚠️ {error}</p>
            <button
              onClick={() => fetchQuestions()}
              className="bg-blue-600 hover:bg-blue-700 px-3 py-1 mt-2 rounded"
            >
              🔁 Retry
            </button>
          </div>
        )}

        {!loading && !polling && questions.length > 0 && (
          <div className="mt-6 bg-white/10 p-4 rounded-lg">
            <h2 className="text-2xl font-semibold mb-4">🧠 Bloom Questions</h2>
            {renderQuestions()}
          </div>
        )}

        {!loading && !polling && !error && questions.length === 0 && videoUrl && (
          <div className="mt-6 text-white/90 p-4 rounded bg-white/5">
            <p>⚠️ No questions found yet. Click “Generate” to start.</p>
            <div className="mt-3">
              <button
                onClick={() => fetchQuestions()}
                className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded"
              >
                Generate Questions
              </button>
            </div>
          </div>
        )}

        <button
          onClick={handleEvaluateScores}
          className="bg-purple-700 hover:bg-purple-800 px-4 py-2 rounded mt-6"
        >
          🎯 Evaluate Scores
        </button>
      </div>
    </div>
  );
}
