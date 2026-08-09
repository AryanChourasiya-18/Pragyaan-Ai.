import json
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import StudyPlanEntry, User
from app.schemas import StudyPlanEntryOut, StudyPlanRequest
from app.security import get_current_user
from app.services.ai_service import _chat

router = APIRouter(prefix="/planner", tags=["planner"])


@router.post("/generate", response_model=List[StudyPlanEntryOut])
def generate_plan(payload: StudyPlanRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    days_remaining = max(1, (payload.exam_date - datetime.utcnow()).days)

    system = (
        "You are an expert exam study planner for Indian competitive exams. "
        "Return ONLY a valid JSON array, no commentary."
    )
    user_prompt = f"""Create a day-by-day study plan.
Goal: {payload.goal}
Days remaining: {days_remaining}
Subjects to cover: {payload.subjects}
Available hours/day: {payload.hours_per_day}

For each day, return one array item:
{{"day_number": int, "subject": one of {payload.subjects}, "topic": string, "task_type": "study"|"revise"|"quiz"|"mock_test"}}

Balance subjects, include periodic revision days and mock tests near the end. Keep it realistic — one focused topic per day.
"""
    raw = _chat(system, user_prompt, temperature=0.5)
    entries = _parse_json_array(raw)
    if not entries:
        raise HTTPException(502, "AI failed to generate a plan — try again")

    db.query(StudyPlanEntry).filter(StudyPlanEntry.user_id == user.id, StudyPlanEntry.goal == payload.goal).delete()

    saved = []
    for e in entries:
        day_number = int(e.get("day_number", 1))
        entry = StudyPlanEntry(
            user_id=user.id,
            goal=payload.goal,
            day_number=day_number,
            date=_date_for_day(payload, day_number),
            subject=e.get("subject", "other") if e.get("subject") in [s for s in payload.subjects] else "other",
            topic=e.get("topic", ""),
            task_type=e.get("task_type", "study"),
        )
        db.add(entry)
        saved.append(entry)
    db.commit()
    for e in saved:
        db.refresh(e)
    return saved


@router.get("", response_model=List[StudyPlanEntryOut])
def get_plan(goal: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(StudyPlanEntry)
        .filter(StudyPlanEntry.user_id == user.id, StudyPlanEntry.goal == goal)
        .order_by(StudyPlanEntry.day_number)
        .all()
    )


@router.post("/{entry_id}/complete", response_model=StudyPlanEntryOut)
def mark_complete(entry_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    entry = db.query(StudyPlanEntry).filter(StudyPlanEntry.id == entry_id, StudyPlanEntry.user_id == user.id).first()
    if not entry:
        raise HTTPException(404, "Plan entry not found")
    entry.completed = True
    db.commit()
    db.refresh(entry)
    return entry


def _date_for_day(payload: StudyPlanRequest, day_number: int) -> datetime:
    from datetime import timedelta
    return datetime.utcnow() + timedelta(days=day_number - 1)


def _parse_json_array(raw: str) -> list:
    raw = raw.strip().strip("`")
    if raw.startswith("json\n"):
        raw = raw[5:]
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        start, end = raw.find("["), raw.rfind("]")
        if start != -1 and end != -1:
            try:
                return json.loads(raw[start:end + 1])
            except json.JSONDecodeError:
                pass
        return []
