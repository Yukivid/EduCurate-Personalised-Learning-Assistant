import httpx
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class AutoEvalClient:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.client = None
    
    async def __aenter__(self):
        try:
            self.client = httpx.AsyncClient(
                base_url=self.base_url, 
                timeout=30.0,
                follow_redirects=True
            )
            # Test connection on startup
            await self._health_check()
            return self
        except Exception as e:
            logger.warning(f"Auto-Eval connection failed: {e}")
            self.client = None
            return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    async def _health_check(self) -> bool:
        """Check if Auto-Eval service is healthy"""
        if not self.client:
            return False
        try:
            response = await self.client.get("/health", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False
    
    async def evaluate_answer(self, question: str, student_answer: str, top_k: int = 5) -> Dict[str, Any]:
        """Evaluate a single answer using the Auto-Eval pipeline"""
        # Check if client is available first
        if not self.client or not await self._health_check():
            logger.warning("Auto-Eval service unavailable, using fallback")
            return self._fallback_evaluation(question, student_answer)
        
        try:
            payload = {
                "question": question,
                "student_answer": student_answer,
                "top_k": top_k,
                "use_graph": True
            }
            response = await self.client.post("/run", json=payload, timeout=30.0)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Auto-Eval evaluation completed with score: {result.get('grade', 'N/A')}")
            return result
        except httpx.TimeoutException:
            logger.error("Auto-Eval evaluation timeout")
            return self._fallback_evaluation(question, student_answer, "Evaluation timeout")
        except httpx.HTTPStatusError as e:
            logger.error(f"Auto-Eval HTTP error {e.response.status_code}: {e.response.text}")
            return self._fallback_evaluation(question, student_answer, f"HTTP error {e.response.status_code}")
        except Exception as e:
            logger.error(f"Auto-Eval evaluation failed: {e}")
            return self._fallback_evaluation(question, student_answer, str(e))
    
    async def grade_answer(self, question: str, student_answer: str, context: str = "") -> Dict[str, Any]:
        """Grade a single answer with optional context"""
        # Check if client is available first
        if not self.client or not await self._health_check():
            logger.warning("Auto-Eval service unavailable, using fallback")
            return self._fallback_evaluation(question, student_answer)
        
        try:
            payload = {
                "question": question,
                "student_answer": student_answer,
                "context": context
            }
            response = await self.client.post("/grade", json=payload, timeout=30.0)
            response.raise_for_status()
            result = response.json()
            return result
        except httpx.TimeoutException:
            logger.error("Auto-Eval grading timeout")
            return self._fallback_evaluation(question, student_answer, "Grading timeout")
        except httpx.HTTPStatusError as e:
            logger.error(f"Auto-Eval HTTP error {e.response.status_code}: {e.response.text}")
            return self._fallback_evaluation(question, student_answer, f"HTTP error {e.response.status_code}")
        except Exception as e:
            logger.error(f"Auto-Eval grading failed: {e}")
            return self._fallback_evaluation(question, student_answer, str(e))
    
    def _fallback_evaluation(self, question: str, student_answer: str, error_msg: str = "") -> Dict[str, Any]:
        """Improved fallback evaluation when Auto-Eval service is unavailable"""
        # Calculate a basic score based on answer length and content
        answer_length = len(student_answer.split())
        base_score = min(60, max(20, answer_length * 3))  # 20-60 based on length
        
        # Simple content analysis
        if any(keyword in student_answer.lower() for keyword in ['because', 'therefore', 'however', 'although']):
            base_score += 10
        if len(student_answer) > 50:
            base_score += 10
            
        final_score = min(80, base_score)  # Cap at 80 for fallback
        
        feedback = f"Basic evaluation: {error_msg}" if error_msg else "Using basic evaluation service"
        
        return {
            "grade": final_score,
            "feedback": feedback,
            "confidence": 0.5,
            "model_answer": "Auto-Eval service unavailable for detailed model answer",
            "rubric": "Basic length and content analysis",
            "source_ids": []
        }