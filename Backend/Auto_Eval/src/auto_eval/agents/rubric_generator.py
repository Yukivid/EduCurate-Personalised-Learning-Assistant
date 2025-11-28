from ..core.types import Rubric
import os

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except Exception:
    ChatGoogleGenerativeAI = None

try:
    from langchain_openai import ChatOpenAI
except Exception:
    ChatOpenAI = None


RUBRIC_SYSTEM = (
    "You are a rubric normalizer. Clean and standardize the candidate rubric into clear bullet criteria."
)


class RubricGeneratorAgent:
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
                print(f"[INFO] RubricGenerator using: {self.model}")
            except Exception as e:
                print(f"[WARN] Gemini init failed in RubricGenerator: {e}")
                self.llm = None
        
        # Fallback to OpenAI
        if self.llm is None and ChatOpenAI is not None:
            try:
                openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                self.llm = ChatOpenAI(model=openai_model, temperature=temperature)
                print(f"[INFO] RubricGenerator using OpenAI fallback: {openai_model}")
            except Exception as e:
                print(f"[WARN] OpenAI init failed in RubricGenerator: {e}")
                self.llm = None

    def finalize(self, candidate_rubric: str) -> Rubric:
        if not self.llm:
            # Simple deterministic parse by commas or newlines
            text = candidate_rubric.strip()
            parts = [p.strip() for p in (text.replace("\n", ",").split(",")) if p.strip()]
            return Rubric(rubric_text=text, criteria=parts)
        
        messages = [
            ("system", RUBRIC_SYSTEM),
            ("user", f"Candidate Rubric:\n{candidate_rubric}\n\nReturn bullet list criteria, one per line."),
        ]
        
        try:
            res = self.llm.invoke(messages)
            content = getattr(res, "content", "").strip()
            
            # Parse bullet points or numbered lists
            lines = [l.strip("- ").strip("* ").strip() for l in content.splitlines() if l.strip()]
            # Remove numbering like "1.", "2.", etc.
            import re
            lines = [re.sub(r'^\d+\.\s*', '', l) for l in lines if l]
            
            return Rubric(rubric_text=content, criteria=lines)
        except Exception as e:
            print(f"[ERROR] RubricGenerator failed: {e}")
            # Fallback parsing
            text = candidate_rubric.strip()
            parts = [p.strip() for p in (text.replace("\n", ",").split(",")) if p.strip()]
            return Rubric(rubric_text=text, criteria=parts)