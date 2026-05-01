from fastapi import FastAPI

from app.api.analyze import router as analyze_router

app = FastAPI(title="Lawgic MVP API", version="0.1.0")

app.include_router(analyze_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
