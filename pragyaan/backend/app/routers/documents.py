from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Document, Subject, User
from app.schemas import DocumentOut
from app.security import get_current_user
from app.services import pdf_service, storage_service, vector_service

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    subject: str = Form("other"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")

    file_bytes = await file.read()
    path = storage_service.save_upload(file_bytes, file.filename)

    pages, used_ocr = pdf_service.extract_text_per_page(path)
    chunks = pdf_service.chunk_pages(pages)

    doc = Document(
        owner_id=user.id,
        title=file.filename,
        subject=Subject(subject) if subject in Subject.__members__ else Subject.other,
        file_path=path,
        page_count=len(pages),
        is_ocr=used_ocr,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    collection = vector_service.index_chunks(doc.id, chunks)
    doc.vector_collection = collection
    db.commit()

    return doc


@router.get("", response_model=List[DocumentOut])
def list_documents(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Document).filter(Document.owner_id == user.id).order_by(Document.created_at.desc()).all()


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == document_id, Document.owner_id == user.id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    return doc


@router.delete("/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == document_id, Document.owner_id == user.id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    db.delete(doc)
    db.commit()
    return {"deleted": True}


def get_document_full_text(doc: Document) -> str:
    pages, _ = pdf_service.extract_text_per_page(doc.file_path)
    return "\n\n".join(pages)
