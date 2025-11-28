"use client";

import React, { useState, useEffect } from "react";
import axios from "axios";
import { Search, Filter, Play, User } from "lucide-react";
import { useRouter } from "next/navigation";
import { FileUpload } from "@/components/ui/file-upload";
import { Sidebar, SidebarBody, SidebarLink } from "@/components/ui/sidebar";
import SearchFilters from "./SearchFilters";

type SidebarTopic = {
  label: string;
  query: string;
  href: string;
  icon: React.ReactNode;
};
type RoadmapItem = {
  topic: string;
  summary?: string;
  estimated_time?: number;
  recommended_time?: number;
  [k: string]: any;
};

type VideoSearchProps = {
  userName: string;
};

function LoaderOverlay() {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="flex flex-col items-center">
        <svg className="animate-spin h-16 w-16 text-cyan-400 mb-4" viewBox="0 0 24 24">
          <circle
            className="opacity-30"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
            fill="none"
          />
          <path
            className="opacity-80"
            fill="currentColor"
            d="M12 2a10 10 0 000 20V2z"
          />
        </svg>
        <span className="text-white text-xl font-semibold">
          Generating Roadmap...
        </span>
      </div>
    </div>
  );
}

export default function VideoSearch({ userName }: VideoSearchProps) {
  const router = useRouter();
  const [open, setOpen] = useState(false);

  const getFromSession = <T,>(key: string, fallback: T): T => {
    if (typeof window === "undefined") return fallback;
    const raw = sessionStorage.getItem(key);
    if (!raw) return fallback;
    try {
      return JSON.parse(raw) as T;
    } catch {
      return fallback;
    }
  };

  const [query, setQuery] = useState(() => getFromSession("query", ""));
  const [roadmapSchedule, setRoadmapSchedule] = useState<RoadmapItem[]>(() =>
    getFromSession("roadmapSchedule", [])
  );

  useEffect(() => {
    sessionStorage.setItem("query", JSON.stringify(query));
  }, [query]);
  useEffect(() => {
    sessionStorage.setItem("roadmapSchedule", JSON.stringify(roadmapSchedule));
  }, [roadmapSchedule]);

  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [isLoading, setIsLoading] = useState(false);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [appliedFilters, setAppliedFilters] = useState<any>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [parsedSyllabus, setParsedSyllabus] = useState<string | null>(null);
  const [uploadingMode, setUploadingMode] = useState(false);
  const [sidebarTopics, setSidebarTopics] = useState<SidebarTopic[]>([]);

  const handleSearch = async () => {
    setIsLoading(true);
    try {
      const searchQuery =
        query && query.trim() !== ""
          ? query.trim()
          : files.length
          ? parsedSyllabus || ""
          : "";

      if (!searchQuery) {
        setRoadmapSchedule([]);
        setIsLoading(false);
        return;
      }

      const payload = {
        userName: userName,
        query: searchQuery,
        original_keywords: [],
        user_model: { mastered_nodes: [], learning_speed: 1.0 },
        time_budget: 120,
      };

      const res = await axios.post(
        "http://localhost:8000/generate-roadmap/",
        payload
      );
      const schedule: RoadmapItem[] = res.data.schedule || [];
      setRoadmapSchedule(schedule);
    } catch (err) {
      console.error("Search failed", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleScheduleCellClick = (topic: string) => {
    router.push(`/course/videos?topic=${encodeURIComponent(topic)}`);
  };

  const handleFiltersChange = (filters: any) => setAppliedFilters(filters);

  const handleFileUpload = (uploadedFiles: File[]) => {
    setFiles(uploadedFiles);
    setParsedSyllabus(null);
    setSidebarTopics([]);
  };

  const handleDoneUploading = async () => {
    if (files.length === 0) return;
    const formData = new FormData();
    formData.append("file", files[0]);
    try {
      const res = await axios.post(
        "http://localhost:8000/upload-syllabus",
        formData
      );
      const moduleStructure = res.data.module_structure;
      const modules = res.data.modules as { title: string; topics: string[] }[];
      setParsedSyllabus(moduleStructure);

      const sidebar: SidebarTopic[] = [];
      modules.forEach((m, mi) => {
        sidebar.push({
          label: `${m.title}:`,
          query: "",
          href: `#module-${mi + 1}`,
          icon: <Play className="h-5 w-5 shrink-0 text-white" />,
        });
        m.topics.forEach((t, ti) => {
          sidebar.push({
            label: `  Topic - ${ti + 1}: ${t}`,
            query: t,
            href: `#module-${mi + 1}-topic-${ti + 1}`,
            icon: <Play className="h-5 w-5 shrink-0 text-white" />,
          });
        });
      });

      setSidebarTopics(sidebar);
      setUploadingMode(false);
      setQuery("");
    } catch (err) {
      console.error("Failed to upload syllabus:", err);
      alert("Failed to upload syllabus. Ensure the file is text-based.");
    }
  };

  const defaultLinks: SidebarTopic[] = [
    {
      label: "Search All Topics",
      query: "",
      href: "#",
      icon: <Search className="h-5 w-5 shrink-0 text-white" />,
    },
  ];

  return (
    <div className="flex min-h-screen bg-gradient-to-tr from-orange-400 via-pink-500 to-pink-600 relative">
      {isLoading && <LoaderOverlay />}
      {/* Sidebar */}
      <div
        className="fixed top-0 right-0 h-full z-50"
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
      >
        <Sidebar open={open} setOpen={setOpen}>
          <SidebarBody className="bg-gradient-to-b from-black via-violet-800 to-blue-800 text-white justify-between gap-10">
            <div className="flex flex-1 flex-col overflow-x-hidden overflow-y-auto">
              <div className="mt-8 flex flex-col gap-2">
                {(sidebarTopics.length > 0 ? sidebarTopics : defaultLinks).map(
                  (topic, idx) => {
                    const handleSidebarLinkClick = (
                      e: React.MouseEvent<HTMLDivElement>
                    ) => {
                      e.preventDefault();
                      if (!topic.query || topic.query.trim() === "") return;
                      setQuery(topic.query);
                      handleSearch();
                    };
                    return (
                      <div
                        key={idx}
                        onClick={handleSidebarLinkClick}
                        style={{
                          cursor: topic.query ? "pointer" : "default",
                          paddingLeft: topic.label.startsWith("  ") ? 12 : 0,
                        }}
                        className="text-lg text-white hover:text-yellow-300 transition-colors"
                      >
                        <SidebarLink
                          link={{
                            label: topic.label,
                            href: topic.href,
                            icon: React.cloneElement(
                              topic.icon as React.ReactElement,
                              { className: "h-5 w-5 shrink-0 text-white" }
                            ),
                          }}
                        />
                      </div>
                    );
                  }
                )}
              </div>
            </div>
            <div>
              <SidebarLink
                link={{
                  label: userName || "User",
                  href: "#",
                  icon: <User className="h-7 w-7 text-white" />,
                }}
              />
            </div>
          </SidebarBody>
        </Sidebar>
      </div>
      {/* Main Content */}
      <main className="flex-1 mr-[80px] flex flex-col items-center w-full px-2 sm:px-0 relative z-10">
        <div className="w-full max-w-6xl mx-auto px-4 flex flex-col items-center">
          <h1 className="text-4xl font-bold mb-6 mt-8 text-white text-center">
            {/* Slightly reduced top margin for more space */}
            Start Learning with EduCurate, our Course Planner
          </h1>
          {uploadingMode ? (
            <div className="flex flex-col items-center gap-4 mt-4">
              <FileUpload onChange={handleFileUpload} />
              {files.length > 0 && (
                <button
                  onClick={handleDoneUploading}
                  className="bg-green-600 hover:bg-green-700 transition-colors text-white font-semibold text-lg px-6 py-2 rounded-full shadow"
                >
                  Done Uploading
                </button>
              )}
            </div>
          ) : (
            <>
              <div className="flex flex-row items-center gap-4 mt-6 mb-3 w-full max-w-3xl">
                <div className="flex items-center bg-white rounded-full shadow px-4 py-2 flex-grow min-w-0">
                  <Search className="text-gray-400 mr-2" size={24} />
                  <input
                    type="text"
                    placeholder="Search for any topic"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    className="bg-transparent outline-none text-gray-800 w-full text-lg min-w-0"
                  />
                </div>
                <button
                  onClick={handleSearch}
                  className="bg-blue-600 hover:bg-blue-700 transition-colors text-white font-semibold text-lg px-6 py-2 rounded-full shadow flex-shrink-0"
                >
                  Search
                </button>
                <button
                  onClick={() => setFiltersOpen(!filtersOpen)}
                  className="bg-pink-600 hover:bg-pink-700 transition-colors text-white font-semibold text-lg px-6 py-2 rounded-full shadow flex-shrink-0 flex items-center gap-2"
                >
                  <Filter size={20} />
                  Filters
                </button>
                <button
                  onClick={() => setUploadingMode(true)}
                  className="bg-yellow-500 hover:bg-yellow-600 transition-colors text-white font-semibold text-lg px-6 py-2 rounded-full shadow flex-shrink-0"
                >
                  Upload Syllabus
                </button>
              </div>
              <SearchFilters
                isOpen={filtersOpen}
                onClose={() => setFiltersOpen(false)}
                onFiltersChange={handleFiltersChange}
                filters={appliedFilters}
              />
              {/* Planned Schedule */}
              {roadmapSchedule.length > 0 && (
                <div
                  className="flex flex-col items-center mt-8 w-full max-w-4xl"
                  style={{ maxHeight: 360, overflowY: "auto" }} /* reduces height to fit more */
                >
                  <h2 className="text-2xl font-bold text-white mb-4">
                    {/* Reduced margin bottom */}
                    Planned Schedule
                  </h2>
                  <div className="w-full bg-white/10 p-3 rounded">
                    <ul className="space-y-2 text-white max-h-full overflow-y-auto">
                      {roadmapSchedule.map((r, idx) => (
                        <li
                          key={idx}
                          className="p-2 bg-white/5 rounded cursor-pointer transition hover:bg-pink-600/50"
                          onClick={() =>
                            handleScheduleCellClick(r.topic ?? r.label)
                          }
                        >
                          <div className="flex items-center justify-between">
                            <div>
                              <div className="font-semibold">
                                {r.topic ?? r.label}
                              </div>
                              <div className="text-sm text-white/70">
                                {r.summary ?? ""}
                              </div>
                            </div>
                            <div className="text-sm text-white/80">
                              {r.estimated_time ??
                                r.recommended_time ??
                                "N/A"}{" "}
                              min
                            </div>
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div className="mt-4 text-center text-sm text-white/80">
                    Click any schedule cell above to see recommended videos.
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}
