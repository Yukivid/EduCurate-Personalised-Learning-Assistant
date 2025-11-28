import os
import re
import json
import logging
import importlib
from typing import List, Optional

from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel

# Conditional imports for Torch and Transformers

HF_AVAILABLE = False
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    HF_AVAILABLE = True
except Exception as e:
    HF_AVAILABLE = False
    torch = None  # Prevent NameError if torch is unavailable
    logging.warning(f"⚠️ Torch/Transformers not available: {e}")

# Optional: PEFT / LoRA imports

PEFT_AVAILABLE = False
LoraConfig = None
get_peft_model = None
prepare_model_for_int8_training = None
try:
    spec = importlib.util.find_spec("peft")
    if spec:
        peft = importlib.import_module("peft")
        LoraConfig = getattr(peft, "LoraConfig", None)
        get_peft_model = getattr(peft, "get_peft_model", None)
        prepare_model_for_int8_training = getattr(peft, "prepare_model_for_int8_training", None)
        if LoraConfig and get_peft_model:
            PEFT_AVAILABLE = True
except Exception as e:
    logging.warning(f"⚠️ PEFT not available: {e}")
    PEFT_AVAILABLE = False

# Environment Config

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
HF_ROADMAP_MODEL_PATH = os.environ.get("HF_ROADMAP_MODEL_PATH")
LLM_MODEL = None  # injected external model (e.g., Gemini)

logger = logging.getLogger(__name__)
app = FastAPI(title="Roadmap Generation Service")

# Helper: Parse roadmap text into topic list

def parse_roadmap_text(text: str) -> List[str]:
    """
    Parse roadmap text in multiple formats into a clean topic list.
    Accepts inputs like:
      "Topic Names: [A, B, C]"
      "1. A\n2. B\n3. C"
      "- A\n- B\n- C"
    """
    if not text:
        return []
    text = text.strip()
    text = re.sub(r'(?i)^.*topic names\s*:\s*', '', text).strip()
    text = re.sub(r'[\r\n]+', ', ', text)
    text = re.sub(r'^\-+\s*', '', text)
    text = text.strip(" []\t\n")
    parts = re.split(r'[,\u2022;\n]+', text)
    cleaned = []
    for p in parts:
        s = re.sub(r'^\s*\d+\.\s*', '', p).strip()
        if s:
            cleaned.append(s)
    return cleaned

# Main: Roadmap Generator Wrapper

class RoadmapGenerator:
    def __init__(self, hf_model_path: Optional[str] = None, llm_client=None, device: Optional[str] = None):
        """
        Initialize roadmap generator.
        - hf_model_path: path to fine-tuned HF seq2seq model
        - llm_client: fallback LLM client (e.g., Gemini)
        """
        self.llm = llm_client
        self.hf_model = None
        self.tokenizer = None

        # --- Safe device handling ---
        if HF_AVAILABLE:
            try:
                import torch
                self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
            except Exception:
                self.device = "cpu"
        else:
            self.device = "cpu"

        # --- Load HF model if available ---
        if hf_model_path and HF_AVAILABLE:
            try:
                logger.info(f"🔹 Loading HF roadmap model from {hf_model_path}")
                self.tokenizer = AutoTokenizer.from_pretrained(hf_model_path, use_fast=True)
                self.hf_model = AutoModelForSeq2SeqLM.from_pretrained(hf_model_path)
                self.hf_model.to(self.device)
                logger.info(f"Loaded HF model to device: {self.device}")
            except Exception as e:
                logger.exception(f"Failed loading HF model: {e}")
                self.hf_model = None
        else:
            logger.info("ℹ️ No fine-tuned HF model found, will use LLM fallback.")

    # Few-shot prompt helper
    
    def _few_shot_prompt(self, topic: str) -> str:
        examples = [
            {
                "in": "linear algebra for machine learning",
                "out": "Topic Names: [Vectors and vector operations, Linear transformations, Matrices and matrix operations, Determinants, Eigenvalues and eigenvectors, Matrix decompositions (SVD), Systems of linear equations, Applications in ML]"
            },
            {
                "in": "html and css basics",
                "out": "Topic Names: [HTML structure and tags, Text formatting and links, Images and multimedia, CSS selectors and specificity, CSS box model, Layouts with Flexbox and Grid, Responsive design, Forms]"
            }
        ]
        prompt_parts = [
            "You are a concise curriculum planner. Given a learner topic, output the minimal ordered list of essential topic names that one must learn to master the topic. "
            "Do not include learning resources, durations, or commentary — only produce a compact list labeled exactly as: "
            "Topic Names: [Comma-separated list]."
        ]
        for ex in examples:
            prompt_parts.append(f"Input: {ex['in']}\nOutput: {ex['out']}")
        prompt_parts.append(f"Input: {topic}\nOutput:")
        return "\n\n".join(prompt_parts)

    # Generate Roadmap
    
    def generate_roadmap(self, topic: str, max_length: int = 256) -> List[str]:
        """Generate roadmap using fine-tuned HF model or fallback LLM."""
        # --- Try fine-tuned HF model ---
        if self.hf_model and HF_AVAILABLE:
            try:
                input_text = f"Generate a compact ordered roadmap for the topic: {topic}\nOutput format: Topic Names: [A, B, C]"
                inputs = self.tokenizer(input_text, return_tensors="pt", truncation=True, padding=True).to(self.device)
                with torch.no_grad():
                    out = self.hf_model.generate(
                        **inputs,
                        max_length=max_length,
                        num_beams=4,
                        early_stopping=True
                    )
                text = self.tokenizer.decode(out[0], skip_special_tokens=True)
                roadmap = parse_roadmap_text(text)
                if roadmap:
                    return roadmap
            except Exception as e:
                logger.exception(f"❌ HF model generation failed: {e}")

        # --- Fallback: LLM client ---
        if self.llm:
            try:
                prompt = self._few_shot_prompt(topic)
                response = self.llm.generate_content(prompt)
                roadmap_text = ""
                if hasattr(response, "candidates") and response.candidates:
                    roadmap_text = response.candidates[0].content.parts[0].text.strip()
                else:
                    roadmap_text = getattr(response, "text", "") or str(response)
                roadmap = parse_roadmap_text(roadmap_text)
                if roadmap:
                    return roadmap
            except Exception as e:
                logger.exception(f"❌ LLM fallback generation failed: {e}")

        # --- Final fallback ---
        return [topic]

