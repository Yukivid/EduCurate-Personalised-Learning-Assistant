from fastapi import FastAPI
from routes import evaluation

app = FastAPI(title="EduCurate Auto-Eval AES Server", version="1.0")

app.include_router(evaluation.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("aes_server:app", host="127.0.0.1", port=8002, reload=True)
