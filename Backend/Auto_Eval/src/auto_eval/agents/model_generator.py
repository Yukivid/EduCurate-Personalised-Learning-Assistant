from ..core.types import ModelAnswer
import os

try:
    from langchain_openai import ChatOpenAI  # type: ignore
except Exception:  # pragma: no cover
    ChatOpenAI = None  # type: ignore

try:
    from langchain_google_genai import ChatGoogleGenerativeAI  # type: ignore
except Exception:  # pragma: no cover
    ChatGoogleGenerativeAI = None  # type: ignore


SYSTEM_PROMPT = (
    "You are a helpful grader assistant. Given a question, a student's answer, and retrieved context, "
    "draft a high-quality model answer and a candidate rubric for grading."
)


class ModelGeneratorAgent:
    """
    Generates:
      - A model answer
      - A candidate rubric
      - Optional reasoning text
    using Gemini 2.5 Flash (preferred) or OpenAI fallback.
    """

    def __init__(
        self,
        model: str | None = None,
        temperature: float = 0.2
    ):
        # ✅ Default to Gemini 2.5 Flash
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.temperature = temperature
        self.llm = None

        # ✅ Prefer Gemini if available
        if ChatGoogleGenerativeAI is not None:
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model=self.model,
                    temperature=self.temperature
                )
                print(f"[INFO] Using Google Gemini model: {self.model}")
            except Exception as e:
                print(f"[WARN] Gemini initialization failed: {e}")
                self.llm = None

        # ✅ Fallback: OpenAI (gpt-4o-mini)
        if self.llm is None and ChatOpenAI is not None:
            try:
                openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                self.llm = ChatOpenAI(model=openai_model, temperature=self.temperature)
                print(f"[INFO] Using OpenAI fallback model: {openai_model}")
            except Exception as e:
                print(f"[WARN] OpenAI initialization failed: {e}")
                self.llm = None

    def generate(self, question: str, student_answer: str, passages_text: str) -> ModelAnswer:
        """Generates the model answer and rubric using the configured LLM."""
        if self.llm is None:
            # 🧩 Offline fallback
            return ModelAnswer(
                answer="",
                candidate_rubric="Clarity, Correctness, Completeness",
                reasoning=None,
            )

        messages = [
            ("system", SYSTEM_PROMPT),
            (
                "user",
                f"Question:\n{question}\n\n"
                f"Student Answer:\n{student_answer}\n\n"
                f"Context:\n{passages_text}\n\n"
                "Respond as JSON with keys: answer (string), candidate_rubric (simple string, not nested object), reasoning (string)."
            ),
        ]

        try:
            res = self.llm.invoke(messages)
        except Exception as e:
            print(f"[ERROR] LLM invocation failed: {e}")
            return ModelAnswer(
                answer="",
                candidate_rubric="Clarity, Correctness, Completeness",
                reasoning=None,
            )

        # Try to parse JSON response
        try:
            import json
            import re
            
            text = getattr(res, "content", "{}")
            
            # Remove markdown code blocks if present
            text = re.sub(r'^```json\s*', '', text)
            text = re.sub(r'^```\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            text = text.strip()
            
            data = json.loads(text)
            
            # Handle candidate_rubric - convert to string if it's a dict/object
            candidate_rubric = data.get("candidate_rubric", "")
            if isinstance(candidate_rubric, dict):
                # Convert dict to readable string format
                if "criteria" in candidate_rubric:
                    # Format as bullet points
                    criteria = candidate_rubric.get("criteria", [])
                    if isinstance(criteria, list):
                        rubric_parts = []
                        for item in criteria:
                            if isinstance(item, dict):
                                desc = item.get("description", str(item))
                                rubric_parts.append(f"- {desc}")
                            else:
                                rubric_parts.append(f"- {item}")
                        candidate_rubric = "\n".join(rubric_parts)
                    else:
                        candidate_rubric = json.dumps(candidate_rubric, indent=2)
                else:
                    # Just stringify the dict
                    candidate_rubric = json.dumps(candidate_rubric, indent=2)
            elif not isinstance(candidate_rubric, str):
                candidate_rubric = str(candidate_rubric)
            
            # Fallback if empty
            if not candidate_rubric or candidate_rubric.strip() == "":
                candidate_rubric = "Clarity, Correctness, Completeness"
            
            return ModelAnswer(
                answer=data.get("answer", ""),
                candidate_rubric=candidate_rubric,
                reasoning=data.get("reasoning"),
            )
        except Exception as e:
            print(f"[WARN] JSON parsing failed: {e}, using raw content")
            text = getattr(res, "content", "") or ""
            return ModelAnswer(
                answer=text,
                candidate_rubric="Clarity, Correctness, Completeness",
                reasoning=None,
            )