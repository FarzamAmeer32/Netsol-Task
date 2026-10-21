
import os

from fastapi import FastAPI

app = FastAPI(
    title=os.getenv("APP_NAME", "Python API Starter"),
    version=os.getenv("APP_VERSION", "0.1.0"),
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "version": app.version,
    }
