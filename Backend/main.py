import os
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import sys
import logging
import io
import asyncio
import uuid
import json
from concurrent.futures import ThreadPoolExecutor
import re

from fastapi import FastAPI, Depends, HTTPException, status, Query, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import bcrypt
import httpx
import pandas as pd
import networkx as nx
import PyPDF2
from docx import Document
from pydantic import BaseModel

import models
import schemas as S
from database import engine, SessionLocal
from utils import extract_modules_and_topics_structured
from models import TopicsViewed
from schemas import TopicsViewedCreate, TopicsViewedOut

from Question_Generation import transcript, bloom_from_transcript
from Question_Generation import updated_bloom_dynamic_questions as bloom

from Question_Generation import bloom_qg_bert_advanced
from Question_Generation import lecture_asr_pipeline_1

from RoadmapGeneration.ModelFineTune import RoadmapGenerator
from RoadmapGeneration.agents.topic_decomposer import topic_decomposer
from RoadmapGeneration.agents.prerequisite_inference import prerequisite_inference
from RoadmapGeneration.agents.difficulty_estimator import difficulty_estimator
from RoadmapGeneration.agents.validator_agent import validator_agent
from RoadmapGeneration.agents.personalizer_agent import personalizer_agent
from RoadmapGeneration.agents.topic_decomposer import GeminiRoadmapAgent

from auto_eval_client import AutoEvalClient

AUTO_EVAL_BASE_URL = os.getenv("AUTO_EVAL_BASE_URL", "http://localhost:8001")

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Personalized Learning Assistant API", version="1.0")

# Database setup
models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ENVIRONMENT CONFIGURATION
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
HF_ROADMAP_MODEL_PATH = os.getenv("HF_ROADMAP_MODEL_PATH")

if not YOUTUBE_API_KEY:
    logger.warning("⚠️ YOUTUBE_API_KEY not found in environment. YouTube searches will fail.")
if not GEMINI_API_KEY:
    logger.warning("⚠️ GEMINI_API_KEY not found in environment. Gemini roadmap generation may fail.")

# Gemini setup
try:
    import google.generativeai as genai
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.5-flash")
    else:
        model = None
except Exception as e:
    logger.warning("⚠️ google.generativeai import/config failed: %s", e)
    model = None

# INITIALIZE ROADMAP GENERATOR ON STARTUP

@app.on_event("startup")        
async def init_roadmap_gen():
    """Initialize roadmap generator on server startup."""
    try:
        app.state.roadmap_gen = RoadmapGenerator(
            hf_model_path=HF_ROADMAP_MODEL_PATH,
            llm_client=model
        )
        logger.info("✅ RoadmapGenerator initialized successfully.")
    except Exception as e:
        logger.exception("❌ Failed to initialize RoadmapGenerator: %s", e)
        app.state.roadmap_gen = None

# AUTHENTICATION ENDPOINTS

@app.post("/sign-up")
def sign_up(request: S.User, db: Session = Depends(get_db)):
    existing_user = db.query(models.User_Info).filter(models.User_Info.userName == request.userName).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists.")
    hashed_pw = bcrypt.hashpw(request.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user = models.User_Info(
        firstName=request.firstName,
        lastName=request.lastName,
        email=request.email,
        phoneNo=request.phoneNo,
        countryCode=request.countryCode,
        userName=request.userName,
        password=hashed_pw
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "User Info Saved", "user_id": user.user_id}

@app.post("/login")
def login(request: S.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User_Info).filter(models.User_Info.userName == request.userName).first()
    if not user:
        raise HTTPException(status_code=404, detail="User does not exist.")
    
    # Check password
    if not bcrypt.checkpw(request.password.encode("utf-8"), user.password.encode("utf-8")):
        raise HTTPException(status_code=401, detail="Incorrect password.")
    
    # Log login time
    login_log = models.Login_Info(user_id=user.user_id, login_time=datetime.utcnow())
    db.add(login_log)
    db.commit()

    return {
        "message": "Login successful",
        "user_id": user.user_id,
        "login_time": login_log.login_time.isoformat()
    }

@app.get("/user-info/{user_id}")
def get_user_info(user_id: int, db: Session = Depends(get_db)):
    user_info = db.query(models.User_Info).filter(models.User_Info.user_id == user_id).first()
    if not user_info:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "user_id": user_info.user_id,
        "userName": user_info.userName,
        "firstName": user_info.firstName,
        "lastName": user_info.lastName,
        "email": user_info.email
    }

