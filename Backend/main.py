import os
import uvicorn
import asyncio
from fastapi import FastAPI, HTTPException,Body
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.concurrency import run_in_threadpool
from router import login,admin
from database import (
    create_session_if_not_exists, save_message, get_all_sessions, get_chat_history,delete_chat_session,update_session_title_db
)
from schemas import ChatRequest
import auth
# 导入你的核心类
from HistoryAid import HistoryRAGAssistant

# 1. 加载环境变量
load_dotenv()
DS_KEY = os.getenv("DEEPSEEK_API_KEY")
BGE_PATH = os.getenv("BGE_MODEL_PATH")

# 2. 初始化 FastAPI
app = FastAPI(title="初中历史全能助手 API")

# 3. 配置跨域 (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(login.router)
app.include_router(admin.router)
# 4. 初始化助手实例
# 假设你的类在初始化时已经处理好了 index
try:
    assistant = HistoryRAGAssistant(BGE_PATH, DS_KEY)
    print("✅ HistoryRAGAssistant 实例已就绪")
except Exception as e:
    print(f"❌ 助手初始化失败: {e}")
    assistant = None

# --- 路由接口 ---

@app.get("/")
def index():
    return {"message": "Welcome to History AI"}

# 获取所有会话列表（用于侧边栏渲染）
@app.get("/sessions")
async def list_sessions():
    try:
        rows = get_all_sessions()
        # 将数据库行转为字典格式供前端使用
        sessions = [{"id": r[0], "title": r[1], "updated_at": r[2]} for r in rows]
        return sessions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions/{user_id}")
async def list_sessions(user_id: int):
    # 打印一下，看看 user_id 是不是真的传进来了
    print(f"--- 正在查询用户 {user_id} 的会话列表 ---")

    if not user_id:
        raise HTTPException(status_code=400, detail="用户ID不能为空")
    sessions = get_all_sessions(user_id)
    return sessions


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    # 调用 database.py 中的逻辑
    success = delete_chat_session(session_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail="删除失败：未找到该会话或数据库错误"
        )

    return {"status": "success", "message": "会话已永久删除"}

# 获取某个特定会话的所有消息（用于切换对话时回填气泡）
@app.get("/history/{session_id}")
async def get_history(session_id: str):
    try:
        messages = get_chat_history(session_id)
        return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据库读取失败: {str(e)}")


@app.put("/sessions/{session_id}/title")
async def update_session_title(session_id: str, payload: dict = Body(...)):
    """
    修改对话记录标题的接口
    """
    new_title = payload.get("title")

    if not new_title or not new_title.strip():
        raise HTTPException(status_code=400, detail="标题内容不能为空")

    # 调用 database.py 中的函数
    success = update_session_title_db(session_id, new_title.strip())

    if not success:
        raise HTTPException(status_code=500, detail="服务器内部错误，无法更新标题")

    return {"status": "success", "message": "标题已更新"}

@app.post("/chat_stream")
async def chat_stream_endpoint(request: ChatRequest):
    # 显式检查 assistant 是否存在
    if assistant is None:
        raise HTTPException(status_code=500, detail="助手未初始化")

    sid = request.session_id
    user_msg = request.message

    # 1. 数据库预处理
    # 确保会话存在（如果不存在则创建，标题默认为消息前十个字）
    create_session_if_not_exists(request.session_id, request.user_id, request.message[:15])

    # 将用户的提问存入 MySQL
    save_message(sid, 'user', user_msg)

    # 2. 获取带历史记忆的引擎
    # 这个方法内部会调用 database.get_chat_history 加载旧消息
    engine = assistant.get_chat_engine(sid)

    # 3. 发起流式对话
    streaming_response = engine.stream_chat(user_msg)

    # 4. 定义异步包装生成器
    async def wrapped_generator():
        full_response = ""
        try:
            # 遍历 LlamaIndex 生成的 token
            for token in streaming_response.response_gen:
                full_response += token
                yield token
                await asyncio.sleep(0.01)

            # 【重要】当循环结束，说明 AI 回答完毕，此时存入数据库
            if full_response:
                save_message(sid, 'assistant', full_response)

        except Exception as e:
            error_msg = f"\n[回答中断: {str(e)}]"
            yield error_msg
            save_message(sid, 'assistant', full_response + error_msg)

    # media_type 使用 text/plain 或 text/event-stream 均可
    # 只要前端 TextDecoder 能解析就行
    return StreamingResponse(
        wrapped_generator(),
        media_type="text/plain",
        headers={
            "Content-Type": "text/plain; charset=utf-8",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 极其重要：防止代理/浏览器缓冲
        }
    )


# 5. 启动
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)