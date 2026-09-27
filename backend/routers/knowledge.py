"""Knowledge graph management router."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
sys.path.insert(0, r"C:\Users\张洋\Documents\Codex\2026-06-30\ji\learning_agent\backend")

from models import KnowledgeNode, CustomerKnowledge, Customer, init_database
from schemas import KnowledgeNodeResponse, MarkKnowledgeRequest, ToastMessage
from utils import logger
from datetime import datetime

router = APIRouter(prefix="/api/knowledge", tags=["\u77e5\u8bc6\u56fe\u8c31"])

def get_db():
    engine = init_database()
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try: yield db
    finally: db.close()

@router.get("/nodes", response_model=ToastMessage)
def list_knowledge_nodes(subject: str = "", customer_id: int = 0, db: Session = Depends(get_db)):
    """\u67e5\u8be2\u77e5\u8bc6\u70b9\u6807\u7b7e"""
    query = db.query(KnowledgeNode)
    if subject:
        query = query.filter(KnowledgeNode.subject == subject)
    nodes = query.order_by(KnowledgeNode.sort_order).all()
    result = []
    for n in nodes:
        mastery = 0.0
        level = "high_risk"
        if customer_id > 0:
            ck = db.query(CustomerKnowledge).filter(
                CustomerKnowledge.customer_id == customer_id,
                CustomerKnowledge.node_id == n.node_id
            ).first()
            if ck:
                mastery = ck.mastery
                level = ck.level
        result.append(KnowledgeNodeResponse(
            id=n.id, node_id=n.node_id, name=n.name, subject=n.subject,
            difficulty=n.difficulty, description=n.description or "",
            prerequisites=n.prerequisites or [], sort_order=n.sort_order or 0,
            mastery=mastery, level=level
        ).model_dump())
    return ToastMessage(data=result)

@router.post("/mark", response_model=ToastMessage)
def mark_knowledge_level(req: MarkKnowledgeRequest, db: Session = Depends(get_db)):
    """\u6807\u8bb0\u77e5\u8bc6\u70b9\u638c\u63e1\u72b6\u6001"""
    ck = db.query(CustomerKnowledge).filter(
        CustomerKnowledge.customer_id == req.customer_id,
        CustomerKnowledge.node_id == req.node_id
    ).first()
    if not ck:
        ck = CustomerKnowledge(customer_id=req.customer_id, node_id=req.node_id)
        db.add(ck)
    ck.level = req.level.value
    ck.mastery = 0.9 if req.level.value == "mastered" else (0.5 if req.level.value == "intermediate" else 0.2)
    ck.updated_at = datetime.utcnow()
    db.commit()
    return ToastMessage(message=f"\u5df2\u66f4\u65b0'{req.node_id}'\u4e3a{req.level.value}")