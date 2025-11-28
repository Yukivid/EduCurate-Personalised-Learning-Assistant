"use client";

import React, { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import axios from "axios";
import SearchResults from "./SearchResults";

type Video = {
  id: { videoId: string };
  snippet: {
    title: string;
    channelTitle: string;
    publishedAt: string;
    thumbnails: { medium: { url: string } };
    description: string;
  };
};

export default function CourseVideos() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const topic = searchParams.get("topic");

  // Load videos from sessionStorage based on current topic or default empty
  const getVideosFromSession = (topic: string | null): Video[] => {
    if (!topic) return [];
    if (typeof window === "undefined") return [];
    const raw = sessionStorage.getItem(`videos-${topic}`);
    if (!raw) return [];
    try {
      return JSON.parse(raw) as Video[];
    } catch {
      return [];
    }
  };

  const [videos, setVideos] = useState<Video[]>(() => getVideosFromSession(topic));
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!topic) {
      setVideos([]);
      return;
    }

    // If videos for topic exist in session, use them (already in state from init)
    // Else fetch from API
    if (getVideosFromSession(topic).length > 0) {
      setVideos(getVideosFromSession(topic));
      return;
    }

    setIsLoading(true);
    axios
      .get(`http://localhost:8000/search?q=${encodeURIComponent(topic)}`)
      .then((res) => {
        const fetchedVideos = res.data.items || [];
        setVideos(fetchedVideos);
        // Save to session for persistence
        sessionStorage.setItem(`videos-${topic}`, JSON.stringify(fetchedVideos));
      })
      .catch((err) => {
        console.error("Failed to fetch videos for topic:", err);
      })
      .finally(() => setIsLoading(false));
  }, [topic]);

  // Persist videos to sessionStorage whenever videos state changes
  useEffect(() => {
    if (topic && videos.length > 0) {
      sessionStorage.setItem(`videos-${topic}`, JSON.stringify(videos));
    }
  }, [videos, topic]);

  const handleVideoClick = (videoId: string) => {
    router.push(`/course/videos/watch?id=${videoId}`);
  };

  return (
    <div className="flex flex-col items-center px-4 py-10">
      <h1 className="text-3xl font-bold mb-6 text-pink-800 text-center">
        Videos for Topic: {topic}
      </h1>
      {videos.length === 0 ? (
        <div className="text-gray-600 mt-8">Searching Best Videos...</div>
      ) : (
        <SearchResults
          videos={videos.map((v) => ({
            id: v.id.videoId,
            title: v.snippet.title,
            channel: v.snippet.channelTitle,
            thumbnail: v.snippet.thumbnails.medium.url,
            duration: "N/A",
            views: "N/A",
            publishedAt: v.snippet.publishedAt,
            description: v.snippet.description ?? "",
          }))}
          isLoading={isLoading}
          viewMode={"grid"}
          onViewModeChange={() => {}}
          onLoadMore={() => {}}
          hasMore={false}
          onVideoClick={handleVideoClick}
        />
      )}
    </div>
  );
}
