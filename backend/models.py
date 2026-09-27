"""
Database ORM Models for Learning SaaS Platform.
"""
import datetime
import os
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, Text, ForeignKey, Enum as SAEnum, JSON, create_engine
from sqlalchemy.orm import declarative_base, relationship
from enum import Enum as PyEnum

Base = declarative_base()

class UserRole(str, PyEnum):
    STUDENT = "student"
    PARENT = "parent"
    ADMIN = "admin"
class SubjectCategory(str, PyEnum):
    MATH_3 = "math_3"
    PHYSICS_3 = "physics_3"
    CHEMISTRY_3 = "chemistry_3"
class KnowledgeLevel(str, PyEnum):
    MASTERED = "mastered"
    INTERMEDIATE = "intermediate"
    HIGH_RISK = "high_risk"
class AlertType(str, PyEnum):
    WEAK_POINT = "weak_point"
    MEMORY_DECAY = "memory_decay"
    ACHIEVEMENT = "achievement"
class MessageRole(str, PyEnum):
    USER = "user"
    ENGINE = "engine"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    display_name = Column(String(64), nullable=False)
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.STUDENT)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False)
    grade = Column(String(32), default="")
    subject = Column(String(32), default="math_3")
    school = Column(String(128), default="")
    phone = Column(String(20), default="")
    email = Column(String(128), default="")
    avatar_url = Column(String(256), default="")
    total_study_minutes = Column(Integer, default=0)
    streak_days = Column(Integer, default=0)
    last_active_date = Column(Date, nullable=True)
    daily_goal_minutes = Column(Integer, default=30)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    knowledge_records = relationship("CustomerKnowledge", back_populates="customer", cascade="all, delete-orphan")
    practice_records = relationship("PracticeRecord", back_populates="customer", cascade="all, delete-orphan")
    task_plans = relationship("TaskPlan", back_populates="customer", cascade="all, delete-orphan")
    review_items = relationship("ReviewItem", back_populates="customer", cascade="all, delete-orphan")

class KnowledgeNode(Base):
    __tablename__ = "knowledge_nodes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    node_id = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    subject = Column(String(32), nullable=False)
    difficulty = Column(Float, default=0.5)
    description = Column(Text, default="")
    prerequisites = Column(JSON, default=list)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class CustomerKnowledge(Base):
    __tablename__ = "customer_knowledge"
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    node_id = Column(String(64), nullable=False)
    mastery = Column(Float, default=0.0)
    level = Column(String(32), default="high_risk")
    total_attempts = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    recent_correct_streak = Column(Integer, default=0)
    recent_error_streak = Column(Integer, default=0)
    last_practice_date = Column(DateTime, nullable=True)
    error_patterns = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    customer = relationship("Customer", back_populates="knowledge_records")

class PracticeRecord(Base):
    __tablename__ = "practice_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    node_id = Column(String(64), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    error_type = Column(String(64), default="")
    difficulty = Column(Float, default=0.5)
    score = Column(Float, default=0.0)
    time_spent_seconds = Column(Integer, default=0)
    practiced_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    customer = relationship("Customer", back_populates="practice_records")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    role = Column(SAEnum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    metadata_json = Column(JSON, default=dict)
    session_id = Column(String(64), default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class TaskPlan(Base):
    __tablename__ = "task_plans"
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    week_start = Column(Date, nullable=False)
    week_end = Column(Date, nullable=False)
    total_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    progress_percent = Column(Float, default=0.0)
    task_data = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    customer = relationship("Customer", back_populates="task_plans")

class ReviewItem(Base):
    __tablename__ = "review_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    node_id = Column(String(64), nullable=False)
    days_since_last_review = Column(Integer, default=0)
    risk_level = Column(String(16), default="normal")
    is_triggered = Column(Boolean, default=False)
    last_review_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    customer = relationship("Customer", back_populates="review_items")

class AlertRule(Base):
    __tablename__ = "alert_rules"
    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_type = Column(SAEnum(AlertType), nullable=False)
    name = Column(String(128), nullable=False)
    condition_json = Column(JSON, default=dict)
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class AlertLog(Base):
    __tablename__ = "alert_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    alert_type = Column(SAEnum(AlertType), nullable=False)
    node_id = Column(String(64), nullable=False)
    message = Column(String(512), nullable=False)
    severity = Column(String(16), default="info")
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

def init_database(database_url="sqlite:///./data/learning_saas.db"):
    os.makedirs(os.path.dirname(database_url.replace("sqlite:///", "")) or ".", exist_ok=True)
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
    return engine
