from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, text
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.sql import func
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")
engine = create_engine(DB_URL, pool_recycle=3600, echo=False)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()


# --- ORM 模型 ---

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    nickname = Column(String(50))
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="user")

    # 级联删除：删除用户时自动删除其所有对话
    sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(String(50), primary_key=True)
    title = Column(String(255), default="新对话")
    user_id = Column(Integer, ForeignKey("users.id"))
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="sessions")
    # 级联删除：删除会话时自动删除所有消息
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), ForeignKey("chat_sessions.id"))
    role = Column(String(20))
    content = Column(Text)
    created_at = Column(DateTime, default=func.now())

    session = relationship("ChatSession", back_populates="messages")


# 密码加密工具
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")


# --- 登录与用户管理 ---

def get_user_by_username(username: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user:
            return {
                "id": user.id,
                "username": user.username,
                "nickname": user.nickname,
                "password_hash": user.password_hash,
                "role": user.role
            }
        return None
    finally:
        db.close()


def insert_new_user(username, nickname, password_hash, role="user"):
    db = SessionLocal()
    try:
        new_user = User(username=username, nickname=nickname, password_hash=password_hash, role=role)
        db.add(new_user)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        return False
    finally:
        db.close()


# --- 对话功能 ---

def create_session_if_not_exists(session_id: str, user_id: int, title: str = "新对话"):
    db = SessionLocal()
    try:
        exists = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not exists:
            new_session = ChatSession(id=session_id, user_id=user_id, title=title[:50])
            db.add(new_session)
            db.commit()
    finally:
        db.close()


def save_message(session_id: str, role: str, content: str):
    db = SessionLocal()
    try:
        new_msg = ChatMessage(session_id=session_id, role=role, content=content)
        db.add(new_msg)
        # 手动触发表的 updated_at 更新（或者在 DB 层设置触发器）
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if session:
            session.updated_at = func.now()
        db.commit()
    finally:
        db.close()


def get_chat_history(session_id: str):
    db = SessionLocal()
    try:
        messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(
            ChatMessage.created_at.asc()).all()
        return [{"role": m.role, "content": m.content} for m in messages]
    finally:
        db.close()


def get_all_sessions(user_id: int):
    db = SessionLocal()
    try:
        sessions = db.query(ChatSession).filter(ChatSession.user_id == user_id).order_by(
            ChatSession.updated_at.desc()).all()
        return [{"id": s.id, "title": s.title, "updated_at": s.updated_at} for s in sessions]
    finally:
        db.close()


def delete_chat_session(session_id: str):
    db = SessionLocal()
    try:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if session:
            db.delete(session)  # 级联删除会自动处理 messages
            db.commit()
            return True
        return False
    finally:
        db.close()


# --- 管理员功能 ---

def get_all_users(search_query: str = None):
    db = SessionLocal()
    try:
        query = db.query(User)
        if search_query:
            query = query.filter((User.username.like(f"%{search_query}%")) | (User.nickname.like(f"%{search_query}%")))
        users = query.order_by(User.id.desc()).all()
        return [{"id": u.id, "username": u.username, "nickname": u.nickname, "role": u.role} for u in users]
    finally:
        db.close()


def update_user_by_admin(user_id: int, nickname: str, role: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.nickname = nickname
            user.role = role
            db.commit()
            return True
        return False
    finally:
        db.close()


def delete_user_and_data(user_id: int):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            db.delete(user)  # 级联删除会自动处理 sessions 和 messages
            db.commit()
            return True
        return False
    finally:
        db.close()


def get_admin_all_sessions():
    db = SessionLocal()
    try:
        # 使用 ORM 的 join
        results = db.query(ChatSession, User.nickname) \
            .join(User, ChatSession.user_id == User.id) \
            .order_by(ChatSession.updated_at.desc()).all()
        return [
            {
                "id": s.id,
                "title": s.title,
                "updated_at": s.updated_at,
                "user_nickname": nickname
            } for s, nickname in results
        ]
    finally:
        db.close()


# --- 共通更新功能 ---

def update_session_title_db(session_id: str, new_title: str):
    db = SessionLocal()
    try:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if session:
            session.title = new_title[:50]
            db.commit()
            return True
        return False
    finally:
        db.close()


def update_user_profile_db(user_id, nickname, old_password, new_password):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "用户未找到"

        if new_password:
            if not pwd_context.verify(old_password, user.password_hash):
                return False, "原密码验证失败"
            user.password_hash = pwd_context.hash(new_password)

        user.nickname = nickname
        db.commit()
        return True, "成功"
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()