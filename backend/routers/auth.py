"""Authentication router: JWT login, role switch, subject switch."""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
sys.path.insert(0, r"C:\Users\张洋\Documents\Codex\2026-06-30\ji\learning_agent\backend")

from models import User, UserRole, init_database
from schemas import LoginRequest, LoginResponse, ToastMessage
from utils import hash_password, verify_password, create_access_token, decode_access_token, logger

router = APIRouter(prefix="/api/auth", tags=["\u8ba4\u8bc1\u6a21\u5757"])

def get_db():
    engine = init_database()
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/login", response_model=ToastMessage)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """JWT\u767b\u5f55\u63a5\u53e3"""
    try:
        user = db.query(User).filter(User.username == req.username).first()
        if not user or not verify_password(req.password, user.password_hash):
            logger.warning(f"\u767b\u5f55\u5931\u8d25: {req.username}")
            return ToastMessage(code=401, message="\u7528\u6237\u540d\u6216\u5bc6\u7801\u9519\u8bef", type="error")
        token = create_access_token({
            "user_id": user.id,
            "role": user.role.value,
            "customer_id": user.customer_id,
            "username": user.username
        })
        logger.info(f"\u7528\u6237\u767b\u5f55\u6210\u529f: {user.username}")
        return ToastMessage(data=LoginResponse(
            access_token=token, user_id=user.id,
            display_name=user.display_name, role=user.role,
            customer_id=user.customer_id
        ).model_dump())
    except Exception as e:
        logger.error(f"\u767b\u5f55\u5f02\u5e38: {e}")
        return ToastMessage(code=500, message="\u670d\u52a1\u5668\u5185\u90e8\u9519\u8bef", type="error")

@router.post("/switch-role", response_model=ToastMessage)
def switch_role(target_role: str, authorization: str = Header(None), db: Session = Depends(get_db)):
    """\u89d2\u8272\u5207\u6362\u63a5\u53e3"""
    token_data = decode_access_token(authorization.replace("Bearer ", "")) if authorization else None
    if not token_data:
        return ToastMessage(code=401, message="\u8eab\u4efd\u9a8c\u8bc1\u5931\u8d25", type="error")
    if target_role not in [r.value for r in UserRole]:
        return ToastMessage(code=400, message=f"\u65e0\u6548\u7684\u89d2\u8272: {target_role}", type="warning")
    user = db.query(User).filter(User.id == token_data["user_id"]).first()
    if user:
        user.role = UserRole(target_role)
        db.commit()
    new_token = create_access_token({**token_data, "role": target_role})
    return ToastMessage(data={"access_token": new_token, "role": target_role})

@router.post("/switch-subject", response_model=ToastMessage)
def switch_subject(subject: str, customer_id: int, authorization: str = Header(None)):
    """\u5b66\u79d1\u6a21\u5757\u5207\u6362"""
    valid_subjects = ["math_3", "physics_3", "chemistry_3"]
    if subject not in valid_subjects:
        return ToastMessage(code=400, message="\u65e0\u6548\u5b66\u79d1", type="warning")
    return ToastMessage(data={"subject": subject})

@router.get("/me", response_model=ToastMessage)
def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    """\u83b7\u53d6\u5f53\u524d\u7528\u6237\u4fe1\u606f"""
    token_data = decode_access_token(authorization.replace("Bearer ", "")) if authorization else None
    if not token_data:
        return ToastMessage(code=401, message="\u672a\u8ba4\u8bc1", type="error")
    user = db.query(User).filter(User.id == token_data["user_id"]).first()
    if not user:
        return ToastMessage(code=404, message="\u7528\u6237\u4e0d\u5b58\u5728", type="error")
    return ToastMessage(data={
        "id": user.id, "username": user.username, "display_name": user.display_name,
        "role": user.role.value, "customer_id": user.customer_id
    })