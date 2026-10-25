from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.session import Base, SessionLocal, engine
from app.models import ApprovedPlan, DesignIssue, NbcSkill, Project  # noqa: F401
from app.api.routes.knowledge import router as knowledge_router
from app.api.routes.projects import router as projects_router
from app.seed import seed_nbc

Base.metadata.create_all(bind=engine)
with SessionLocal() as _seed_db:
    seed_nbc(_seed_db)

app = FastAPI(title="Fire Design Agent", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(projects_router, prefix="/api")
app.include_router(knowledge_router, prefix="/api")


@app.on_event("startup")
def startup() -> None:
    db = SessionLocal()
    try:
        seed_nbc(db)
    finally:
        db.close()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "llm": "configured" if settings.llm_api_key else "fallback"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
