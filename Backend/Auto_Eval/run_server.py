# Auto_Eval/run_server.py
import sys
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

# Add the src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Now import and run your mcp_server
from src.auto_eval.server.mcp_server import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)