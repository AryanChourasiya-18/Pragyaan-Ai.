from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Flashcard, User
from app.schemas import FlashcardOut, FlashcardReviewRequest
from app.security import get_current_user
from app.services import ai_service
from app.routers.documents import get_document_full_text
from app.routers.ai import _get_owned_document

router = APIRouter(prefix="/flashcards", tags=["flashcards"])


@router.post("/generate/{document_id}", response_model=List[FlashcardOut])
def generate_flashcards(document_id: str, count: int = 15, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = _get_owned_document(document_id, db, user)
    full_text = get_document_full_text(doc)

    raw_cards = ai_service.generate_flashcards(full_text, count)
    if not raw_cards:
        raise HTTPException(502, "AI failed to generate flashcards — try again")

    cards = []
    for c in raw_cards:
        card = Flashcard(owner_id=user.id, document_id=doc.id, front=c.get("front", ""), back=c.get("back", ""))
        db.add(card)
        cards.append(card)
    db.commit()
    for c in cards:
        db.refresh(c)
    return cards


@router.get("/due", response_model=List[FlashcardOut])
def get_due_flashcards(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    now = datetime.utcnow()
    return (
        db.query(Flashcard)
        .filter(Flashcard.owner_id == user.id, Flashcard.next_review_at <= now)
        .order_by(Flashcard.next_review_at)
        .all()
    )


@router.post("/review", response_model=FlashcardOut)
def review_flashcard(payload: FlashcardReviewRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    card = db.query(Flashcard).filter(Flashcard.id == payload.flashcard_id, Flashcard.owner_id == user.id).first()
    if not card:
        raise HTTPException(404, "Flashcard not found")

    _apply_sm2(card, payload.quality)
    card.last_reviewed_at = datetime.utcnow()
    db.commit()
    db.refresh(card)
    return card


def _apply_sm2(card: Flashcard, quality: int) -> None:
    """SM-2 spaced repetition algorithm (as used by Anki/SuperMemo)."""
    quality = max(0, min(5, quality))

    if quality < 3:
        card.interval_days = 1
    else:
        if card.interval_days <= 1:
            card.interval_days = 6
        else:
            card.interval_days = round(card.interval_days * card.ease_factor)

    card.ease_factor = max(
        1.3,
        card.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)),
    )
    card.next_review_at = datetime.utcnow() + timedelta(days=card.interval_days)
