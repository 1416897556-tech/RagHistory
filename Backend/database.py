from passlib.context import CryptContext
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

# 创建引擎和 Session 工厂
engine = create_engine(DB_URL, pool_recycle=3600, echo=False)
SessionLocal = sessionmaker(bind=engine)

#登录功能
def get_user_by_username(username: str):
    db = SessionLocal()
    try:
        # 查询时也要把 role 带出来
        sql = text("SELECT id, username, nickname, password_hash, role FROM users WHERE username = :u")
        result = db.execute(sql, {"u": username}).fetchone()
        if result:
            return {
                "id": result[0],
                "username": result[1],
                "nickname": result[2],
                "password_hash": result[3],
                "role": result[4] # 这里的 role 会返回给前端
            }
        return None
    finally:
        db.close()

def insert_new_user(username, nickname, password_hash, role="user"):
    """插入新用户数据"""
    db = SessionLocal()
    try:
        sql = text("INSERT INTO users (username, nickname, password_hash, role) VALUES (:u, :n, :p, :r)")
        db.execute(sql, {"u": username, "n": nickname, "p": password_hash, "r": role})
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"DB Error: {e}")
        return False
    finally:
        db.close()

#对话功能
def create_session_if_not_exists(session_id: str, user_id: int, title: str = "新对话"):
    db = SessionLocal()
    try:
        check_sql = text("SELECT id FROM chat_sessions WHERE id = :sid")
        if not db.execute(check_sql, {"sid": session_id}).fetchone():
            ins_sql = text("INSERT INTO chat_sessions (id, title, user_id) VALUES (:sid, :title, :uid)")
            db.execute(ins_sql, {"sid": session_id, "title": title[:50], "uid": user_id})
            db.commit()
    finally:
        db.close()


def save_message(session_id: str, role: str, content: str):
    """保存单条聊天记录"""
    db = SessionLocal()
    try:
        sql = text("INSERT INTO chat_messages (session_id, role, content) VALUES (:sid, :role, :content)")
        db.execute(sql, {"sid": session_id, "role": role, "content": content})
        db.commit()
    finally:
        db.close()


def get_chat_history(session_id: str):
    """获取某个会话的所有历史记录"""
    db = SessionLocal()
    try:
        sql = text("SELECT role, content FROM chat_messages WHERE session_id = :sid ORDER BY created_at ASC")
        return db.execute(sql, {"sid": session_id}).fetchall()
    finally:
        db.close()


def get_all_sessions(user_id: int):
    """获取所有历史会话列表（用于前端侧边栏）"""
    db = SessionLocal()
    try:
        sql = text("SELECT id, title, updated_at FROM chat_sessions WHERE user_id = :uid ORDER BY updated_at DESC")

        result = db.execute(sql, {"uid": user_id}).fetchall()
        # 将结果转为字典列表，方便前端读取
        return [{"id": r[0], "title": r[1], "updated_at": r[2]} for r in result]
    finally:
        db.close()


def delete_chat_session(session_id: str):
    """
    删除会话及其关联的所有聊天记录
    """
    db = SessionLocal()
    try:
        # 1. 删除关联的消息（从表）
        db.execute(
            text("DELETE FROM chat_messages WHERE session_id = :sid"),
            {"sid": session_id}
        )
        # 2. 删除会话主体（主表）
        result = db.execute(
            text("DELETE FROM chat_sessions WHERE id = :sid"),
            {"sid": session_id}
        )

        db.commit()
        # 返回受影响的行数，用于判断是否真的删除了东西
        return result.rowcount > 0
    except Exception as e:
        db.rollback()
        print(f"数据库删除失败: {e}")
        return False
    finally:
        db.close()


def get_all_users(search_query: str = None):
    """获取用户列表，支持按用户名模糊搜索"""
    db = SessionLocal()
    try:
        if search_query:
            # 使用 SQL 的 LIKE 语法进行模糊匹配
            sql = text("""
                SELECT id, username, nickname, role 
                FROM users 
                WHERE username LIKE :q OR nickname LIKE :q
                ORDER BY id DESC
            """)
            result = db.execute(sql, {"q": f"%{search_query}%"}).fetchall()
        else:
            sql = text("SELECT id, username, nickname, role FROM users ORDER BY id DESC")
            result = db.execute(sql).fetchall()

        return [{"id": r[0], "username": r[1], "nickname": r[2], "role": r[3]} for r in result]
    finally:
        db.close()