# ----------------------------------------------------------------------
# PASSWORD RESET ENDPOINTS
# ----------------------------------------------------------------------
reset_tokens = {}

@app.post("/forgot-password")
async def forgot_password(request: S.ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(models.User_Info).filter(models.User_Info.email == request.userName).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email not found.")
    token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    expires_at = datetime.utcnow() + timedelta(hours=1)
    reset_tokens[token] = {"user_id": user.user_id, "expires_at": expires_at}
    reset_link = f"http://localhost:3000/reset-password?token={token}"
    logger.info(f"🔗 Reset link: {reset_link} (expires {expires_at})")
    return {"message": "Password reset link generated."}

@app.post("/reset-password")
async def reset_password():
    raise HTTPException(status_code=501, detail="Reset flow not implemented in this demo.")

# Agentic AI Roadmap Generation Endpoint
@app.post("/generate-roadmap/", response_model=dict)
async def generate_roadmap(payload: dict, db: Session = Depends(get_db)):
    """
    Main Agentic AI roadmap generation pipeline.
    Uses Gemini-powered Perception and multi-agent reasoning to build a personalized roadmap.
    """
    try:
        user = payload.get("userName")
        main_topic = payload.get("query", "").strip()
        if not main_topic:
            raise HTTPException(status_code=400, detail="Missing 'query' field (main topic).")

        # --- Step 1: Fetch any existing user-topic data ---
        topic_row = db.query(TopicsViewed).filter_by(userName=user, topic=main_topic).first()
        db_subtopics = []
        if topic_row and topic_row.sub_topics:
            db_subtopics = [s.strip() for s in topic_row.sub_topics.split(",") if s.strip()]

        # --- Step 2: Initialize Gemini agent (Perception stage) ---
        gemini_agent = GeminiRoadmapAgent(gemini_client=model)

        # --- Step 3: Generate topic-specific subtopics (Perception) ---
        nodes = gemini_agent.generate_subtopics(main_topic)

        roadmap_subtopics = [n["label"] for n in nodes]
        all_subtopics = sorted(set(db_subtopics + roadmap_subtopics))

        # --- Step 4: Sync DB ---
        if topic_row:
            topic_row.sub_topics = ", ".join(all_subtopics)
            db.commit()
            db.refresh(topic_row)
        else:
            new_topic = TopicsViewed(
                userName=user,
                topic=main_topic,
                sub_topics=", ".join(roadmap_subtopics),
                videos_viewed=0,
                questions_answered=0
            )
            db.add(new_topic)
            db.commit()
            db.refresh(new_topic)

        # --- Step 5: Reasoning Stage (Build knowledge DAG) ---
        nodes_input = []
        for i, n in enumerate(nodes):
            nodes_input.append({
                "id": str(i),
                "label": n.get("label", f"Section {i+1}"),
                "summary": n.get("summary", "Auto-generated summary."),
                "keywords": n.get("keywords", []),
                "dependencies": n.get("dependencies", []),
                "sources": n.get("sources", []),
                "embedding": n.get("embedding", [])
            })

        G = prerequisite_inference(nodes_input)

        # --- Step 6: Action Stage (Difficulty + Personalization) ---
        G = difficulty_estimator(G)
        G, issues = validator_agent(G, payload.get("original_keywords", []))

        user_model = payload.get("user_model", {}) or {}
        time_budget = payload.get("time_budget", 0)
        schedule = personalizer_agent(G, user_model, time_budget)

        # --- Step 7: Return results ---
        return {
            "query": main_topic,
            "schedule": schedule,
            "issues": issues,
            "node_count": len(nodes),
            "edge_count": len(G.edges)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("❌ Roadmap generation failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Roadmap generation error: {e}")

# Youtube Search
@app.get("/search")
async def search_videos(q: str = Query(..., description="Search query / topic")):
    """Generate roadmap for topic + fetch YouTube videos. Uses only fine-tuned/LLM-based chain or just the query."""
    if not YOUTUBE_API_KEY:
        raise HTTPException(status_code=500, detail="YOUTUBE_API_KEY not configured on server.")

    roadmap_gen: RoadmapGenerator = getattr(app.state, "roadmap_gen", None)
    try:
        roadmap_list = roadmap_gen.generate_roadmap(q) if roadmap_gen else [q]
    except Exception as e:
        logger.exception("Roadmap generation failed: %s", e)
        roadmap_list = [q]

    async with httpx.AsyncClient(timeout=15.0) as client:
        yt_response = await client.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                "part": "snippet",
                "q": q,
                "type": "video",
                "key": YOUTUBE_API_KEY,
                "maxResults": 10,
            },
        )

    if yt_response.status_code != 200:
        try:
            err_json = yt_response.json()
            message = err_json.get("error", {}).get("message", yt_response.text)
        except Exception:
            message = yt_response.text
        raise HTTPException(status_code=yt_response.status_code, detail=f"YouTube API error: {message}")

    items = yt_response.json().get("items", [])
    return {"items": items, "roadmap": roadmap_list}