# Fine-tuning Function (HF + optional LoRA)

def train_roadmap_model(
    train_jsonl_path: str,
    output_dir: str,
    base_model: str = "t5-small",
    epochs: int = 3,
    batch_size: int = 8,
    lr: float = 5e-5,
    use_lora: bool = True,
):
    """Fine-tune a seq2seq model (T5-style) for roadmap generation."""
    if not HF_AVAILABLE:
        raise RuntimeError("Transformers or torch not available. Install with: pip install torch transformers datasets")

    from datasets import load_dataset
    from transformers import DataCollatorForSeq2Seq, Seq2SeqTrainingArguments, Seq2SeqTrainer

    logger.info("🔹 Loading training dataset...")
    ds = load_dataset("json", data_files={"train": train_jsonl_path})
    tokenizer = AutoTokenizer.from_pretrained(base_model, use_fast=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(base_model)

    if use_lora and PEFT_AVAILABLE:
        try:
            logger.info("🔹 Applying LoRA fine-tuning...")
            lora_config = LoraConfig(
                r=8,
                lora_alpha=32,
                target_modules=["q", "v", "k", "o"],
                lora_dropout=0.05,
                bias="none",
                task_type="SEQ_2_SEQ_LM",
            )
            try:
                model = prepare_model_for_int8_training(model)
            except Exception:
                pass
            model = get_peft_model(model, lora_config)
        except Exception as e:
            logger.warning(f"⚠️ Failed to apply LoRA: {e}")

    def preprocess(examples):
        inputs = [f"Generate ordered roadmap for: {x}" for x in examples["input"]]
        targets = examples["output"]
        model_inputs = tokenizer(inputs, max_length=256, truncation=True)
        labels = tokenizer(targets, max_length=256, truncation=True).input_ids
        model_inputs["labels"] = labels
        return model_inputs

    ds_proc = ds["train"].map(preprocess, batched=True, remove_columns=ds["train"].column_names)
    data_collator = DataCollatorForSeq2Seq(tokenizer, model=model)

    training_args = Seq2SeqTrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=batch_size,
        predict_with_generate=True,
        num_train_epochs=epochs,
        logging_steps=50,
        save_strategy="epoch",
        evaluation_strategy="no",
        learning_rate=lr,
        weight_decay=0.01,
        fp16=torch.cuda.is_available() if HF_AVAILABLE else False,
        push_to_hub=False,
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=ds_proc,
        tokenizer=tokenizer,
        data_collator=data_collator,
    )

    logger.info("🚀 Starting fine-tuning...")
    trainer.train()
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)
    logger.info(f"✅ Model fine-tuned and saved to {output_dir}")
    return output_dir

# FastAPI Startup Hook

@app.on_event("startup")
async def startup_event():
    """Initialize shared RoadmapGenerator instance."""
    global LLM_MODEL
    try:
        app.state.roadmap_gen = RoadmapGenerator(
            hf_model_path=HF_ROADMAP_MODEL_PATH,
            llm_client=LLM_MODEL
        )
        logger.info("✅ RoadmapGenerator initialized successfully.")
    except Exception as e:
        logger.exception(f"❌ Failed to initialize RoadmapGenerator: {e}")
        app.state.roadmap_gen = None
