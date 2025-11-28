# 🚀 EduCurate — AI-Powered Personalized Learning Assistant

**Next-Gen Adaptive Roadmap Generation • Intelligent Content Curation • Automated Evaluation System (AES)**

EduCurate is an agentic AI-driven personalized learning assistant that creates student-specific topic roadmaps, recommends curated learning content, generates Bloom-taxonomy questions, and evaluates student answers using a knowledge-graph–based Auto Evaluation System (AES).

Built using Python FastAPI, PostgreSQL, Neo4j, WhisperX, Gemini LLMs, and Next.js, EduCurate aims to deliver truly adaptive learning tailored to each student's understanding level, time availability, learning pace, and topic complexity.

---

## 🌟 Key Features

### 🔥 1. Personalized Learning Roadmap Generator

- Extracts topics from syllabus PDFs / text
- Analyzes difficulty, dependencies, and student's available study time
- Generates optimized, student-specific learning paths
- Powered by Gemini LLM + rule-based reasoning
- **Achieved 98.3% roadmap accuracy vs. expert-created roadmaps**

### 🎯 2. Content Curation Engine

- Fetches high-quality learning materials such as:
  - YouTube videos (via YouTube Data API v3)
  - Lecture resources
  - Notes, summaries, and examples
- Displayed inside the EduCurate UI for frictionless learning

### 🧠 3. AES — Auto Evaluation System (Knowledge Graph–Based)

- Evaluates written answers using semantic similarity + reasoning
- Uses Neo4j-powered Knowledge Graphs for concept-level understanding
- Generates adaptive feedback (weak areas, misconceptions, next steps)
- Re-aligns the roadmap based on student performance
- **Achieved 95.7% evaluation alignment with expert assessors**

### 📝 4. Bloom-Level Question Generator

Pipeline includes:

- YouTube video download (yt-dlp)
- Audio extraction (FFmpeg)
- WhisperX ASR transcription
- Gemini 2.5 Pro LLM for question generation

Produces exactly 5 Bloom's taxonomy questions from lecture videos.

### 🎥 5. Lecture ASR Pipeline

- Integrated audio pipeline:
  - Download → Extract Audio → Transcribe → Segment → Generate Questions
- Robust for long videos with timestamped transcripts

### 🖥 6. Full-Stack Web Application

**Frontend:**
- Next.js 14 with TypeScript
- Modern UI components (ShadCN UI)
- Syllabus viewer sidebar
- Learning roadmap viewer
- Interactive video player

**Backend:**
- FastAPI REST API
- PostgreSQL for user data and roadmaps
- Neo4j for knowledge graphs
- LLM-based modules

---

## 🏗 System Architecture

```
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
┌──────────┼───────────────────┐
▼          ▼                   ▼
┌──────────────┐  ┌───────────────┐   ┌────────────────┐
│ PostgreSQL    │  │ Neo4j KG       │   │ Gemini LLMs     │
│ User Data,    │  │ Concept Graphs │   │ Roadmap, QGen    │
│ Roadmaps,     │  │ Evaluator AES  │   │ Evaluation Logic │
└──────────────┘  └───────────────┘   └────────────────┘
```

---

## 🧩 Tech Stack

### Backend

- **Language:** Python 3.8+
- **Framework:** FastAPI
- **ASR:** WhisperX
- **Video Processing:** yt-dlp + FFmpeg
- **LLM:** Gemini 2.5 Pro / Flash
- **Graph Database:** Neo4j + Cypher
- **Relational Database:** PostgreSQL
- **ORM:** SQLAlchemy
- **Validation:** Pydantic

### Frontend

- **Framework:** Next.js 14
- **Language:** TypeScript
- **UI Library:** React 18
- **Components:** ShadCN UI
- **Styling:** Tailwind CSS
- **3D Graphics:** Three.js, React Three Fiber

---

## 🧪 Performance Metrics

