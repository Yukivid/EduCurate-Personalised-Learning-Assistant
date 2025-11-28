"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { Home, Eye, EyeOff, Mail, Lock } from "lucide-react";

interface LoginData {
  userName: string;
  password: string;
}

function BackgroundOverlay() {
  return (
    <svg
      className="absolute inset-0 w-full h-full pointer-events-none z-0"
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 1440 900"
      fill="none"
    >
      <defs>
        <radialGradient id="bgGlow" cx="50%" cy="40%" r="60%" fx="50%" fy="50%" gradientTransform="rotate(0)">
          <stop offset="0%" stopColor="#52e0e7" stopOpacity="0.12" />
          <stop offset="50%" stopColor="#0f223b" stopOpacity="0.17" />
          <stop offset="100%" stopColor="#031528" stopOpacity="0.25" />
        </radialGradient>
      </defs>
      <rect width="100%" height="100%" fill="url(#bgGlow)" />
      {/* Decorative panels */}
      <path d="M340,0 Q420 200 0 340" stroke="#2281a2aa" strokeWidth="2" opacity="0.25" />
      <path d="M1100,0 Q1000 200 1440 340" stroke="#2281a2aa" strokeWidth="2" opacity="0.25" />
      <path d="M340,900 Q420 700 0 600" stroke="#2281a2aa" strokeWidth="2" opacity="0.25" />
      <path d="M1100,900 Q1000 700 1440 600" stroke="#2281a2aa" strokeWidth="2" opacity="0.25" />
      {/* More lines/panels can be added for complexity */}
    </svg>
  );
}

export default function Login() {
  const router = useRouter();
  const [userName, setUserName] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null); // For displaying error inline

  async function handleLogin() {
    const payload: LoginData = { userName, password };
    setErrorMessage(null); // Clear previous error on new attempt

    try {
      const response = await fetch("http://localhost:8000/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      console.log("Response status:", response.status, response);

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem("userName", userName);
        sessionStorage.setItem("user_id", data.user_id);
        router.push("/user-info");
      } else {
        let data;
        try {
          data = await response.json();
        } catch {
          const text = await response.text();
          data = { detail: text || "Login failed." };
        }

        const detail = data?.detail || "";

        if (
          response.status === 401 ||
          detail.toLowerCase().includes("incorrect password")
        ) {
          setErrorMessage("Incorrect password. Please try again.");
        } else if (
          response.status === 404 ||
          detail.toLowerCase().includes("user does not exist")
        ) {
          setErrorMessage("User does not exist. Please sign up first.");
        } else {
          setErrorMessage(detail || "Login failed. Please try again.");
        }
      }
    } catch (error) {
      setErrorMessage("Something went wrong.");
      console.error(error);
    }
  }

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-gradient-to-br from-[#052944] via-[#0a1842] to-[#044356] relative overflow-hidden">
      <BackgroundOverlay />
      <div className="relative z-10 flex flex-col items-center justify-center w-full min-h-screen">
        <div className="max-w-md w-full mx-auto bg-black/90 border border-cyan-800 rounded-2xl shadow-2xl px-8 py-10 backdrop-blur-xl">
          <h2 className="text-white text-2xl font-semibold text-center mb-2">
            Welcome Back
          </h2>
          <p className="text-gray-400 text-center mb-8">Login to your account to continue</p>
          <form
            className="flex flex-col gap-6"
            onSubmit={e => {
              e.preventDefault();
              handleLogin();
            }}
            autoComplete="off"
          >
            <div>
              <label htmlFor="username" className="block text-sm text-gray-300 mb-2">
                Username
              </label>
              <div className="relative">
                <span className="absolute top-1/2 left-3 -translate-y-1/2 text-gray-400">
                  <Mail size={20} />
                </span>
                <input
                  id="username"
                  type="text"
                  autoComplete="username"
                  placeholder="Enter your User Name"
                  value={userName}
                  onChange={e => setUserName(e.target.value)}
                  className="w-full py-3 pl-11 pr-4 rounded-md bg-[#181d24] text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-400 transition shadow-none border-none"
                  required
                />
              </div>
            </div>
            <div>
              <label htmlFor="password" className="block text-sm text-gray-300 mb-2">
                Password
              </label>
              <div className="relative">
                <span className="absolute top-1/2 left-3 -translate-y-1/2 text-gray-400">
                  <Lock size={20} />
                </span>
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="w-full py-3 pl-11 pr-12 rounded-md bg-[#181d24] text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-400 transition shadow-none border-none"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(v => !v)}
                  tabIndex={-1}
                  className="absolute top-1/2 right-3 -translate-y-1/2 text-gray-400 hover:text-gray-200"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
            </div>
            {/* Forgot password can be shown inline if desired */}
            <div className="text-right text-sm text-gray-400 mt-[-20px] mb-2 hover:underline cursor-pointer">
              Forgot password?
            </div>
            {errorMessage && (
              <div className="mb-2 text-red-500 text-center font-medium">{errorMessage}</div>
            )}
            <button
              type="submit"
              className="w-full py-3 rounded-md bg-gradient-to-r from-cyan-400 to-teal-400 text-black font-semibold text-lg shadow-lg hover:from-cyan-300 hover:to-teal-300 transition"
            >
              Login
            </button>
          </form>
        </div>
      </div>
      {/* Optionally: gradient overlays, grid effects here for subtle background accents */}
      {/* Remove or customize below for extra effect */}
      <div className="absolute inset-0 pointer-events-none z-0" />
    </div>
  );
}
