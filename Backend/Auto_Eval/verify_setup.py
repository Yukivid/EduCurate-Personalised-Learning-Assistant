#!/usr/bin/env python3
"""
Verification script for Auto-Eval setup.
Run this after completing installation to ensure everything works.
"""

import sys
import os

def check_dependencies():
    """Check if all required packages are installed."""
    required = [
        "langchain_google_genai",
        "langchain_openai",
        "langchain_community",
        "faiss",
        "fastapi",
        "pydantic",
        "langgraph",
        "dotenv",
    ]
    
    missing = []
    for pkg in required:
        try:
            __import__(pkg.replace("-", "_"))
            print(f"✓ {pkg}")
        except ImportError:
            print(f"✗ {pkg} - MISSING")
            missing.append(pkg)
    
    return missing


def check_env_vars():
    """Check environment configuration."""
    from dotenv import load_dotenv
    load_dotenv()
    
    google_key = os.getenv("GOOGLE_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    print("\n=== Environment Variables ===")
    if google_key:
        print(f"✓ GOOGLE_API_KEY: {google_key[:20]}...")
    else:
        print("✗ GOOGLE_API_KEY: NOT SET")
    
    if openai_key:
        print(f"✓ OPENAI_API_KEY: {openai_key[:20]}... (fallback)")
    else:
        print("⚠ OPENAI_API_KEY: NOT SET (optional)")
    
    print(f"✓ GEMINI_MODEL: {gemini_model}")
    
    return bool(google_key or openai_key)


def test_agents():
    """Test agent initialization."""
    print("\n=== Testing Agents ===")
    
    try:
        from src.auto_eval.agents.model_generator import ModelGeneratorAgent
        agent = ModelGeneratorAgent()
        if agent.llm:
            print(f"✓ ModelGeneratorAgent initialized with {agent.model}")
        else:
            print("✗ ModelGeneratorAgent failed - no LLM")
            return False
    except Exception as e:
        print(f"✗ ModelGeneratorAgent error: {e}")
        return False
    
    try:
        from src.auto_eval.agents.retriever import RetrieverAgent
        retriever = RetrieverAgent()
        print("✓ RetrieverAgent initialized")
    except Exception as e:
        print(f"✗ RetrieverAgent error: {e}")
        return False
    
    return True


def test_simple_generation():
    """Test a simple generation."""
    print("\n=== Testing Simple Generation ===")
    
    try:
        from src.auto_eval.agents.model_generator import ModelGeneratorAgent
        agent = ModelGeneratorAgent()
        
        result = agent.generate(
            question="What is 2+2?",
            student_answer="4",
            passages_text="Mathematics basics: 2+2 equals 4."
        )
        
        if result.answer or result.candidate_rubric:
            print("✓ Generation successful")
            print(f"  Model Answer: {result.answer[:100]}...")
            print(f"  Rubric: {result.candidate_rubric[:100]}...")
            return True
        else:
            print("✗ Generation returned empty results")
            return False
    except Exception as e:
        print(f"✗ Generation failed: {e}")
        return False


def main():
    print("=" * 50)
    print("Auto-Eval Setup Verification")
    print("=" * 50)
    
    # Check dependencies
    print("\n=== Checking Dependencies ===")
    missing = check_dependencies()
    
    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print("Run: pip install " + " ".join(missing))
        sys.exit(1)
    
    # Check environment
    if not check_env_vars():
        print("\n❌ No API keys configured!")
        print("Create a .env file with GOOGLE_API_KEY or OPENAI_API_KEY")
        sys.exit(1)
    
    # Test agents
    if not test_agents():
        print("\n❌ Agent initialization failed!")
        sys.exit(1)
    
    # Test generation
    if not test_simple_generation():
        print("\n❌ Generation test failed!")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✅ All checks passed! Auto-Eval is ready to use.")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Run CLI: python -m src.auto_eval.pipeline.cli run --question '...' --answer '...'")
    print("2. Start server: uvicorn src.auto_eval.server.mcp_server:app --reload")


if __name__ == "__main__":
    main()