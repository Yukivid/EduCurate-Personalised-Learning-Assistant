import sys
import os

print("Current working directory:", os.getcwd())

# Ensure absolute path of Auto-Eval/src is appended
sys.path.append(r"D:\BJT\BJT\Backend\Auto-Eval\src")

print("sys.path after append:", sys.path)

try:
    from auto_eval.agents.retriever import RetrieverAgent
    print("Import successful:", RetrieverAgent)
except Exception as e:
    print("Import failed:", e)
