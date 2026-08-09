from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import PerformanceLog, User
from app.schemas import PerformanceSummaryOut
from app.security import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=PerformanceSummaryOut)
def performance_summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    logs = db.query(PerformanceLog).filter(PerformanceLog.user_id == user.id).all()

    if not logs:
        return PerformanceSummaryOut(average_score=0, total_study_minutes=0, weak_subjects=[], strong_subjects=[])

    scores_by_subject = defaultdict(list)
    total_minutes = 0
    all_scores = []

    for log in logs:
        total_minutes += log.study_time_minutes or 0
        if log.score_percent is not None:
            scores_by_subject[log.subject].append(log.score_percent)
            all_scores.append(log.score_percent)

    avg_by_subject = {s: sum(v) / len(v) for s, v in scores_by_subject.items()}
    weak = sorted(avg_by_subject, key=avg_by_subject.get)[:2]
    strong = sorted(avg_by_subject, key=avg_by_subject.get, reverse=True)[:2]

    return PerformanceSummaryOut(
        average_score=sum(all_scores) / len(all_scores) if all_scores else 0,
        total_study_minutes=total_minutes,
        weak_subjects=[str(s) for s in weak],
        strong_subjects=[str(s) for s in strong],
    )
