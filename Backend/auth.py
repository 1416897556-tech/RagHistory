from passlib.context import CryptContext
from database import get_user_by_username, insert_new_user

# 初始化加密工具
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str):
    """明文转哈希"""
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    """验证明文和哈希是否匹配"""
    return pwd_context.verify(plain_password, hashed_password)


def register_user(username, nickname, password,role="user"):
    """业务层：用户注册"""
    # 1. 检查用户是否已存在
    if get_user_by_username(username):
        return {"success": False, "message": "用户名已存在"}
    if len(password) < 5:
        return {"success": False, "message": "注册失败：密码长度不能少于 5 位"}
    if len(username) < 8:
        return {"success": False, "message": "注册失败：账号长度不能少于 8 位"}
    # 2. 密码加密并存入
    hashed = hash_password(password)
    if insert_new_user(username, nickname, hashed,role):
        return {"success": True, "message": "注册成功"}
    return {"success": False, "message": "系统繁忙"}


def login_user(username, password):
    """业务层：用户登录"""
    user = get_user_by_username(username)
    if not user:
        return None

    # 校验密码 (user[3] 是数据库里的 password_hash)
    if user and verify_password(password, user["password_hash"]):
        # 移除敏感的 password_hash 后返回给前端
        user_info = user.copy()
        del user_info["password_hash"]
        return user_info