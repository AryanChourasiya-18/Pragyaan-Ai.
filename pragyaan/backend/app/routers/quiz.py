import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    Difficulty, PerformanceLog, Quiz, QuizAttempt, QuizQuestion, User,
)
from app.schemas import (
    QuizGenerateRequest, QuizOut, QuizResultItem, QuizResultOut,
    QuizSubmitRequest,
)
from app.security import get_current_user
from app.services import ai_service
from app.routers.documents import get_document_full_text
from app.routers.ai import _get_owned_document

router = APIRouter(prefix="/quiz", tags=["quiz"])


@router.post("/generate", response_model=QuizOut)
def generate_quiz(payload: QuizGenerateRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = _get_owned_document(payload.document_id, db, user)
    full_text = get_document_full_text(doc)

    raw_questions = ai_service.generate_quiz(
        full_text, payload.question_types, payload.difficulty, payload.exam_level, payload.count
    )
    if not raw_questions:
        raise HTTPException(502, "AI failed to generate questions — try again or reduce count")

    quiz = Quiz(
        owner_id=user.id,
        document_id=doc.id,
        title=f"{doc.title} — {payload.difficulty.title()} Quiz",
        difficulty=Difficulty(payload.difficulty) if payload.difficulty in Difficulty.__members__ else Difficulty.medium,
        exam_level=payload.exam_level,
        negative_marking=payload.negative_marking,
        time_limit_seconds=payload.time_limit_seconds,
    )
    db.add(quiz)
    db.flush()

    for q in raw_questions:
        db.add(QuizQuestion(
            quiz_id=quiz.id,
            type=q.get("type", "mcq"),
            question_text=q.get("question_text", ""),
            options=json.dumps(q.get("options")) if q.get("options") else None,
            correct_answer=str(q.get("correct_answer", "")),
            explanation=q.get("explanation"),
            source_page=q.get("source_page"),
        ))
    db.commit()
    db.refresh(quiz)
    return _quiz_to_out(quiz)


@router.get("/{quiz_id}", response_model=QuizOut)
def get_quiz(quiz_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id, Quiz.owner_id == user.id).first()
    if not quiz:
        raise HTTPException(404, "Quiz not found")
    return _quiz_to_out(quiz)


@router.post("/submit", response_model=QuizResultOut)
def submit_quiz(payload: QuizSubmitRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    quiz = db.query(Quiz).filter(Quiz.id == payload.quiz_id, Quiz.owner_id == user.id).first()
    if not quiz:
        raise HTTPException(404, "Quiz not found")

    questions_by_id = {q.id: q for q in quiz.questions}
    results = []
    score = 0.0
    total_marks = float(len(questions_by_id))

    for ans in payload.answers:
        q = questions_by_id.get(ans.question_id)
        if not q:
            continue
        is_correct = ans.answer.strip().lower() == q.correct_answer.strip().lower()
        if is_correct:
            score += 1
        elif quiz.negative_marking:
            score -= 0.25
        results.append(QuizResultItem(
            question_id=q.id, correct=is_correct,
            correct_answer=q.correct_answer, explanation=q.explanation,
        ))

    attempt = QuizAttempt(
        quiz_id=quiz.id,
        user_id=user.id,
        score=score,
        total_marks=total_marks,
        time_taken_seconds=payload.time_taken_seconds,
        answers_json=json.dumps([a.model_dump() for a in payload.answers]),
    )
    db.add(attempt)

    doc = quiz.document
    db.add(PerformanceLog(
        user_id=user.id,
        subject=doc.subject if doc else "other",
        chapter=doc.title if doc else None,
        activity_type="quiz",
        score_percent=(score / total_marks * 100) if total_marks else 0,
        study_time_minutes=(payload.time_taken_seconds or 0) // 60,
    ))
    db.commit()

    return QuizResultOut(score=score, total_marks=total_marks, results=results)


def _quiz_to_out(quiz: Quiz) -> QuizOut:
    return QuizOut(
        id=quiz.id,
        title=quiz.title,
        difficulty=quiz.difficulty,
        negative_marking=quiz.negative_marking,
        time_limit_seconds=quiz.time_limit_seconds,
        questions=[{
            "id": q.id,
            "type": q.type,
            "question_text": q.question_text,
            "options": json.loads(q.options) if q.options else None,
            "source_page": q.source_page,
        } for q in quiz.questions],
    )
