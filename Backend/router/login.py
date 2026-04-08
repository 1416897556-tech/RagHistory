import sys
import os
from fastapi import APIRouter, HTTPException, status

# --- 核心修复代码：动态定位根目录 ---
# 获取当前文件 (login.py) 的路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取上一级目录 (Backend 根目录)
root_dir = os.path.dirname(current_dir)
# 如果根目录不在搜索路径中，添加进去
sys.path.append(root_dir)
from schemas import UserRegister,UserLogin
import auth

# 创建路由对象，可以给所有接口加前缀，比如 /auth/login
router = APIRouter(prefix="/auth", tags=["用户认证"])

@router.post("/register")
async def register(user_data: UserRegister):
    result = auth.register_user(
        user_data.username,
        user_data.nickname,
        user_data.password,
        role="user"  # 强制设为普通用户，安全性更高
    )
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    return result

@router.post("/login")
async def login(user_data: UserLogin):
    user_info = auth.login_user(user_data.username, user_data.password)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    return user_info