| Component | Metric | Result |
|-----------|--------|--------|
| Roadmap Generator | Accuracy vs Experts | 98.3% |
| AES Evaluator | Alignment with human evaluators | 95.7% |
| ASR (WhisperX) | Avg WER | Low (~4–8%) depending on clarity |
| Video → Bloom Questions | Generation Latency | ~3–7 seconds |

---

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Python** 3.8 or higher
- **Node.js** 18+ and npm/yarn
- **PostgreSQL** 12+ (running locally or remote)
- **Neo4j** 4.0+ (running locally or remote)
- **FFmpeg** (for audio processing)
- **Git**

### API Keys Required

- **Google Gemini API Key** - Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **YouTube Data API v3 Key** - Get from [Google Cloud Console](https://console.cloud.google.com/)
- (Optional) **OpenAI API Key** - For Auto-Eval fallback

---

## 📦 Installation Guide

### 1. Clone the Repository

```bash
git clone https://github.com/KishoreLOL21/EduCurate_Learning_Application.git
cd EduCurate_Learning_Application
```

### 2. Backend Setup

```bash
cd Backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Note:** If you encounter issues with `ffmpeg`, install it separately:
- **Windows:** Download from [ffmpeg.org](https://ffmpeg.org/download.html) or use `choco install ffmpeg`
- **macOS:** `brew install ffmpeg`
- **Linux:** `sudo apt-get install ffmpeg` or `sudo yum install ffmpeg`

### 3. Database Setup

#### PostgreSQL Setup

1. Create a new database:
```sql
CREATE DATABASE educurate;
```

2. The application will automatically create tables on first run.

3. Update database connection in `Backend/database.py` or use environment variable:
```python
# Default (update this in database.py):
# postgresql://postgres:password@localhost:5432/educurate
```

#### Neo4j Setup

1. Download and install Neo4j from [neo4j.com](https://neo4j.com/download/)
2. Start Neo4j Desktop or Neo4j Server
3. Create a new database (default: `neo4j`)
4. Note your connection credentials

### 4. Environment Variables

Create a `.env` file in the `Backend` directory:

```env
# Google APIs
GEMINI_API_KEY=your_gemini_api_key_here
YOUTUBE_API_KEY=your_youtube_api_key_here

# Database
POSTGRES_URL=postgresql://postgres:password@localhost:5432/educurate
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password

# Auto-Eval Service (optional)
AUTO_EVAL_BASE_URL=http://localhost:8001
GOOGLE_API_KEY=your_gemini_api_key_here

# Optional: HuggingFace Model Path
HF_ROADMAP_MODEL_PATH=/path/to/model
```

### 5. Start Backend Services

You need to run multiple services:

**Terminal 1 - Auto-Eval Server (optional):**
```bash
cd Backend/Auto_Eval
python run_server.py
# Or: uvicorn server:app --reload --port 8001
```

**Terminal 2 - Main FastAPI Server:**
```bash
cd Backend
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`
API documentation: `http://localhost:8000/docs`

### 6. Frontend Setup

```bash
cd Frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

---

## 🧠 Key Modules

### 1. Roadmap Generator

- Topic extraction
- Time allocation
- Complexity analysis
- Sequential ordering
- LLM refinement

### 2. AES (Knowledge Graph Evaluator)

- Extracts key concepts from ideal answers
- Builds a concept graph
- Maps student answer nodes
- Computes semantic + structural similarity
- Generates feedback

### 3. ASR Pipeline

- yt-dlp for downloading
- ffmpeg for WAV conversion
- WhisperX for ASR
- Timestamped transcription

### 4. Bloom Question Generator

- Fully automated
- Structured 5-level output
- Works with any transcript

---

## 📘 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/sign-up` | User registration |
| POST | `/login` | User authentication |
| POST | `/upload-syllabus` | Extract topics from PDF/DOCX |
| POST | `/generate-roadmap/` | Create student-specific roadmap |
| GET | `/search?q={topic}` | Search YouTube videos for topic |
| GET | `/generate-questions?video_url={url}` | Generate Bloom questions from video |
| GET | `/status/{job_id}` | Check question generation status |
| POST | `/submit-answer` | Save student answer |
| POST | `/evaluate-answer` | Evaluate answer using AES |
| POST | `/evaluate-answers` | Batch evaluate answers |
| GET | `/user-info/{user_id}` | Get user information |

For detailed API documentation, visit `http://localhost:8000/docs` when the server is running.

---

## 🔧 Troubleshooting

### Backend Issues

**Issue: Module not found errors**
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt` again

**Issue: Database connection errors**
- Verify PostgreSQL is running: `pg_isready` or check service status
- Check connection string in `database.py` or `.env`
- Ensure database exists: `psql -l | grep educurate`

**Issue: Neo4j connection errors**
- Verify Neo4j is running (check Neo4j Desktop or service)
- Test connection: `cypher-shell -u neo4j -p password`
- Update `NEO4J_URI` and credentials in `.env`

**Issue: FFmpeg not found**
- Install FFmpeg and ensure it's in PATH
- Test: `ffmpeg -version`

**Issue: WhisperX/ASR errors**
- Ensure CUDA is set up if using GPU (optional)
- Check audio file permissions and format

### Frontend Issues

**Issue: npm install fails**
- Clear cache: `npm cache clean --force`
- Delete `node_modules` and `package-lock.json`, then reinstall
- Try using yarn: `yarn install`

**Issue: Port 3000 already in use**
- Change port: `npm run dev -- -p 3001`
- Or kill process using port 3000

**Issue: API connection errors**
- Verify backend is running on `http://localhost:8000`
- Check CORS settings in `main.py`
- Verify API endpoints in browser console

### General Issues

**Issue: Missing API keys**
- Check `.env` file exists and has correct keys
- Verify keys are valid and not expired
- Check logs for specific error messages

**Issue: Auto-Eval service not available**
- This is optional - the app will use fallback evaluation
- To enable: Start Auto-Eval server on port 8001
- Check `AUTO_EVAL_BASE_URL` in `.env`

---

## 🔜 Upcoming Features

- Adaptive weekly pacing engine
- Learning analytics dashboard
- Student progress predictor (ML model)
- Gamification layer (XP, badges, topic mastery)
- Multi-language support
- Mobile app (React Native)

---

## 📁 Project Structure

```
Personalised-Learning-Assistant-main/
├── Backend/
│   ├── main.py                 # FastAPI application
│   ├── database.py             # Database configuration
│   ├── models.py               # SQLAlchemy models
│   ├── schemas.py              # Pydantic schemas
│   ├── requirements.txt        # Python dependencies
│   ├── Question_Generation/    # ASR and question generation
│   ├── RoadmapGeneration/      # Roadmap generation agents
│   ├── Auto_Eval/              # Auto Evaluation System
│   ├── routes/                 # API route handlers
│   └── jobs/                   # Background job storage
├── Frontend/
│   ├── app/                    # Next.js app directory
│   ├── components/             # React components
│   ├── lib/                    # Utility functions
│   ├── types/                  # TypeScript types
│   ├── package.json            # Node dependencies
│   └── public/                 # Static assets
└── README.md                   # This file
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

**Before submitting:**
- Ensure all tests pass (if available)
- Update documentation as needed
- Follow existing code style
- Open an issue for major changes before submitting

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## ⭐ Support the Project

If you like EduCurate, consider giving the repo a star ⭐ on GitHub — it helps visibility!

---

## 👥 Authors

- **KishoreLOL21** - [GitHub](https://github.com/KishoreLOL21)

---

## 🙏 Acknowledgments

- Google Gemini Team for the powerful LLM APIs
- WhisperX developers for excellent ASR capabilities
- Next.js and FastAPI communities for amazing frameworks
- All contributors and testers

---

## 📞 Contact & Support

For questions, issues, or feature requests:
- Open an issue on [GitHub Issues](https://github.com/KishoreLOL21/EduCurate_Learning_Application/issues)
- Check the documentation at `/docs` endpoint when server is running

---

**Made with ❤️ for personalized learning**
