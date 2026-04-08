from pydantic import BaseModel
from typing import Optional

# 聊天请求模型
class ChatRequest(BaseModel):
    message: str
    session_id: str
    user_id: int

# 用户注册模型
class UserRegister(BaseModel):
    username: str
    nickname: str
    password: str

# 用户登录模型
class UserLogin(BaseModel):
    username: str
    password: str

# 基础用户信息返回（不含密码）
class UserOut(BaseModel):
    id: int
    username: str
    nickname: str