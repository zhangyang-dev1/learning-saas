"""
Chat router: AI conversation, Taylor expansion data generation.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys, math
sys.path.insert(0, r"C:/Users/张洋/Documents/Codex/2026-06-30/ji/learning_agent/backend")

from models import ChatMessage, MessageRole, init_database
from schemas import ChatRequest, ChatResponse, TaylorExpansionRequest, ToastMessage
from utils import logger

router = APIRouter(prefix="/api/chat", tags=["chat"])

def get_db():
    engine = init_database()
    s = sessionmaker(bind=engine)
    db = s()
    try: yield db
    finally: db.close()

@router.post("", response_model=ToastMessage)
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    user_msg = ChatMessage(customer_id=req.customer_id, role=MessageRole.USER,
                           content=req.content, session_id=req.session_id or "default")
    db.add(user_msg); db.commit()
    reply = _generate_reply(req.content)
    engine_msg = ChatMessage(customer_id=req.customer_id, role=MessageRole.ENGINE,
                             content=reply, session_id=req.session_id or "default")
    db.add(engine_msg); db.commit()
    return ToastMessage(data=ChatResponse(reply=reply, session_id=req.session_id or "default").model_dump())

def _generate_reply(content: str) -> str:
    cl = content.lower()
    if "taylor" in cl or "taylor" in cl:
        return "Taylor expansion approximates functions using polynomials. I can generate visualization data for you."
    if "derivative" in cl or "derivative" in cl:
        return "The derivative represents the rate of change of a function."
    if "function" in cl or "function" in cl:
        return "A function maps inputs to outputs. It is a core concept in mathematics."
    if "practice" in cl or "exercise" in cl:
        return "I can generate practice questions for you. Tell me which topic you want to work on."
    return "I am your AI learning assistant! I can help explain concepts, generate exercises, and analyze learning progress."

@router.get("/history/{customer_id}", response_model=ToastMessage)
def get_chat_history(customer_id: int, session_id: str = "", page: int = 1, page_size: int = 50, db: Session = Depends(get_db)):
    query = db.query(ChatMessage).filter(ChatMessage.customer_id == customer_id)
    if session_id: query = query.filter(ChatMessage.session_id == session_id)
    total = query.count()
    msgs = query.order_by(ChatMessage.created_at).offset((page-1)*page_size).limit(page_size).all()
    return ToastMessage(data={
        "items": [{"id": m.id, "role": m.role.value, "content": m.content[:500],
                   "session_id": m.session_id, "created_at": m.created_at.isoformat()} for m in msgs],
        "total": total, "page": page, "page_size": page_size
    })

@router.post("/taylor-data", response_model=ToastMessage)
def generate_taylor_data(req: TaylorExpansionRequest):
    series = []
    x_min, x_max = req.x_range
    if x_max <= x_min: x_max = x_min + 1.0
    step = (x_max - x_min) / 50
    for i in range(51):
        x = x_min + i * step
        if req.func_name == "sin":
            f_val = math.sin(x)
        elif req.func_name == "cos":
            f_val = math.cos(x)
        elif req.func_name == "exp":
            f_val = math.exp(x)
        else:
            f_val = math.log(x + 1.0) if x > -1 else 0.0
        t_val = 0.0
        for n in range(req.order + 1):
            if req.func_name == "sin":
                if n % 2 == 0: continue
                sign = 1 if (n // 2) % 2 == 0 else -1
                t_val += sign * (x ** n) / math.factorial(n)
            elif req.func_name == "cos":
                if n % 2 != 0: continue
                sign = 1 if (n // 2) % 2 == 0 else -1
                t_val += sign * (x ** n) / math.factorial(n)
            elif req.func_name == "exp":
                t_val += (x ** n) / math.factorial(n)
            else:
                if n > 0:
                    t_val += (-1) ** (n + 1) * (x ** n) / n
        t_val = max(min(t_val, 1e6), -1e6)
        key = "taylor_" + str(req.order)
        series.append({"x": round(x, 4), "f_x": round(f_val, 4), key: round(t_val, 4)})
    return ToastMessage(data={"function": req.func_name, "order": req.order, "data": series})