def update_user_by_admin(user_id: int, nickname: str, role: str):
    """管理员更新用户信息（昵称或权限等级）"""
    db = SessionLocal()
    try:
        sql = text("UPDATE users SET nickname = :n, role = :r WHERE id = :id")
        db.execute(sql, {"n": nickname, "r": role, "id": user_id})
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"更新用户失败: {e}")
        return False
    finally:
        db.close()

def delete_user_and_data(user_id: int):
    """
    危险操作：注销用户。
    需要先删除该用户所有的聊天记录和会话，再删除用户主体。
    """
    db = SessionLocal()
    try:
        # 1. 找到该用户所有的 session_id
        sessions_sql = text("SELECT id FROM chat_sessions WHERE user_id = :uid")
        session_ids = [r[0] for r in db.execute(sessions_sql, {"uid": user_id}).fetchall()]

        # 2. 删除这些 session 关联的所有消息
        if session_ids:
            db.execute(
                text("DELETE FROM chat_messages WHERE session_id IN :sids"),
                {"sids": tuple(session_ids)}
            )
            # 3. 删除这些 session
            db.execute(text("DELETE FROM chat_sessions WHERE user_id = :uid"), {"uid": user_id})

        # 4. 最后删除用户
        db.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": user_id})

        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"注销用户失败: {e}")
        return False
    finally:
        db.close()

# --- 管理员：对话监控拓展 ---
def get_admin_all_sessions():
    """获取全系统所有对话，并关联显示对应的用户昵称"""
    db = SessionLocal()
    try:
        # 使用 JOIN 关联查询，方便管理员知道这段对话是谁的
        sql = text("""
            SELECT s.id, s.title, s.updated_at, u.nickname 
            FROM chat_sessions s
            JOIN users u ON s.user_id = u.id
            ORDER BY s.updated_at DESC
        """)
        result = db.execute(sql).fetchall()
        return [
            {
                "id": r[0],
                "title": r[1],
                "updated_at": r[2],
                "user_nickname": r[3]
            } for r in result
        ]
    finally:
        db.close()

def update_session_title_by_admin(session_id: str, new_title: str):
    """管理员强行修改对话标题"""
    db = SessionLocal()
    try:
        sql = text("UPDATE chat_sessions SET title = :t WHERE id = :sid")
        db.execute(sql, {"t": new_title[:50], "sid": session_id})
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        return False
    finally:
        db.close()


# 初始化密码加密工具
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto"
)


def update_user_profile_db(user_id, nickname, old_password, new_password):
    db = SessionLocal()
    try:
        # 1. 修改查询语句，将字段名改为 password_hash
        # 建议显式查出需要的列
        result = db.execute(
            text("SELECT id, nickname, password_hash FROM users WHERE id = :id"),
            {"id": user_id}
        ).fetchone()

        if not result:
            return False, "用户未找到"

        # 2. 获取数据库中的哈希值
        # 使用 _mapping 可以通过列名字符串访问，最稳妥
        db_data = result._mapping
        current_password_hash = db_data["password_hash"]

        # 3. 如果涉及密码修改
        if new_password:
            # 验证原密码：用输入的 old_password 和数据库的 password_hash 对比
            if not pwd_context.verify(old_password, current_password_hash):
                return False, "原密码验证失败"

            # 哈希新密码
            hashed_new_pwd = pwd_context.hash(new_password)

            # 更新语句同步修改字段名为 password_hash
            db.execute(
                text("""
                    UPDATE users 
                    SET nickname = :n, password_hash = :p 
                    WHERE id = :id
                """),
                {"n": nickname, "p": hashed_new_pwd, "id": user_id}
            )
        else:
            # 只更新昵称
            db.execute(
                text("UPDATE users SET nickname = :n WHERE id = :id"),
                {"n": nickname, "id": user_id}
            )

        db.commit()
        return True, "成功"
    except Exception as e:
        db.rollback()
        print(f"Update Profile Error: {e}")
        return False, str(e)
    finally:
        db.close()

def update_session_title_db(session_id: int, new_title: str):
    db = SessionLocal()
    try:
        # 更新指定会话的标题
        sql = text("UPDATE chat_sessions SET title = :title WHERE id = :id")
        db.execute(sql, {"title": new_title, "id": session_id})
        db.commit()
        return True
    except Exception as e:
        print(f"Update Session Title Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()