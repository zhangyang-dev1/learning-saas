"""Customer CRUD router."""
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
sys.path.insert(0, r"C:\Users\张洋\Documents\Codex\2026-06-30\ji\learning_agent\backend")

from models import Customer, CustomerKnowledge, User, init_database
from schemas import CustomerCreate, CustomerUpdate, CustomerResponse, ToastMessage
from utils import decode_access_token, logger

router = APIRouter(prefix="/api/customers", tags=["\u5ba2\u6237\u6863\u6848"])

def get_db():
    engine = init_database()
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try: yield db
    finally: db.close()

@router.get("", response_model=ToastMessage)
def list_customers(page: int = 1, page_size: int = 20, authorization: str = Header(None), db: Session = Depends(get_db)):
    """\u5ba2\u6237\u5217\u8868\u67e5\u8be2"""
    total = db.query(Customer).count()
    customers = db.query(Customer).offset((page-1)*page_size).limit(page_size).all()
    return ToastMessage(data={
        "items": [{"id": c.id, "name": c.name, "grade": c.grade, "subject": c.subject,
                    "school": c.school, "total_study_minutes": c.total_study_minutes,
                    "streak_days": c.streak_days, "is_active": c.is_active,
                    "created_at": c.created_at.isoformat() if c.created_at else None} for c in customers],
        "total": total, "page": page, "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    })

@router.get("/{customer_id}", response_model=ToastMessage)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    """\u83b7\u53d6\u5355\u4e2a\u5ba2\u6237\u8be6\u60c5"""
    c = db.query(Customer).filter(Customer.id == customer_id).first()
    if not c:
        return ToastMessage(code=404, message="\u5ba2\u6237\u4e0d\u5b58\u5728", type="error")
    return ToastMessage(data=CustomerResponse(
        id=c.id, name=c.name, grade=c.grade or "", subject=c.subject or "",
        school=c.school or "", phone=c.phone or "", email=c.email or "",
        avatar_url=c.avatar_url or "", total_study_minutes=c.total_study_minutes or 0,
        streak_days=c.streak_days or 0, last_active_date=c.last_active_date,
        daily_goal_minutes=c.daily_goal_minutes or 30, is_active=c.is_active,
        created_at=c.created_at, updated_at=c.updated_at
    ).model_dump())

@router.post("", response_model=ToastMessage)
def create_customer(req: CustomerCreate, authorization: str = Header(None), db: Session = Depends(get_db)):
    """\u521b\u5efa\u5ba2\u6237\u6863\u6848"""
    try:
        c = Customer(name=req.name, grade=req.grade, subject=req.subject, school=req.school,
                     phone=req.phone, email=req.email, daily_goal_minutes=req.daily_goal_minutes)
        db.add(c)
        db.commit()
        db.refresh(c)
        logger.info(f"\u521b\u5efa\u5ba2\u6237: {c.name} (id={c.id})")
        return ToastMessage(data=CustomerResponse(
            id=c.id, name=c.name, grade=c.grade or "", subject=c.subject or "",
            school=c.school or "", phone=c.phone or "", email=c.email or "",
            avatar_url=c.avatar_url or "", total_study_minutes=0,
            streak_days=0, last_active_date=None,
            daily_goal_minutes=c.daily_goal_minutes, is_active=True,
            created_at=c.created_at, updated_at=c.updated_at
        ).model_dump())
    except Exception as e:
        logger.error(f"\u521b\u5efa\u5ba2\u6237\u5f02\u5e38: {e}")
        return ToastMessage(code=500, message=str(e), type="error")

@router.put("/{customer_id}", response_model=ToastMessage)
def update_customer(customer_id: int, req: CustomerUpdate, db: Session = Depends(get_db)):
    """\u66f4\u65b0\u5ba2\u6237\u4fe1\u606f"""
    c = db.query(Customer).filter(Customer.id == customer_id).first()
    if not c:
        return ToastMessage(code=404, message="\u5ba2\u6237\u4e0d\u5b58\u5728", type="error")
    update_data = req.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(c, k, v)
    db.commit()
    return ToastMessage(message="\u66f4\u65b0\u6210\u529f")

@router.delete("/{customer_id}", response_model=ToastMessage)
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    """\u5220\u9664\u5ba2\u6237"""
    c = db.query(Customer).filter(Customer.id == customer_id).first()
    if not c:
        return ToastMessage(code=404, message="\u5ba2\u6237\u4e0d\u5b58\u5728", type="error")
    c.is_active = False
    db.commit()
    return ToastMessage(message="\u5df2\u5173\u95ed\u5ba2\u6237\u8d26\u6237")