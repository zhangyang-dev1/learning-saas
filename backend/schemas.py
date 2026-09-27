"""
Pydantic data validation schemas for Learning SaaS Platform.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, Literal
from datetime import date, datetime
from enum import Enum

class UserRole(str, Enum):
    student = "student"; parent = "parent"; admin = "admin"
class SubjectCategory(str, Enum):
    math_3 = "math_3"; physics_3 = "physics_3"; chemistry_3 = "chemistry_3"
class KnowledgeLevel(str, Enum):
    mastered = "mastered"; intermediate = "intermediate"; high_risk = "high_risk"
class AlertType(str, Enum):
    weak_point = "weak_point"; memory_decay = "memory_decay"; achievement = "achievement"
class MessageRole(str, Enum):
    user = "user"; engine = "engine"

class ToastMessage(BaseModel):
    code: int = Field(200, ge=100, le=599)
    message: str = "\u64cd\u4f5c\u6210\u529f"
    type: Literal["success", "error", "warning", "info"] = "success"
    data: Optional[Any] = None

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=64)
    password: str = Field(..., min_length=4, max_length=128)

class LoginResponse(BaseModel):
    access_token: str; token_type: str = "bearer"
    user_id: int; display_name: str; role: UserRole; customer_id: Optional[int] = None

class CustomerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    grade: str = ""; subject: str = "math_3"; school: str = ""
    phone: str = ""; email: str = ""
    daily_goal_minutes: int = Field(30, ge=10, le=480)

class CustomerUpdate(BaseModel):
    name: Optional[str] = None; grade: Optional[str] = None
    subject: Optional[str] = None; school: Optional[str] = None
    phone: Optional[str] = None; email: Optional[str] = None
    daily_goal_minutes: Optional[int] = None

class CustomerResponse(BaseModel):
    id: int; name: str; grade: str; subject: str; school: str
    phone: str; email: str; avatar_url: str; total_study_minutes: int
    streak_days: int; last_active_date: Optional[date] = None
    daily_goal_minutes: int; is_active: bool
    created_at: datetime; updated_at: datetime

class DashboardStats(BaseModel):
    knowledge_mastery_rate: float; total_study_minutes: int
    weak_point_count: int; avg_accuracy: float; week_over_week_growth: float

class KnowledgeNodeResponse(BaseModel):
    id: int; node_id: str; name: str; subject: str
    difficulty: float; description: str; prerequisites: List[str]
    sort_order: int; mastery: Optional[float] = 0.0; level: Optional[str] = "high_risk"

class TaskPlanCreate(BaseModel):
    customer_id: int; week_start: date; week_end: date
    task_data: List[Dict[str, Any]] = []

class TaskPlanResponse(BaseModel):
    id: int; customer_id: int; week_start: date; week_end: date
    total_tasks: int; completed_tasks: int; progress_percent: float
    task_data: List[Dict[str, Any]]; created_at: datetime

class ChatRequest(BaseModel):
    customer_id: int; content: str = Field(..., min_length=1, max_length=5000)
    session_id: str = ""

class ChatResponse(BaseModel):
    reply: str; session_id: str; engine_trace: Optional[List[Dict]] = None

class ExportRequest(BaseModel):
    customer_ids: Optional[List[int]] = None; date_from: Optional[date] = None
    date_to: Optional[date] = None; format_type: str = "pdf"

class AlertLogResponse(BaseModel):
    id: int; customer_id: int; alert_type: str; node_id: str
    message: str; severity: str; is_read: bool; created_at: datetime

class TaylorExpansionRequest(BaseModel):
    func_name: str = "sin"; center: float = 0.0; order: int = Field(4, ge=1, le=10)
    x_range: List[float] = [0.0, 6.28]

class QuestionGenerateRequest(BaseModel):
    customer_id: int; node_ids: List[str]; count: int = Field(5, ge=1, le=20)
    difficulty_range: List[float] = [0.3, 0.8]

class MemoryDecayCheckRequest(BaseModel):
    customer_id: int; threshold_days: int = Field(5, ge=1, le=30)

class MarkKnowledgeRequest(BaseModel):
    customer_id: int; node_id: str; level: KnowledgeLevel; note: str = ""

class ReviewItemCreate(BaseModel):
    customer_id: int; node_id: str; risk_level: str = "normal"

class PaginatedResponse(BaseModel):
    items: List[Any]; total: int; page: int; page_size: int; total_pages: int