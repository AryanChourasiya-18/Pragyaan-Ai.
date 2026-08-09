from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ChatMessage, Document, User
from app.schemas import (
    ChatRequest, ChatResponse, ChatSource, SummaryRequest, SummaryOut,
)
from app.security import get_current_user
from app.services import ai_service
from app.routers.documents import get_document_full_text

router = APIRouter(prefix="/ai", tags=["ai"])


def _get_owned_document(document_id: str, db: Session, user: User) -> Document:
    doc = db.query(Document).filter(Document.id == document_id, Document.owner_id == user.id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    return doc


@router.post("/summary", response_model=SummaryOut)
def summarize(payload: SummaryRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = _get_owned_document(payload.document_id, db, user)
    full_text = get_document_full_text(doc)
    summary = ai_service.summarize_text(full_text, payload.style)
    return SummaryOut(summary=summary)


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = _get_owned_document(payload.document_id, db, user)

    db.add(ChatMessage(document_id=doc.id, role="user", content=payload.message))

    answer, sources = ai_service.answer_from_document(doc.id, payload.message)

    db.add(ChatMessage(
        document_id=doc.id,
        role="assistant",
        content=answer,
        source_pages=",".join(str(s["page"]) for s in sources if s.get("page")),
    ))
    db.commit()

    return ChatResponse(answer=answer, sources=[ChatSource(page=s["page"], snippet=s["snippet"]) for s in sources])
