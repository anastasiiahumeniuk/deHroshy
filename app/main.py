from fastapi import FastAPI

app = FastAPI(
    title="deHroshy",
    description="Personal monthly finance tracker",
    version="0.1.0",
)

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}