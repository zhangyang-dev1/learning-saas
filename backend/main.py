
"""
主程序入口 — 智能学情分析 SaaS 管理平台

启动命令：
    cd backend && python main.py
    # 或 uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import init_database, User, UserRole, Customer, KnowledgeNode, CustomerKnowledge,     ReviewItem, AlertRule, AlertType, Base
from utils import hash_password, logger
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from datetime import datetime, date
import random

# ─── 导入路由 ───
from routers.auth import router as auth_router
from routers.customer import router as customer_router
from routers.dashboard import router as dashboard_router
from routers.knowledge import router as knowledge_router
from routers.task import router as task_router
from routers.chat import router as chat_router
from routers.tools import router as tools_router
from routers.alert import router as alert_router
from routers.report import router as report_router

app = FastAPI(
    title="智能学情分析 SaaS 管理平台",
    description="Learning Analytics SaaS Platform - 数据驱动个性化教学管理",
    version="1.0.0"
)

# ─── CORS ───
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── 注册路由 ───
app.include_router(auth_router)
app.include_router(customer_router)
app.include_router(dashboard_router)
app.include_router(knowledge_router)
app.include_router(task_router)
app.include_router(chat_router)
app.include_router(tools_router)
app.include_router(alert_router)
app.include_router(report_router)


@app.on_event("startup")
def startup():
    """启动时初始化数据库并填充种子数据"""
    db_url = os.environ.get("DATABASE_URL", "sqlite:///./data/learning_saas.db")
    engine = init_database(db_url)
    logger.info(f"Database initialized: {db_url}")
    _seed_data(engine)


def _seed_data(engine):
    """填充初始种子数据（仅当数据库为空时）"""
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            return

        # 1. 创建客户
        c1 = Customer(name="小李", grade="高三", subject="math_3", school="第一中学",
                      total_study_minutes=1280, streak_days=15, daily_goal_minutes=45,
                      last_active_date=date.today())
        c2 = Customer(name="小王", grade="高三", subject="physics_3", school="实验中学",
                      total_study_minutes=860, streak_days=8, daily_goal_minutes=30,
                      last_active_date=date.today())
        db.add_all([c1, c2])
        db.flush()

        # 2. 创建用户
        admin = User(username="admin", password_hash=hash_password("admin123"),
                     display_name="运营管理员", role=UserRole.ADMIN)
        teacher = User(username="teacher", password_hash=hash_password("teacher123"),
                       display_name="张老师", role=UserRole.ADMIN)
        parent = User(username="parent", password_hash=hash_password("parent123"),
                      display_name="小李家长", role=UserRole.PARENT, customer_id=c1.id)
        student = User(username="student", password_hash=hash_password("student123"),
                       display_name="小李同学", role=UserRole.STUDENT, customer_id=c1.id)
        db.add_all([admin, teacher, parent, student])

        # 3. 创建知识点（高三数学）
        math_nodes = [
            ("m_01", "函数定义与性质", 0.3, []),
            ("m_02", "函数单调性", 0.4, ["m_01"]),
            ("m_03", "函数奇偶性", 0.4, ["m_01"]),
            ("m_04", "指数与对数", 0.5, ["m_01"]),
            ("m_05", "三角函数概念", 0.5, ["m_01"]),
            ("m_06", "三角恒等变换", 0.6, ["m_05"]),
            ("m_07", "导数基础", 0.6, ["m_02", "m_03"]),
            ("m_08", "导数的应用", 0.7, ["m_07"]),
            ("m_09", "数列", 0.5, []),
            ("m_10", "数列求和", 0.6, ["m_09"]),
            ("m_11", "向量运算", 0.5, []),
            ("m_12", "空间几何", 0.6, []),
            ("m_13", "概率计算", 0.5, []),
            ("m_14", "统计分布", 0.6, ["m_13"]),
            ("m_15", "圆锥曲线", 0.7, []),
            ("m_16", "导数与函数综合", 0.8, ["m_08", "m_10"]),
        ]
        for nid, name, diff, prereqs in math_nodes:
            db.add(KnowledgeNode(node_id=nid, name=name, subject="math_3",
                                 difficulty=diff, prerequisites=prereqs, sort_order=float(diff)))

        physics_nodes = [
            ("p_01", "力学基础", 0.3, []),
            ("p_02", "牛顿定律", 0.4, ["p_01"]),
            ("p_03", "功与能", 0.5, ["p_02"]),
            ("p_04", "动量守恒", 0.6, ["p_03"]),
            ("p_05", "电场", 0.5, []),
            ("p_06", "磁场", 0.6, ["p_05"]),
            ("p_07", "电磁感应", 0.7, ["p_06"]),
            ("p_08", "振动与波", 0.5, []),
        ]
        for nid, name, diff, prereqs in physics_nodes:
            db.add(KnowledgeNode(node_id=nid, name=name, subject="physics_3",
                                 difficulty=diff, prerequisites=prereqs, sort_order=float(diff)))

        # 4. 创建客户知识点掌握记录
        math_all = [n[0] for n in math_nodes]
        for cid in [c1.id, c2.id]:
            for i, nid in enumerate(math_all):
                mastery = round(random.uniform(0.15, 0.95), 2)
                level = "mastered" if mastery >= 0.8 else ("intermediate" if mastery >= 0.5 else "high_risk")
                db.add(CustomerKnowledge(
                    customer_id=cid, node_id=nid,
                    mastery=mastery, level=level,
                    total_attempts=random.randint(3, 20),
                    correct_count=random.randint(1, 18),
                    last_practice_date=datetime.utcnow()
                ))

        # 5. 创建复习项目
        for cid in [c1.id, c2.id]:
            db.add(ReviewItem(customer_id=cid, node_id="m_02",
                              days_since_last_review=6, risk_level="warning", is_triggered=True,
                              last_review_date=datetime.utcnow()))
            db.add(ReviewItem(customer_id=cid, node_id="m_08",
                              days_since_last_review=2, risk_level="normal",
                              last_review_date=datetime.utcnow()))

        # 6. 创建预警规则
        db.add(AlertRule(alert_type=AlertType.WEAK_POINT, name="高危薄弱知识点自动判定",
                         condition_json={"consecutive_errors": 3, "max_accuracy": 0.5}))
        db.add(AlertRule(alert_type=AlertType.ACHIEVEMENT, name="知识点掌握达标判定",
                         condition_json={"consecutive_correct": 5, "min_accuracy": 0.9}))
        db.add(AlertRule(alert_type=AlertType.MEMORY_DECAY, name="记忆衰减复习提醒",
                         condition_json={"review_interval_days": 5}))

        db.commit()
        logger.info("Seed data created: users=4, customers=2, knowledge_nodes=24, rules=3")
    except Exception as e:
        db.rollback()
        logger.warning(f"Seed data skipped: {e}")
    finally:
        db.close()


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "learning-saas", "version": "1.0.0"}


@app.get("/api/seed/status")
def seed_status():
    """查询系统数据状态"""
    engine = init_database()
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        return {
            "users": db.query(User).count(),
            "customers": db.query(Customer).count(),
            "knowledge_nodes": db.query(KnowledgeNode).count(),
            "reviews": db.query(ReviewItem).count(),
            "alert_rules": db.query(AlertRule).count(),
        }
    finally:
        db.close()


# ─── 直接运行 ───
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"智能学情分析 SaaS 管理平台")
    print(f"API: http://localhost:{port}")
    print(f"Docs: http://localhost:{port}/docs")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
