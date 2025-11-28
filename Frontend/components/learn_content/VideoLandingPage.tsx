"use client";

import React, { useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

declare global {
  interface Window {
    YT: any;
    onYouTubeIframeAPIReady: () => void;
  }
}

// Production-ready VideoLandingPage:
// - Loads YT iframe API once safely
// - Cleans up player and interval on unmount and video changes
// - Saves playback time and "completed" flag in sessionStorage
// - Debounces interval creation to avoid duplicates
export default function VideoLandingPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const videoId = searchParams.get("id") || "";

  const playerRef = useRef<any>(null);
  const intervalRef = useRef<number | null>(null);
  const [completed, setCompleted] = useState(false);

  // Load YT iframe API once
  useEffect(() => {
    if (!videoId) return;
    if (typeof window === "undefined") return;

    // If API already loaded, do nothing. Otherwise inject script.
    if (!document.getElementById("yt-iframe-script")) {
      const tag = document.createElement("script");
      tag.id = "yt-iframe-script";
      tag.src = "https://www.youtube.com/iframe_api";
      tag.async = true;
      document.body.appendChild(tag);
    }

    // Cleanup on unmount
    return () => {
      if (intervalRef.current) {
        window.clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      if (playerRef.current && typeof playerRef.current.destroy === "function") {
        try {
          playerRef.current.destroy();
        } catch (e) {
          console.warn("Error destroying YT player:", e);
        } finally {
          playerRef.current = null;
        }
      }
    };
  }, [videoId]);

  // Create player whenever YT API ready and videoId changes
  useEffect(() => {
    if (!videoId) return;

    // if already completed earlier
    const savedCompleted = sessionStorage.getItem(`video-${videoId}-completed`);
    if (savedCompleted === "true") setCompleted(true);

    const onYouTubeReady = () => {
      createPlayer();
    };

    if (window.YT && window.YT.Player) {
      createPlayer();
    } else {
      // set handler; this will get called once script is loaded
      window.onYouTubeIframeAPIReady = onYouTubeReady;
    }

    // ensure cleanup for this videoId
    return () => {
      if (intervalRef.current) {
        window.clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      if (playerRef.current && typeof playerRef.current.destroy === "function") {
        try {
          playerRef.current.destroy();
        } catch (e) {
          console.warn("Error destroying YT player on cleanup:", e);
        } finally {
          playerRef.current = null;
        }
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [videoId]);

  const createPlayer = () => {
    if (!videoId) return;

    // Destroy previous player (if exists)
    if (playerRef.current && typeof playerRef.current.destroy === "function") {
      try {
        playerRef.current.destroy();
      } catch (e) {
        console.warn("destroy previous player error:", e);
      } finally {
        playerRef.current = null;
      }
    }

    try {
      playerRef.current = new window.YT.Player("yt-player", {
        videoId,
        height: "100%",
        width: "100%",
        playerVars: { autoplay: 0, controls: 1 },
        events: {
          onReady: (event: any) => {
            const savedTime = sessionStorage.getItem(`video-${videoId}-time`);
            if (savedTime) {
              try {
                const t = parseFloat(savedTime);
                if (!Number.isNaN(t)) {
                  event.target.seekTo(t, true);
                }
              } catch (e) {
                // ignore seek errors
              }
            }
          },
          onStateChange: (event: any) => {
            // PLAYING: start interval to persist time
            if (event.data === window.YT.PlayerState.PLAYING) {
              // prevent duplicate intervals
              if (intervalRef.current) {
                window.clearInterval(intervalRef.current);
                intervalRef.current = null;
              }
              intervalRef.current = window.setInterval(() => {
                try {
                  const currentTime = playerRef.current?.getCurrentTime?.();
                  if (typeof currentTime === "number" && !Number.isNaN(currentTime)) {
                    sessionStorage.setItem(`video-${videoId}-time`, currentTime.toString());
                  }
                } catch (e) {
                  // ignore
                }
              }, 2000);
            } else if (
              event.data === window.YT.PlayerState.PAUSED ||
              event.data === window.YT.PlayerState.BUFFERING
            ) {
              if (intervalRef.current) {
                window.clearInterval(intervalRef.current);
                intervalRef.current = null;
              }
            }

            // ENDED: mark as completed
            if (event.data === window.YT.PlayerState.ENDED) {
              if (intervalRef.current) {
                window.clearInterval(intervalRef.current);
                intervalRef.current = null;
              }
              setCompleted(true);
              sessionStorage.setItem(`video-${videoId}-completed`, "true");
            }
          },
        },
      });
    } catch (err) {
      console.error("Error creating YT Player:", err);
    }
  };

  const handleWatchAgain = () => {
    if (!playerRef.current) return;
    try {
      playerRef.current.seekTo(0);
      playerRef.current.playVideo();
      setCompleted(false);
      sessionStorage.setItem(`video-${videoId}-completed`, "false");
    } catch (e) {
      console.warn("watch again error:", e);
    }
  };

  const handleTakeTest = () => {
    if (!videoId) return;
    // Compose full YouTube URL and navigate to test page
    const fullUrl = `https://www.youtube.com/watch?v=${videoId}`;
    router.push(`/course/test?videoUrl=${encodeURIComponent(fullUrl)}`);
  };

  if (!videoId) {
    return (
      <div className="flex items-center justify-center h-screen text-white bg-black">
        <div>
          <h2 className="text-xl font-semibold mb-2">No video selected</h2>
          <p className="text-sm">Provide a video id in query param like <code>?id=VIDEO_ID</code></p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-start min-h-screen bg-black text-white px-4 py-6">
      <h1 className="text-2xl font-bold mb-4">Now Playing</h1>

      <div className="w-full max-w-5xl aspect-video bg-black rounded overflow-hidden">
        <div id="yt-player" className="w-full h-full" />
      </div>

      {completed ? (
        <div className="mt-6 text-center">
          <p className="text-lg font-semibold mb-4">🎉 Video completed — ready for the test?</p>
          <div className="flex gap-4 justify-center">
            <button onClick={handleWatchAgain} className="bg-gray-700 hover:bg-gray-800 px-6 py-2 rounded-lg">
              No, Watch Again
            </button>
            <button onClick={handleTakeTest} className="bg-green-600 hover:bg-green-700 px-6 py-2 rounded-lg">
              Yea, Sure!
            </button>
          </div>
        </div>
      ) : (
        <div className="mt-6 text-center">
          <p className="text-sm text-gray-300">Watch the video to unlock the test. Progress is saved automatically.</p>
          <div className="mt-3">
            <button
              onClick={handleTakeTest}
              className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded"
              title="You can still take the test but completing the video improves relevancy"
            >
              Take Test (now)
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
