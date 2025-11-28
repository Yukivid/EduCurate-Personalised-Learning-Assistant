from ..core.types import Evaluation
import os

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except Exception:
    ChatGoogleGenerativeAI = None

try:
    from langchain_openai import ChatOpenAI
except Exception:
    ChatOpenAI = None


EVAL_SYSTEM = (
    "You are a strict grader. Use the rubric and context to grade the student's answer against the model answer. "
    "Return ONLY valid JSON with numeric scores."
)


class EvaluatorAgent:
    def __init__(self, model: str | None = None, temperature: float = 0.0):
        # Default to Gemini 2.5 Flash
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.llm = None
        
        # Try Gemini first
        if ChatGoogleGenerativeAI is not None:
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model=self.model,
                    temperature=temperature
                )
                print(f"[INFO] Evaluator using: {self.model}")
            except Exception as e:
                print(f"[WARN] Gemini init failed in Evaluator: {e}")
                self.llm = None
        
        # Fallback to OpenAI
        if self.llm is None and ChatOpenAI is not None:
            try:
                openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                self.llm = ChatOpenAI(model=openai_model, temperature=temperature)
                print(f"[INFO] Evaluator using OpenAI fallback: {openai_model}")
            except Exception as e:
                print(f"[WARN] OpenAI init failed in Evaluator: {e}")
                self.llm = None

    def evaluate(self, question: str, student_answer: str, model_answer: str, rubric_text: str, context: str) -> Evaluation:
        if not self.llm:
            # Offline fallback: naive keyword overlap
            base = 0.0
            if model_answer and student_answer:
                overlap = len(set(student_answer.lower().split()) & set(model_answer.lower().split()))
                total = max(1, len(set(model_answer.lower().split())))
                base = min(1.0, overlap / total)
            feedback = "Heuristic overlap-based score (LLM unavailable)."
            return Evaluation(score=round(base * 100, 1), feedback=feedback, evidence_ids=[], confidence=0.3)
        
        messages = [
            ("system", EVAL_SYSTEM),
            (
                "user",
                "Grade on a 0-100 scale. Return ONLY valid JSON with these exact keys:\n"
                "{\n"
                '  "score": <number between 0-100>,\n'
                '  "feedback": "<string with explanation>",\n'
                '  "evidence_ids": [],\n'
                '  "confidence": <number between 0.0-1.0>\n'
                "}\n\n"
                "IMPORTANT: score and confidence must be numbers, not strings.\n\n"
                f"Question:\n{question}\n\nRubric:\n{rubric_text}\n\nModel Answer:\n{model_answer}\n\n"
                f"Student Answer:\n{student_answer}\n\nContext:\n{context}\n",
            ),
        ]
        
        try:
            res = self.llm.invoke(messages)
            import json
            import re
            
            content = getattr(res, "content", "{}")
            
            # Remove markdown code blocks if present
            content = re.sub(r'^```json\s*', '', content)
            content = re.sub(r'^```\s*', '', content)
            content = re.sub(r'\s*```$', '', content)
            content = content.strip()
            
            data = json.loads(content)
            
            # Robust score parsing
            score = data.get("score", 0)
            if isinstance(score, str):
                # Try to extract number from string like "high" or "85/100"
                score_match = re.search(r'\d+\.?\d*', str(score))
                if score_match:
                    score = float(score_match.group())
                else:
                    # Map text to numbers
                    score_map = {
                        'low': 30, 'medium': 60, 'high': 85,
                        'poor': 25, 'fair': 50, 'good': 75, 'excellent': 95,
                        'very low': 15, 'very high': 95
                    }
                    score = score_map.get(str(score).lower(), 50)
            score = max(0.0, min(100.0, float(score)))
            
            # Robust confidence parsing
            confidence = data.get("confidence", 0.5)
            if isinstance(confidence, str):
                conf_match = re.search(r'0?\.\d+|\d+\.?\d*', str(confidence))
                if conf_match:
                    confidence = float(conf_match.group())
                    # If it's > 1, assume it's a percentage
                    if confidence > 1:
                        confidence = confidence / 100.0
                else:
                    confidence_map = {
                        'low': 0.3, 'medium': 0.6, 'high': 0.85,
                        'poor': 0.2, 'fair': 0.5, 'good': 0.7, 'excellent': 0.9,
                        'very low': 0.15, 'very high': 0.95
                    }
                    confidence = confidence_map.get(str(confidence).lower(), 0.5)
            confidence = max(0.0, min(1.0, float(confidence)))
            
            return Evaluation(
                score=float(score),
                feedback=str(data.get("feedback", "")),
                evidence_ids=list(data.get("evidence_ids", [])),
                confidence=float(confidence),
            )
        except Exception as e:
            print(f"[ERROR] Evaluator failed: {e}")
            # Fallback - try to extract any useful info
            try:
                content = getattr(res, "content", "")
                # Try to find any numbers that might be scores
                score_match = re.search(r'score["\s:]+(\d+)', content, re.IGNORECASE)
                if score_match:
                    score = float(score_match.group(1))
                else:
                    score = 50.0
                
                return Evaluation(
                    score=score,
                    feedback=f"Partial evaluation (parsing error: {str(e)})",
                    evidence_ids=[],
                    confidence=0.3
                )
            except:
                return Evaluation(
                    score=0.0,
                    feedback=f"Evaluation failed: {str(e)}",
                    evidence_ids=[],
                    confidence=0.0
                )