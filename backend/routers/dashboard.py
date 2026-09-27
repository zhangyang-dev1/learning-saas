"""Dashboard router: real-time analytics."""
from fastapi import APIRouter
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
import sys
sys.path.insert(0, r"C:\Users\张洋\Documents\Codex\2026-06-30\ji\learning_agent\backend")

from models import Customer, CustomerKnowledge, PracticeRecord, init_database
from schemas import DashboardStats, ToastMessage
from utils import calc_week_over_week, calc_accuracy, logger
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/dashboard", tags=["\u5b9e\u65f6\u6570\u636e\u770b\u677f"])

def get_db():
    engine = init_database()
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try: yield db
    finally: db.close()

@router.get("/stats/{customer_id}", response_model=ToastMessage)
def get_dashboard_stats(customer_id: int, db: Session = Depends(get_db)):
    """\u83b7\u53d6\u5ba2\u6237\u770b\u677f\u7edf\u8ba1"""
    c = db.query(Customer).filter(Customer.id == customer_id).first()
    if not c:
        return ToastMessage(code=404, message="\u5ba2\u6237\u4e0d\u5b58\u5728", type="error")
    records = db.query(CustomerKnowledge).filter(CustomerKnowledge.customer_id == customer_id).all()
    total_nodes = len(records) or 1
    mastered = sum(1 for r in records if r.level == "mastered")
    high_risk = sum(1 for r in records if r.level == "high_risk")
    mastery_rate = round(mastered / total_nodes, 4)

    # \u6b63\u786e\u7387
    practices = db.query(PracticeRecord).filter(PracticeRecord.customer_id == customer_id).all()
    total_p = len(practices)
    correct_p = sum(1 for p in practices if p.is_correct)
    avg_acc = calc_accuracy(correct_p, total_p) if total_p > 0 else 0.0

    # \u5468\u73af\u6bd4
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    current_week = sum(1 for p in practices if p.practiced_at and p.practiced_at >= week_ago)
    prev_week = sum(1 for p in practices if p.practiced_at and week_ago - timedelta(days=7) <= p.practiced_at < week_ago)
    wow = calc_week_over_week(float(current_week), float(prev_week))

    return ToastMessage(data=DashboardStats(
        knowledge_mastery_rate=mastery_rate,
        total_study_minutes=c.total_study_minutes or 0,
        weak_point_count=high_risk,
        avg_accuracy=avg_acc,
        week_over_week_growth=wow
    ).model_dump())

@router.get("/study-time/{customer_id}", response_model=ToastMessage)
def get_study_time(customer_id: int, days: int = 7, db: Session = Depends(get_db)):
    """\u5468\u5b66\u4e60\u65f6\u957f\u7edf\u8ba1"""
    practices = db.query(PracticeRecord).filter(
        PracticeRecord.customer_id == customer_id,
        PracticeRecord.practiced_at >= datetime.utcnow() - timedelta(days=days)
    ).all()
    daily = {}
    for p in practices:
        day = p.practiced_at.strftime("%Y-%m-%d")
        daily[day] = daily.get(day, 0) + (p.time_spent_seconds or 0) // 60
    return ToastMessage(data={
        "daily_data": [{"date": d, "minutes": m} for d, m in sorted(daily.items())],
        "total_minutes": sum(daily.values())
    })

@router.get("/accuracy-trend/{customer_id}", response_model=ToastMessage)
def get_accuracy_trend(customer_id: int, days: int = 30, db: Session = Depends(get_db)):
    """\u6b63\u786e\u7387\u8d8b\u52bf"""
    practices = db.query(PracticeRecord).filter(
        PracticeRecord.customer_id == customer_id,
        PracticeRecord.practiced_at >= datetime.utcnow() - timedelta(days=days)
    ).order_by(PracticeRecord.practiced_at).all()
    daily = {}
    for p in practices:
        day = p.practiced_at.strftime("%Y-%m-%d")
        if day not in daily:
            daily[day] = {"correct": 0, "total": 0}
        daily[day]["total"] += 1
        if p.is_correct:
            daily[day]["correct"] += 1
    trend = [{"date": d, "accuracy": round(v["correct"]/v["total"], 4) if v["total"]>0 else 0}
             for d, v in sorted(daily.items())]
    return ToastMessage(data={"trend": trend, "period": f"{days}\u5929"})