import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer,
    String, Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class Subject(str, enum.Enum):
    physics = "physics"
    chemistry = "chemistry"
    maths = "maths"
    biology = "biology"
    english = "english"
    other = "other"


class QuestionType(str, enum.Enum):
    mcq = "mcq"
    short_answer = "short_answer"
    long_answer = "long_answer"
    true_false = "true_false"
    fill_blank = "fill_blank"
    hots = "hots"


class Difficulty(str, enum.Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(String, default="student")  # student | teacher
    created_at = Column(DateTime, default=datetime.utcnow)

    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="owner", cascade="all, delete-orphan")
    flashcards = relationship("Flashcard", back_populates="owner", cascade="all, delete-orphan")
    performance_logs = relationship("PerformanceLog", back_populates="user", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    owner_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    subject = Column(Enum(Subject), default=Subject.other)
    file_path = Column(String, nullable=False)
    page_count = Column(Integer, default=0)
    is_ocr = Column(Boolean, default=False)
    vector_collection = Column(String, nullable=True)  # chroma collection name
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="documents")
    chat_messages = relationship("ChatMessage", back_populates="document", cascade="all, delete-orphan")
    flashcards = relationship("Flashcard", back_populates="document", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="document", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    document_id = Column(UUID(as_uuid=False), ForeignKey("documents.id"), nullable=False)
    role = Column(String, nullable=False)  # user | assistant
    content = Column(Text, nullable=False)
    source_pages = Column(String, nullable=True)  # comma separated page numbers cited
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="chat_messages")


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    owner_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    document_id = Column(UUID(as_uuid=False), ForeignKey("documents.id"), nullable=True)
    title = Column(String, nullable=False)
    difficulty = Column(Enum(Difficulty), default=Difficulty.medium)
    exam_level = Column(String, nullable=True)  # jee | neet | general
    negative_marking = Column(Boolean, default=False)
    time_limit_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="quizzes")
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    quiz_id = Column(UUID(as_uuid=False), ForeignKey("quizzes.id"), nullable=False)
    type = Column(Enum(QuestionType), default=QuestionType.mcq)
    question_text = Column(Text, nullable=False)
    options = Column(Text, nullable=True)  # JSON-encoded list for MCQ
    correct_answer = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    source_page = Column(Integer, nullable=True)

    quiz = relationship("Quiz", back_populates="questions")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    quiz_id = Column(UUID(as_uuid=False), ForeignKey("quizzes.id"), nullable=False)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    score = Column(Float, default=0)
    total_marks = Column(Float, default=0)
    time_taken_seconds = Column(Integer, nullable=True)
    answers_json = Column(Text, nullable=True)  # JSON-encoded {question_id: answer}
    created_at = Column(DateTime, default=datetime.utcnow)

    quiz = relationship("Quiz", back_populates="attempts")


class Flashcard(Base):
    __tablename__ = "flashcards"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    owner_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    document_id = Column(UUID(as_uuid=False), ForeignKey("documents.id"), nullable=True)
    front = Column(Text, nullable=False)
    back = Column(Text, nullable=False)
    # spaced repetition (SM-2 lite)
    interval_days = Column(Integer, default=1)
    ease_factor = Column(Float, default=2.5)
    next_review_at = Column(DateTime, default=datetime.utcnow)
    last_reviewed_at = Column(DateTime, nullable=True)

    owner = relationship("User", back_populates="flashcards")
    document = relationship("Document", back_populates="flashcards")


class Note(Base):
    __tablename__ = "notes"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    document_id = Column(UUID(as_uuid=False), ForeignKey("documents.id"), nullable=False)
    kind = Column(String, nullable=False)  # revision | last_minute | formula_sheet | definitions | cheat_sheet
    content_markdown = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="notes")


class StudyPlanEntry(Base):
    __tablename__ = "study_plan_entries"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    goal = Column(String, nullable=False)  # e.g. "JEE in 100 days"
    day_number = Column(Integer, nullable=False)
    date = Column(DateTime, nullable=False)
    subject = Column(Enum(Subject), default=Subject.other)
    topic = Column(String, nullable=False)
    task_type = Column(String, default="study")  # study | revise | quiz | mock_test
    completed = Column(Boolean, default=False)


class PerformanceLog(Base):
    __tablename__ = "performance_logs"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    subject = Column(Enum(Subject), default=Subject.other)
    chapter = Column(String, nullable=True)
    activity_type = Column(String, nullable=False)  # quiz | mock_test | flashcard_review
    score_percent = Column(Float, nullable=True)
    study_time_minutes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="performance_logs")
