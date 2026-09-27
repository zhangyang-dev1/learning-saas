"""
Report router: CSV export.
"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys, io, csv
sys.path.insert(0, "C:/Users/张洋/Documents/Codex/2026-06-30/ji/learning_agent/backend")

from models import Customer, CustomerKnowledge, init_database
from schemas import ExportRequest, ToastMessage
from utils import logger

router = APIRouter(prefix="/api/report", tags=["report"])

def get_db():
    engine = init_database()
    s = sessionmaker(bind=engine)
    db = s()
    try: yield db
    finally: db.close()

@router.post("/export")
def export_data(req: ExportRequest, db: Session = Depends(get_db)):
    query = db.query(Customer).filter(Customer.is_active == True)
    if req.customer_ids:
        query = query.filter(Customer.id.in_(req.customer_ids))
    customers = query.all()
    logger.info(f"Exporting {len(customers)} customers as {req.format_type}")
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Name", "Grade", "Subject", "Study Minutes", "Streak Days", "Mastery Rate"])
    for c in customers:
        records = db.query(CustomerKnowledge).filter(CustomerKnowledge.customer_id == c.id).all()
        mastered = sum(1 for r in records if r.level == "mastered")
        total = len(records) or 1
        writer.writerow([c.id, c.name, c.grade, c.subject, c.total_study_minutes, c.streak_days, f"{mastered/total*100:.1f}%"])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=learning_report.csv"}
    )