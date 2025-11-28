🚀 EduCurate — AI-Powered Personalized Learning Assistant
Next-Gen Adaptive Roadmap Generation • Intelligent Content Curation • Automated Evaluation System (AES)

EduCurate is an agentic AI-driven personalized learning assistant that creates student-specific topic roadmaps, recommends curated learning content, generates Bloom-taxonomy questions, and evaluates student answers using a knowledge-graph–based Auto Evaluation System (AES).

Built using Python FastAPI, PostgreSQL, Neo4j, WhisperX, Gemini LLMs, and Next.js, EduCurate aims to deliver truly adaptive learning tailored to each student’s understanding level, time availability, learning pace, and topic complexity.

🌟 Key Features
🔥 1. Personalized Learning Roadmap Generator

Extracts topics from syllabus PDFs / text

Analyzes difficulty, dependencies, and student’s available study time

Generates optimized, student-specific learning paths

Powered by Gemini LLM + rule-based reasoning

Achieved 98.3% roadmap accuracy vs. expert-created roadmaps

🎯 2. Content Curation Engine

Fetches high-quality learning materials such as:

YouTube videos (via YouTube Data API v3)

Lecture resources

Notes, summaries, and examples
Displayed inside the EduCurate UI for frictionless learning.

🧠 3. AES — Auto Evaluation System (Knowledge Graph–Based)

Evaluates written answers using semantic similarity + reasoning

Uses Neo4j-powered Knowledge Graphs for concept-level understanding

Generates adaptive feedback (weak areas, misconceptions, next steps)

Re-aligns the roadmap based on student performance

Achieved 95.7% evaluation alignment with expert assessors

📝 4. Bloom-Level Question Generator

Pipeline includes:

YouTube video download (yt-dlp)

Audio extraction (FFmpeg)

WhisperX ASR transcription

Gemini 2.5 Pro LLM for question generation

Produces exactly 5 Bloom’s taxonomy questions from lecture videos.

🎥 5. Lecture ASR Pipeline

Integrated audio pipeline:

Download → Extract Audio → Transcribe → Segment → Generate Questions
Robust for long videos with timestamped transcripts.

🖥 6. Full-Stack Web Application

Frontend:

Next.js

Modern UI components

Syllabus viewer sidebar

Learning roadmap viewer

Backend:

FastAPI

PostgreSQL

Neo4j

LLM-based modules

🏗 System Architecture
                ┌───────────────────────┐
                │      Next.js UI       │
                │ Syllabus Upload,       │
                │ Roadmap View,          │
                │ Video Search, Assess   │
                └───────────┬───────────┘
                            │
                            ▼
               ┌──────────────────────────┐
               │       FastAPI Backend    │
               │  - Roadmap Generator     │
               │  - Content Fetcher       │
               │  - ASR Pipeline (WhisperX)│
               │  - Bloom Question Gen     │
               │  - Auto Evaluation (AES)  │
               └──────────┬───────────────┘
                         │
        ┌────────────────┼───────────────────┐
        ▼                ▼                   ▼
┌──────────────┐  ┌───────────────┐   ┌────────────────┐
│ PostgreSQL    │  │ Neo4j KG       │   │ Gemini LLMs     │
│ User Data,    │  │ Concept Graphs │   │ Roadmap, QGen    │
│ Roadmaps,     │  │ Evaluator AES  │   │ Evaluation Logic │
└──────────────┘  └───────────────┘   └────────────────┘

🧩 Tech Stack
Backend

Python, FastAPI

WhisperX (ASR)

yt-dlp + FFmpeg

Gemini 2.5 Pro

Neo4j + Cypher

PostgreSQL

SQLAlchemy

Pydantic

Frontend

Next.js 14

TypeScript

React

ShadCN UI

Tailwind CSS

🧪 Performance Metrics
Component	Metric	Result
Roadmap Generator	Accuracy vs Experts	98.3%
AES Evaluator	Alignment with human evaluators	95.7%
ASR (WhisperX)	Avg WER	Low (~4–8%) depending on clarity
Video → Bloom Questions	Generation Latency	~3–7 seconds
📦 Installation Guide
1. Clone the Repo
git clone https://github.com/KishoreLOL21/EduCurate_Learning_Application.git
cd EduCurate_Learning_Application

2. Backend Setup
cd Backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

3. Environment Variables

Create a .env file:

GEMINI_API_KEY=your_key_here
POSTGRES_URL=postgresql://user:pass@localhost:5432/educurate
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

4. Start Backend
Treminal - 1: python server.py
Treminal - 2: uvicorn main:app --reload

🖥 Frontend Setup
cd Frontend
npm install
npm run dev

🧠 Key Modules
1. Roadmap Generator

Topic extraction

Time allocation

Complexity analysis

Sequential ordering

LLM refinement

2. AES (Knowledge Graph Evaluator)

Extracts key concepts from ideal answers

Builds a concept graph

Maps student answer nodes

Computes semantic + structural similarity

Generates feedback

3. ASR Pipeline

yt-dlp for downloading

ffmpeg for WAV conversion

WhisperX for ASR

Timestamped transcription

4. Bloom Question Generator

Fully automated

Structured 5-level output

Works with any transcript

📘 API Endpoints (Examples)
Method	Endpoint	Description
POST	/upload-syllabus	Extract topics
POST	/generate-roadmap	Create student-specific roadmap
POST	/evaluate-answer	AES evaluation
POST	/process-video	Run ASR + Bloom QGen
GET	/get-content?topic=	Fetch YouTube videos
🔜 Upcoming Features

Adaptive weekly pacing engine

Learning analytics dashboard

Student progress predictor (ML model)

Gamification layer (XP, badges, topic mastery)

🤝 Contributing

PRs are welcome!
Please open an issue before submitting major changes.

⭐ Support the Project

If you like EduCurate, consider giving the repo a star ⭐ on GitHub — it helps visibility!