@app.post("/topics-viewed", response_model=TopicsViewedOut)
def record_topics_viewed(
    data: TopicsViewedCreate,
    db: Session = Depends(get_db)
):
    topic_obj = TopicsViewed(
        userName=data.userName,
        topic=data.topic,
        sub_topics=data.sub_topics,
        videos_viewed=data.videos_viewed,
        questions_answered=data.questions_answered
    )
    db.add(topic_obj)
    db.commit()
    db.refresh(topic_obj)
    return topic_obj

# Roadmap finetune
from RoadmapGeneration.ModelFineTune import train_roadmap_model

class TrainRequest(BaseModel):
    train_jsonl_path: str
    output_dir: str
    base_model: Optional[str] = "t5-small"
    epochs: Optional[int] = 3
    batch_size: Optional[int] = 8
    use_lora: Optional[bool] = True

@app.post("/train-roadmap-model")
def train_endpoint(req: TrainRequest):
    """Trigger fine-tuning of roadmap model (dev use only)."""
    try:
        out = train_roadmap_model(
            train_jsonl_path=req.train_jsonl_path,
            output_dir=req.output_dir,
            base_model=req.base_model,
            epochs=req.epochs,
            batch_size=req.batch_size,
            use_lora=req.use_lora,
        )
        app.state.roadmap_gen = RoadmapGenerator(hf_model_path=out, llm_client=model)
        return {"status": "ok", "model_saved_to": out}
    except Exception as e:
        logger.exception("Training failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

# Syllabus Upload
@app.post("/upload-syllabus")
async def upload_syllabus(file: UploadFile = File(...)):
    """Upload and extract module/topic structure from PDF or DOCX."""
    contents = await file.read()
    filename = (file.filename or "").lower()
    text = ""
    if filename.endswith(".pdf"):
        reader = PyPDF2.PdfReader(io.BytesIO(contents))
        text = "\n".join([page.extract_text() or "" for page in reader.pages])
    elif filename.endswith(".docx"):
        doc = Document(io.BytesIO(contents))
        text = "\n".join([para.text for para in doc.paragraphs])
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type. Use .pdf or .docx")
    if not text.strip():
        raise HTTPException(status_code=400, detail="No readable text found in file. Ensure it's selectable text.")
    pretty, modules = extract_modules_and_topics_structured(text)
    return {"module_structure": pretty, "modules": modules}


logger = logging.getLogger("uvicorn.error")

# Use a single global executor for CPU-bound tasks
executor = ThreadPoolExecutor(max_workers=2)

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("question_gen")

executor = ThreadPoolExecutor(max_workers=2)

# Create jobs directory
os.makedirs("jobs", exist_ok=True)

def clean_question(text: str) -> str:
    """
    Cleans malformed questions generated by the model.
    Examples:
      Input: "What does Generate 2 remembering: recall key facts and definitions questions from this text?"
      Output: "recall key facts and definitions questions from this text?"
    """
    if not text:
        return text

    # Normalize whitespace and punctuation
    text = re.sub(r"\s+", " ", text).strip()

    # Remove “Generate X ...” prefixes
    text = re.sub(r"(?i)generate\s*\d*\s*(remembering|understanding|applying|analyzing|evaluating|creating)\s*:\s*", "", text)

    # Remove “What does ... questions from this text” style wrappers
    match = re.search(r"(recall|explain|use|identify|make|generate)[^?]*\?", text)
    if match:
        text = match.group(0)

    # Capitalize first letter
    text = text[0].upper() + text[1:] if text else text
    return text.strip()


def save_job_status(job_id: str, status: str, message: str = "", questions=None):
    """Save job progress and result."""
    job_path = f"jobs/{job_id}.json"
    data = {
        "job_id": job_id,
        "status": status,
        "message": message,
        "questions": questions or []
    }
    with open(job_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def run_pipeline(video_url: str, job_id: str, num_qs: int):
    """Background task: run full ASR + T5 pipeline and read bloom_questions_unique.txt."""
    try:
        save_job_status(job_id, "processing", "Starting ASR and question generation pipeline...")
        logger.info(f"[Job {job_id}] Starting ASR+Gemini for {video_url}")

        # Run ASR + Gemini pipeline
        lecture_asr_pipeline_1.process_video(video_url)

        # Run local T5 model (creates bloom_questions_unique.txt)
        logger.info(f"[Job {job_id}] Running local T5 generator.")
        bloom_qg_bert_advanced.main()

        # --- Read and parse from bloom_questions_unique.txt ---
        questions = []
        file_path = "bloom_questions_unique.txt"

        if not os.path.exists(file_path):
            raise FileNotFoundError("bloom_questions_unique.txt not found after pipeline execution.")

        logger.info(f"[Job {job_id}] Reading {file_path} ...")

        with open(file_path, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f.readlines() if ln.strip()]

        current_level = None
        for ln in lines:
            if ln.startswith("🟢"):
                # Example: 🟢 Remembering: recall key facts and definitions
                current_level = ln.replace("🟢", "").strip()
            elif ln.startswith("Q"):
                parts = ln.split(":", 1)
                question_text = parts[1].strip() if len(parts) > 1 else ln.strip()
                cleaned_q = clean_question(question_text)
                questions.append({
                    "source": "t5",
                    "level": current_level or "Unknown",
                    "question": cleaned_q
                })

        # Limit number of questions
        if num_qs and len(questions) > num_qs:
            questions = questions[:num_qs]

        save_job_status(job_id, "completed", "Question generation complete.", questions)
        logger.info(f"[Job {job_id}] ✅ Cleaned and saved {len(questions)} questions.")

    except Exception as e:
        logger.exception(f"[Job {job_id}] Failed: {e}")
        save_job_status(job_id, "error", str(e), [])




@app.get("/generate-questions")
async def generate_questions(
    background_tasks: BackgroundTasks,
    video_url: str = Query(..., description="YouTube video URL to process"),
    num_qs: int = Query(10, ge=1, le=20, description="Number of questions to return (max 20)")
):
    """
    Starts async Bloom Question Generation.
    Reads final questions from bloom_questions_unique.txt once done.
    """
    job_id = str(uuid.uuid4())
    save_job_status(job_id, "queued", "Job queued for processing.")
    background_tasks.add_task(run_pipeline, video_url, job_id, num_qs)

    return JSONResponse({
        "status": "queued",
        "message": "Job started successfully.",
        "job_id": job_id
    })


@app.get("/status/{job_id}")
async def get_status(job_id: str):
    """Poll the current job status or get final questions."""
    job_path = f"jobs/{job_id}.json"
    if not os.path.exists(job_path):
        raise HTTPException(status_code=404, detail="Job not found.")

    with open(job_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # If completed but bloom_questions_unique.txt still exists, ensure consistency
    if data.get("status") == "completed" and not data.get("questions"):
        file_path = "bloom_questions_unique.txt"
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                lines = [ln.strip() for ln in f.readlines() if ln.strip()]
            current_level = None
            questions = []
            for ln in lines:
                if ln.startswith("🟢"):
                    current_level = ln.replace("🟢", "").strip()
                elif ln.startswith("Q"):
                    parts = ln.split(":", 1)
                    question_text = parts[1].strip() if len(parts) > 1 else ln.strip()
                    questions.append({
                        "source": "t5",
                        "level": current_level or "Unknown",
                        "question": question_text
                    })
            data["questions"] = questions

    return JSONResponse(content=data)

@app.post("/submit-answer", response_model=S.SubmitAnswerOut)
def submit_answer(payload: S.SubmitAnswerCreate, db: Session = Depends(get_db)):
    """
    Save user answer into test_answers table.
    Payload: { user_name, topic, question, answer }
    """
    # Optional: basic validation
    if not payload.user_name or not payload.question or not payload.answer:
        raise HTTPException(status_code=400, detail="user_name, question and answer are required.")
    try:
        ta = models.TestAnswer(
            user_name=payload.user_name,
            topic=payload.topic or "",
            question=payload.question,
            answer=payload.answer
        )
        db.add(ta)
        db.commit()
        db.refresh(ta)
        return ta
    except Exception as e:
        db.rollback()
        logger.exception("Failed saving user answer: %s", e)
        raise HTTPException(status_code=500, detail="Failed to save answer.")
    
# Add to main.py after your existing endpoints

@app.post("/evaluate-answer")
async def evaluate_answer(
    question: str, 
    answer: str, 
    top_k: int = 5,
    db: Session = Depends(get_db)
):
    """
    Evaluate a single answer using Auto-Eval pipeline
    """
    try:
        async with AutoEvalClient(AUTO_EVAL_BASE_URL) as client:
            result = await client.evaluate_answer(question, answer, top_k)
            
        return {
            "question": question,
            "answer": answer,
            "evaluation": result
        }
    except Exception as e:
        logger.exception(f"Evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

# Add this function to main.py before your endpoints
def simple_evaluation_fallback(question: str, answer: str) -> Dict[str, Any]:
    """Simple fallback evaluation when Auto-Eval is not available"""
    # Basic keyword-based scoring as fallback
    question_lower = question.lower()
    answer_lower = answer.lower()
    
    score = 50  # Base score
    
    # Simple keyword matching logic
    important_keywords = []
    if "what" in question_lower:
        important_keywords = ["is", "are", "the", "define", "explain"]
    elif "how" in question_lower:
        important_keywords = ["process", "work", "method", "step"]
    elif "why" in question_lower:
        important_keywords = ["because", "reason", "purpose", "cause"]
    
    # Count matching keywords
    matches = sum(1 for keyword in important_keywords if keyword in answer_lower)
    if matches > 0:
        score = min(100, 50 + (matches * 10))
    
    # Length-based adjustment
    answer_length = len(answer.split())
    if answer_length < 5:
        score = max(0, score - 20)
    elif answer_length > 20:
        score = min(100, score + 10)
    
    return {
        "grade": score,
        "feedback": f"Basic evaluation: Answer contains relevant keywords. Score based on content relevance and length.",
        "confidence": 0.7,
        "model_answer": "Auto-Eval service not available for detailed model answer.",
        "rubric": "Basic keyword and length-based evaluation",
        "source_ids": []
    }

# Then update your evaluate_answers endpoint to use the fallback:
@app.post("/evaluate-answers")
async def evaluate_answers(
    user_name: str, 
    topic: str, 
    db: Session = Depends(get_db)
):
    """
    Alias endpoint for frontend compatibility
    """
    try:
        # Get user answers from database
        answers = db.query(models.TestAnswer).filter_by(user_name=user_name, topic=topic).all()
        if not answers:
            raise HTTPException(status_code=404, detail="No answers found for this user/topic.")

        results = []
        
        # Try Auto-Eval first, fallback to simple evaluation
        try:
            async with AutoEvalClient(AUTO_EVAL_BASE_URL) as client:
                for ans in answers:
                    evaluation = await client.evaluate_answer(ans.question, ans.answer)
                    results.append({
                        "question": ans.question,
                        "answer": ans.answer,
                        "score": evaluation.get("grade", 0),
                        "feedback": evaluation.get("feedback", ""),
                        "confidence": evaluation.get("confidence", 0.0),
                        "model_answer": evaluation.get("model_answer", ""),
                        "rubric": evaluation.get("rubric", "")
                    })
        except Exception as auto_eval_error:
            logger.warning(f"Auto-Eval failed, using fallback: {auto_eval_error}")
            for ans in answers:
                evaluation = simple_evaluation_fallback(ans.question, ans.answer)
                results.append({
                    "question": ans.question,
                    "answer": ans.answer,
                    "score": evaluation.get("grade", 0),
                    "feedback": evaluation.get("feedback", ""),
                    "confidence": evaluation.get("confidence", 0.0),
                    "model_answer": evaluation.get("model_answer", ""),
                    "rubric": evaluation.get("rubric", "")
                })

        avg_score = sum(r["score"] for r in results) / len(results) if results else 0
        return {
            "user_name": user_name,
            "topic": topic,
            "results": results,
            "average_score": round(avg_score, 2),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Batch evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch evaluation failed: {str(e)}")
    
@app.post("/grade-answer-with-context")
async def grade_answer_with_context(
    question: str,
    answer: str,
    context: str = "",
    db: Session = Depends(get_db)
):
    """
    Grade an answer with additional context using Auto-Eval
    """
    try:
        async with AutoEvalClient(AUTO_EVAL_BASE_URL) as client:
            result = await client.grade_answer(question, answer, context)
            
        return {
            "question": question,
            "answer": answer,
            "context": context,
            "grading_result": result
        }
    except Exception as e:
        logger.exception(f"Grading with context failed: {e}")
        raise HTTPException(status_code=500, detail=f"Grading failed: {str(e)}")
    
@app.on_event("startup")
async def startup_event():
    """Initialize services on server startup."""
    # Your existing roadmap generator initialization
    try:
        app.state.roadmap_gen = RoadmapGenerator(
            hf_model_path=HF_ROADMAP_MODEL_PATH,
            llm_client=model
        )
        logger.info("✅ RoadmapGenerator initialized successfully.")
    except Exception as e:
        logger.exception("❌ Failed to initialize RoadmapGenerator: %s", e)
        app.state.roadmap_gen = None
    
    # Check Auto-Eval service availability
    try:
        async with AutoEvalClient(AUTO_EVAL_BASE_URL) as client:
            # Simple health check
            await client.client.get("/docs")
        logger.info("✅ Auto-Eval service is available.")
    except Exception as e:
        logger.warning("⚠️ Auto-Eval service is not available: %s", e)