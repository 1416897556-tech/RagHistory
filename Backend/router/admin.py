import os
import sys
from typing import Optional

# 1. 获取 Backend 根目录的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)

# 2. 将根目录插入到路径最前端
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# 3. 核心黑科技：直接通过文件路径加载 database，彻底解决重名问题
import importlib.util
def load_custom_db():
    db_path = os.path.join(root_dir, "database.py")
    spec = importlib.util.spec_from_file_location("my_custom_db", db_path)
    module = importlib.util.module_from_spec(spec)
    # 将其注入到 sys.modules 防止重复加载
    sys.modules["my_custom_db"] = module
    spec.loader.exec_module(module)
    return module

# 4. 执行加载并起别名为 my_db
try:
    my_db = load_custom_db()
except Exception as e:
    print(f"无法加载项目数据库文件: {e}")
    # 最后的兜底尝试
    import database as my_db

# 5. 现在再导入其他第三方库
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

# 6. 处理 ModelScope (如果它干扰了 database 这个词)
try:
    from modelscope.preprocessors.nlp.space_T_cn.fields import database as ms_db
except ImportError:
    ms_db = None

router = APIRouter(prefix="/admin", tags=["管理员模块"])
# --- 数据模型 ---

class UserUpdate(BaseModel):
    nickname: str
    role: str

class SessionUpdate(BaseModel):
    title: str

# --- 辅助函数：校验管理员权限 ---
def check_admin_auth(role: str):
    if role != "admin":
        raise HTTPException(status_code=403, detail="对不起，您没有管理权限")

# --- 用户管理接口 ---

@router.get("/users")
async def get_all_platform_users(
    current_user_role: str = Query(...),
    q: Optional[str] = Query(None) # 新增可选搜索参数
):
    """获取所有用户信息（支持搜索）"""
    check_admin_auth(current_user_role)
    return my_db.get_all_users(search_query=q)

@router.put("/users/{user_id}")
async def update_user(user_id: int, data: UserUpdate, current_user_role: str = Query(...)):
    """修改用户信息（昵称或角色）"""
    check_admin_auth(current_user_role)
    success = my_db.update_user_by_admin(user_id, data.nickname, data.role)
    if success:
        return {"message": "用户信息修改成功"}
    raise HTTPException(status_code=500, detail="更新失败")

@router.delete("/users/{user_id}")
async def delete_user(user_id: int, current_user_role: str = Query(...)):
    """彻底注销用户及其所有数据"""
    check_admin_auth(current_user_role)
    success = my_db.delete_user_and_data(user_id)
    if success:
        return {"message": "用户及其关联数据已永久删除"}
    raise HTTPException(status_code=500, detail="删除用户失败")

# --- 对话监控接口 ---

@router.get("/sessions")
async def get_all_platform_sessions(current_user_role: str = Query(...)):
    """获取全系统对话列表（带用户昵称）"""
    check_admin_auth(current_user_role)
    return my_db.get_admin_all_sessions()

@router.patch("/sessions/{session_id}")
async def update_session_title(session_id: str, data: SessionUpdate, current_user_role: str = Query(...)):
    """管理员强行修改对话标题"""
    check_admin_auth(current_user_role)
    success = my_db.update_session_title_by_admin(session_id, data.title)
    if success:
        return {"message": "对话标题已重置"}
    raise HTTPException(status_code=500, detail="标题修改失败")

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, current_user_role: str = Query(...)):
    """删除指定对话记录"""
    check_admin_auth(current_user_role)
    # 直接复用你之前在 database.py 写的 delete_chat_session 即可
    success = my_db.delete_chat_session(session_id)
    if success:
        return {"message": "对话记录已清理"}
    raise HTTPException(status_code=404, detail="未找到该对话或删除失败")


class ProfileUpdate(BaseModel):
    nickname: str
    old_password: Optional[str] = None
    new_password: Optional[str] = None


@router.put("/users/{user_id}/profile")
async def update_profile(user_id: int, payload: dict):
    nickname = payload.get("nickname")
    old_pwd = payload.get("old_password")
    new_pwd = payload.get("new_password")
    success, msg = my_db.update_user_profile_db(user_id, nickname, old_pwd, new_pwd)
    if not success:
        raise HTTPException(status_code=400, detail=msg)

    return {"status": "ok"}


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str, current_user_role: str):
    """
    管理员获取特定会话的历史消息详情
    """
    if current_user_role != "admin":
        raise HTTPException(status_code=403, detail="权限不足，仅限管理员查看")

    try:
        # 🚩 调用 ORM 版的数据库函数
        # 此时 history 已经是类似于 [{"role": "user", "content": "..."}, ...] 的格式
        history = my_db.get_chat_history(session_id)

        return {
            "status": "success",
            "data": history
        }
    except Exception as e:
        print(f"获取消息失败: {e}")
        raise HTTPException(status_code=500, detail="无法读取对话记录")