from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Note, User
from app.schemas import NotesGenerateRequest, NotesOut
from app.security import get_current_user
from app.services import ai_service
from app.routers.documents import get_document_full_text
from app.routers.ai import _get_owned_document

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("/generate", response_model=NotesOut)
def generate_notes(payload: NotesGenerateRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = _get_owned_document(payload.document_id, db, user)
    full_text = get_document_full_text(doc)

    content = ai_service.generate_notes(full_text, payload.kind)

    note = Note(document_id=doc.id, kind=payload.kind, content_markdown=content)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note
