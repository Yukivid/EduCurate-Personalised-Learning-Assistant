from typing import Optional
import os
from pydantic import BaseModel

class Env(BaseModel):
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    google_api_key: Optional[str] = os.getenv("GOOGLE_API_KEY")

ENV = Env()
