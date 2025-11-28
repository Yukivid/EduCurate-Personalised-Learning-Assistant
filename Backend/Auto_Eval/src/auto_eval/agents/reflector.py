from ..core.types import Reflection
import os

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except Exception:
    ChatGoogleGenerativeAI = None

try:
    from langchain_openai import ChatOpenAI
except Exception:
    ChatOpenAI = None


REFLECT_SYSTEM = (
    "You are a sanity checker. Flag hallucinations or rubric misalignment and adjust confidence if needed. "
    "Return ONLY valid JSON with numeric confidence_adjustment."
)


class ReflectorAgent:
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
                print(f"[INFO] Reflector using: {self.model}")
            except Exception as e:
                print(f"[WARN] Gemini init failed in Reflector: {e}")
                self.llm = None
        
        # Fallback to OpenAI
        if self.llm is None and ChatOpenAI is not None:
            try:
                openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                self.llm = ChatOpenAI(model=openai_model, temperature=temperature)
                print(f"[INFO] Reflector using OpenAI fallback: {openai_model}")
            except Exception as e:
                print(f"[WARN] OpenAI init failed in Reflector: {e}")
                self.llm = None

    def reflect(self, context: str, evaluation_feedback: str) -> Reflection:
        if not self.llm:
            return Reflection(issues=[], adjustments=None, confidence_adjustment=0.0)
        
        messages = [
            ("system", REFLECT_SYSTEM),
            (
                "user",
                "Given the context and the evaluation feedback, list any issues found (hallucinations, missing evidence, rubric misuse).\n"
                "Return ONLY valid JSON with these exact keys:\n"
                "{\n"
                '  "issues": [<list of strings>],\n'
                '  "adjustments": "<string or null>",\n'
                '  "confidence_adjustment": <number between -0.3 and 0.3>\n'
                "}\n\n"
                "IMPORTANT: confidence_adjustment must be a number, not a string.\n\n"
                f"Context:\n{context}\n\nEvaluation Feedback:\n{evaluation_feedback}\n",
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
            
            # Robust confidence_adjustment parsing
            adj = data.get("confidence_adjustment", 0.0)
            if isinstance(adj, str):
                # Try to extract number
                adj_match = re.search(r'-?\d+\.?\d*', str(adj))
                if adj_match:
                    adj = float(adj_match.group())
                else:
                    # Map text to numbers
                    adj_map = {
                        'none': 0.0, 'low': -0.1, 'medium': -0.2, 'high': -0.3,
                        'slight': -0.05, 'moderate': -0.15, 'significant': -0.25,
                        'positive': 0.1, 'negative': -0.1
                    }
                    adj = adj_map.get(str(adj).lower(), 0.0)
            
            try:
                adj = float(adj)
            except Exception:
                adj = 0.0
            
            # Clamp adjustment to [-0.3, 0.3]
            adj = max(-0.3, min(0.3, adj))
            
            return Reflection(
                issues=list(data.get("issues", [])),
                adjustments=data.get("adjustments"),
                confidence_adjustment=adj
            )
        except Exception as e:
            print(f"[ERROR] Reflector failed: {e}")
            return Reflection(issues=[], adjustments=None, confidence_adjustment=0.0)