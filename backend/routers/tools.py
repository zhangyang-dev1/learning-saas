"""
Tools router: OCR, voice, question generation, mindmap, summary.
"""
from fastapi import APIRouter, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys, random
sys.path.insert(0, "C:/Users/张洋/Documents/Codex/2026-06-30/ji/learning_agent/backend")

from models import KnowledgeNode, CustomerKnowledge, init_database
from schemas import QuestionGenerateRequest, ToastMessage
from utils import logger

router = APIRouter(prefix="/api/tools", tags=["tools"])

def get_db():
    engine = init_database()
    s = sessionmaker(bind=engine)
    db = s()
    try: yield db
    finally: db.close()

@router.post("/ocr/upload", response_model=ToastMessage)
async def ocr_upload(file: UploadFile = File(...)):
    content = await file.read()
    logger.info(f"OCR upload: {file.filename}, {len(content)/1024:.1f}KB")
    return ToastMessage(data={"text": "[OCR] Recognized text content", "confidence": 0.95, "detected_areas": []})

@router.post("/voice/upload", response_model=ToastMessage)
async def voice_upload(file: UploadFile = File(...)):
    await file.read()
    return ToastMessage(data={"text": "[Voice] Transcribed text", "duration_seconds": 15.0})

@router.post("/generate-questions", response_model=ToastMessage)
def generate_questions(req: QuestionGenerateRequest, db: Session = Depends(get_db)):
    nodes = db.query(KnowledgeNode).filter(KnowledgeNode.node_id.in_(req.node_ids)).all()
    names = {n.node_id: n.name for n in nodes}
    templates = [
        "Explain {0}:", "What is {0}?", "Describe the concept of {0}.",
        "What are common applications of {0}?",
    ]
    questions = []
    for i in range(req.count):
        nid = random.choice(req.node_ids)
        t = random.choice(templates).format(names.get(nid, nid))
        questions.append({
            "id": f"gen_{i}_{random.randint(100,999)}",
            "node_id": nid,
            "stem": t,
            "difficulty": round(random.uniform(req.difficulty_range[0], req.difficulty_range[1]), 2),
        })
    return ToastMessage(data={"questions": questions, "count": len(questions)})

@router.post("/mindmap", response_model=ToastMessage)
def generate_mindmap(customer_id: int = 0, subject: str = "math_3", db: Session = Depends(get_db)):
    nodes = db.query(KnowledgeNode).filter(KnowledgeNode.subject == subject).all()
    tree = []
    for n in nodes:
        mastery = 0.0
        if customer_id > 0:
            ck = db.query(CustomerKnowledge).filter(
                CustomerKnowledge.customer_id == customer_id,
                CustomerKnowledge.node_id == n.node_id).first()
            if ck: mastery = ck.mastery
        tree.append({"id": n.node_id, "name": n.name, "difficulty": n.difficulty,
                     "mastery": mastery, "prerequisites": n.prerequisites or []})
    return ToastMessage(data={"nodes": tree, "subject": subject})

@router.post("/summary", response_model=ToastMessage)
def generate_summary(customer_id: int, db: Session = Depends(get_db)):
    records = db.query(CustomerKnowledge).filter(CustomerKnowledge.customer_id == customer_id).all()
    mastered = sum(1 for r in records if r.level == "mastered")
    total = len(records) or 1
    text = f"# Learning Summary\n- Mastery: {mastered}/{total} ({mastered/total*100:.1f}%)\n- Keep up the good work!"
    return ToastMessage(data={"summary": text, "format": "markdown"})