"""
Task planning router: weekly schedules, review queue.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
sys.path.insert(0, r"C:/Users/张洋/Documents/Codex/2026-06-30/ji/learning_agent/backend")

from models import TaskPlan, ReviewItem, init_database
from schemas import TaskPlanCreate, TaskPlanResponse, ToastMessage
from utils import logger
from datetime import date

router = APIRouter(prefix="/api/tasks", tags=["task"])

def get_db():
    engine = init_database()
    s = sessionmaker(bind=engine)
    db = s()
    try: yield db
    finally: db.close()

@router.get("/week/{customer_id}", response_model=ToastMessage)
def get_weekly_tasks(customer_id: int, week_start: str = "", db: Session = Depends(get_db)):
    today = date.today() if not week_start else date.fromisoformat(week_start)
    plan = db.query(TaskPlan).filter(
        TaskPlan.customer_id == customer_id,
        TaskPlan.week_start <= today,
        TaskPlan.week_end >= today
    ).order_by(TaskPlan.created_at.desc()).first()
    if not plan:
        return ToastMessage(data=None, message="No weekly plan found")
    return ToastMessage(data=TaskPlanResponse(
        id=plan.id, customer_id=plan.customer_id,
        week_start=plan.week_start, week_end=plan.week_end,
        total_tasks=plan.total_tasks, completed_tasks=plan.completed_tasks,
        progress_percent=plan.progress_percent,
        task_data=plan.task_data or [], created_at=plan.created_at
    ).model_dump())

@router.post("", response_model=ToastMessage)
def create_task_plan(req: TaskPlanCreate, db: Session = Depends(get_db)):
    completed = sum(1 for t in req.task_data if t.get("status") == "done")
    total = len(req.task_data) or 1
    progress = round(completed / total * 100, 2)
    plan = TaskPlan(customer_id=req.customer_id, week_start=req.week_start,
                    week_end=req.week_end, total_tasks=total,
                    completed_tasks=completed, progress_percent=progress,
                    task_data=req.task_data)
    db.add(plan); db.commit(); db.refresh(plan)
    return ToastMessage(data=TaskPlanResponse(
        id=plan.id, customer_id=plan.customer_id,
        week_start=plan.week_start, week_end=plan.week_end,
        total_tasks=plan.total_tasks, completed_tasks=plan.completed_tasks,
        progress_percent=plan.progress_percent,
        task_data=plan.task_data or [], created_at=plan.created_at
    ).model_dump())

@router.put("/{plan_id}/progress", response_model=ToastMessage)
def update_task_progress(plan_id: int, completed_tasks: int, db: Session = Depends(get_db)):
    plan = db.query(TaskPlan).filter(TaskPlan.id == plan_id).first()
    if not plan: return ToastMessage(code=404, message="Task not found", type="error")
    plan.completed_tasks = completed_tasks
    plan.progress_percent = round(completed_tasks / max(plan.total_tasks, 1) * 100, 2)
    db.commit()
    return ToastMessage(data={"progress_percent": plan.progress_percent})

@router.get("/review-queue/{customer_id}", response_model=ToastMessage)
def get_review_queue(customer_id: int, db: Session = Depends(get_db)):
    items = db.query(ReviewItem).filter(
        ReviewItem.customer_id == customer_id,
        ReviewItem.is_triggered == False
    ).order_by(ReviewItem.risk_level.desc()).all()
    return ToastMessage(data=[{
        "id": i.id, "node_id": i.node_id,
        "days_since_last_review": i.days_since_last_review,
        "risk_level": i.risk_level, "is_triggered": i.is_triggered,
        "last_review_date": i.last_review_date.isoformat() if i.last_review_date else None
    } for i in items])