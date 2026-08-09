from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import ai, analytics, auth, documents, flashcards, notes, planner, quiz

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Pragyaan API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(ai.router)
app.include_router(quiz.router)
app.include_router(flashcards.router)
app.include_router(notes.router)
app.include_router(planner.router)
app.include_router(analytics.router)


@app.get("/health")
def health():
    return {"status": "ok"}
