"""
Alert router: risk detection, memory decay check.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
sys.path.insert(0, "C:/Users/张洋/Documents/Codex/2026-06-30/ji/learning_agent/backend")

from models import AlertLog, AlertType, CustomerKnowledge, PracticeRecord, ReviewItem, init_database
from schemas import AlertLogResponse, AlertCheckResult, MemoryDecayCheckRequest, ToastMessage
from utils import is_high_risk, is_mastered, memory_decay_risk, logger
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/alert", tags=["alert"])

def get_db():
    engine = init_database()
    s = sessionmaker(bind=engine)
    db = s()
    try: yield db
    finally: db.close()

@router.post("/check/{customer_id}", response_model=ToastMessage)
def check_alerts(customer_id: int, db: Session = Depends(get_db)):
    alerts = []
    records = db.query(CustomerKnowledge).filter(CustomerKnowledge.customer_id == customer_id).all()
    for r in records:
        recent = db.query(PracticeRecord).filter(
            PracticeRecord.customer_id == customer_id,
            PracticeRecord.node_id == r.node_id
        ).order_by(PracticeRecord.practiced_at.desc()).limit(5).all()
        results = [p.is_correct for p in recent]
        if is_high_risk(results) and r.level != "high_risk":
            r.level = "high_risk"
            log = AlertLog(customer_id=customer_id, alert_type=AlertType.WEAK_POINT,
                           node_id=r.node_id, message=f"High risk: {r.node_id} accuracy < 50% for 3 attempts",
                           severity="critical")
            db.add(log); alerts.append(log)
        if is_mastered(results) and r.level != "mastered":
            r.level = "mastered"
            log = AlertLog(customer_id=customer_id, alert_type=AlertType.ACHIEVEMENT,
                           node_id=r.node_id, message=f"Mastered: {r.node_id} accuracy >= 90% for 5 attempts",
                           severity="info")
            db.add(log); alerts.append(log)
    review_items = db.query(ReviewItem).filter(ReviewItem.customer_id == customer_id).all()
    for ri in review_items:
        if ri.last_review_date:
            days = (datetime.utcnow() - ri.last_review_date).days
            ri.days_since_last_review = days
            if memory_decay_risk(days, 5) and not ri.is_triggered:
                ri.is_triggered = True
                log = AlertLog(customer_id=customer_id, alert_type=AlertType.MEMORY_DECAY,
                               node_id=ri.node_id, message=f"Memory decay: {ri.node_id} not reviewed for {days} days",
                               severity="warning")
                db.add(log); alerts.append(log)
    db.commit()
    return ToastMessage(data=AlertCheckResult(
        triggered=len(alerts) > 0,
        alerts=[AlertLogResponse(
            id=a.id, customer_id=a.customer_id, alert_type=a.alert_type.value,
            node_id=a.node_id, message=a.message, severity=a.severity,
            is_read=a.is_read, created_at=a.created_at
        ) for a in alerts]
    ).model_dump())

@router.get("/logs/{customer_id}", response_model=ToastMessage)
def get_alert_logs(customer_id: int, unread_only: bool = False, db: Session = Depends(get_db)):
    query = db.query(AlertLog).filter(AlertLog.customer_id == customer_id)
    if unread_only: query = query.filter(AlertLog.is_read == False)
    logs = query.order_by(AlertLog.created_at.desc()).limit(50).all()
    return ToastMessage(data=[AlertLogResponse(
        id=l.id, customer_id=l.customer_id, alert_type=l.alert_type.value,
        node_id=l.node_id, message=l.message, severity=l.severity,
        is_read=l.is_read, created_at=l.created_at
    ).model_dump() for l in logs])

@router.post("/check-memory-decay", response_model=ToastMessage)
def check_memory_decay(req: MemoryDecayCheckRequest, db: Session = Depends(get_db)):
    items = db.query(ReviewItem).filter(ReviewItem.customer_id == req.customer_id).all()
    result = []
    for ri in items:
        if ri.last_review_date:
            days = (datetime.utcnow() - ri.last_review_date).days
            if days >= req.threshold_days:
                result.append({"node_id": ri.node_id, "days_since_review": days, "trigger_review": True})
    return ToastMessage(data={"items": result, "triggered_count": len(result)})