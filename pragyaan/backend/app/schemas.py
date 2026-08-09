from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr


# --- Auth ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: str = "student"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str]
    role: str

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# --- Documents ---
class DocumentOut(BaseModel):
    id: str
    title: str
    subject: str
    page_count: int
    is_ocr: bool
    created_at: datetime

    class Config:
        from_attributes = True


# --- AI Summary ---
class SummaryRequest(BaseModel):
    document_id: str
    style: str = "bullet_points"  # 100_words | 500_words | bullet_points | beginner | advanced | eli10


class SummaryOut(BaseModel):
    summary: str


# --- Chat ---
class ChatRequest(BaseModel):
    document_id: str
    message: str


class ChatSource(BaseModel):
    page: int
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[ChatSource] = []


# --- Question generator / quiz ---
class QuizGenerateRequest(BaseModel):
    document_id: str
    question_types: List[str] = ["mcq"]
    difficulty: str = "medium"
    exam_level: Optional[str] = None  # jee | neet
    count: int = 10
    negative_marking: bool = False
    time_limit_seconds: Optional[int] = None


class QuizQuestionOut(BaseModel):
    id: str
    type: str
    question_text: str
    options: Optional[List[str]] = None
    source_page: Optional[int] = None

    class Config:
        from_attributes = True


class QuizOut(BaseModel):
    id: str
    title: str
    difficulty: str
    negative_marking: bool
    time_limit_seconds: Optional[int]
    questions: List[QuizQuestionOut]

    class Config:
        from_attributes = True


class QuizSubmitAnswer(BaseModel):
    question_id: str
    answer: str


class QuizSubmitRequest(BaseModel):
    quiz_id: str
    answers: List[QuizSubmitAnswer]
    time_taken_seconds: Optional[int] = None


class QuizResultItem(BaseModel):
    question_id: str
    correct: bool
    correct_answer: str
    explanation: Optional[str] = None


class QuizResultOut(BaseModel):
    score: float
    total_marks: float
    results: List[QuizResultItem]


# --- Flashcards ---
class FlashcardOut(BaseModel):
    id: str
    front: str
    back: str
    next_review_at: datetime

    class Config:
        from_attributes = True


class FlashcardReviewRequest(BaseModel):
    flashcard_id: str
    quality: int  # 0-5, SM-2 self-rating (0 = total blackout, 5 = perfect recall)


# --- Notes ---
class NotesGenerateRequest(BaseModel):
    document_id: str
    kind: str = "revision"  # revision | last_minute | formula_sheet | definitions | cheat_sheet


class NotesOut(BaseModel):
    id: str
    kind: str
    content_markdown: str

    class Config:
        from_attributes = True


# --- Study planner ---
class StudyPlanRequest(BaseModel):
    goal: str
    exam_date: datetime
    subjects: List[str]
    hours_per_day: float = 3.0


class StudyPlanEntryOut(BaseModel):
    day_number: int
    date: datetime
    subject: str
    topic: str
    task_type: str
    completed: bool

    class Config:
        from_attributes = True


# --- Analytics ---
class PerformanceSummaryOut(BaseModel):
    average_score: float
    total_study_minutes: int
    weak_subjects: List[str]
    strong_subjects: List[str]
