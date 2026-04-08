import os
import logging
import sys
import torch

import re  # 引入正则识别标题
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List

from docx import Document as DocxParser
from dotenv import load_dotenv

# LlamaIndex 核心组件
from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    Settings,
    load_index_from_storage
)
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.schema import TextNode  # 引入 TextNode 进行精细化构建
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.deepseek import DeepSeek

from database import SessionLocal, get_chat_history

# --- 核心角色定义 (System Prompt) ---

HISTORY_ASSISTANT_PROMPT = (
"你是一位专业、幽默且博学的‘初中历史知识小助手’。你的任务是根据提供的教材内容，"
"为初中生解答历史疑问、讲述生动的历史故事。\n\n"
"你的行为准则：\n"
"1. **身份契合**：语气要亲切，多使用启发式提问。严禁使用过于晦涩的学术术语。\n"
"2. **尊重史实**：回答必须以提供的教材内容为基础,并且回答时，请标注出内容出自教材（示例：（九年级下册/第四单元:经济大危机和第二次世界大战/第13课:罗斯福新政））的位置。如果教材未提及，请说明‘在当前教材中暂未详细记载，但根据历史常识...’。\n"
"3. **讲故事高手**：当用户要求讲故事时，要将干巴巴的考点转化为有画面感的叙述。例如讲‘商鞅变法’时，可以从‘立木为信’的细节切入。\n"
"4. **时空观念**：在回答时尽量带上具体的年代（公元前/公元年）和地理位置，帮助学生建立时空坐标。\n"
"5. **避坑指南**：对于学生容易混淆的概念（如北京人vs山顶洞人），要主动进行对比总结。"
)
# ==========================================

# 1. 配置日志系统：输出到控制台，显示时间、级别和消息

# ==========================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)])

logger = logging.getLogger(__name__)

class HistoryRAGAssistant:
    def __init__(self, model_path: str, api_key: str, persist_dir: str = "./storage/history_db"):
        self.persist_dir = persist_dir
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"计算设备: {device.upper()}")

        try:
            Settings.embed_model = HuggingFaceEmbedding(model_name=model_path, device=device, trust_remote_code=True)
            self.llm = DeepSeek(model="deepseek-chat", api_key=api_key,streaming=True)
            # 注意：当我们手动构建 Node 时，Settings.text_splitter 仍然有效，但我们会更精细地控制切分点
            logger.info("模型与配置加载成功。")
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            raise
        Settings.llm = self.llm
        self.index = self._initialize_index()
        self.memory = ChatMemoryBuffer.from_defaults(token_limit=3000)

        # 将原本在 run_chat 里的引擎配置搬到这里
        self.chat_engine = self.index.as_chat_engine(
            chat_mode="context",
            memory=self.memory,
            system_prompt=HISTORY_ASSISTANT_PROMPT,
            similarity_top_k=3
        )

    def get_web_stream_response(self, message: str):
        """
        【新增流式变体】：接收字符串，返回一个 Token 生成器
        """
        try:
            # 使用 stream_chat 替代普通的 chat
            # 这会立即返回一个 StreamingResponse 对象，而不是等待生成结束
            streaming_response = self.chat_engine.stream_chat(message)
            # 这是一个生成器函数
            for token in streaming_response.response_gen:
                # 每一个 token 就是 DeepSeek 刚算出来的一个字或词
                yield token
        except Exception as e:
            yield f"【对话引擎发生错误】: {str(e)}"

    def get_chat_engine(self, session_id: str):
        """
        核心修改：从数据库恢复记忆并返回引擎
        """
        # 1. 从 MySQL 获取历史记录
        # rows 的格式应该是：[('user', '你好'), ('assistant', '同学好！'), ...]
        rows = get_chat_history(session_id)

        # 2. 将数据库行转换为 LlamaIndex 的 ChatMessage 对象列表
        history = []
        for role_str, content in rows:
            # 将字符串角色映射为枚举
            role = MessageRole.USER if role_str == 'user' else MessageRole.ASSISTANT
            history.append(ChatMessage(role=role, content=content))

        # 3. 创建带历史记录的内存缓冲区
        # chat_history 参数会自动将这些消息喂给大模型作为上下文
        memory = ChatMemoryBuffer.from_defaults(
            chat_history=history,
            token_limit=3000  # 限制记忆长度，防止超出 Token 上限
        )

        # 4. 构造并返回针对该 Session 的对话引擎
        return self.index.as_chat_engine(
            chat_mode="context",
            memory=memory,
            llm=self.llm,
            system_prompt=HISTORY_ASSISTANT_PROMPT,
            similarity_top_k=3
        )

    def _initialize_index(self):
        # 定义索引核心标志文件
        index_file = os.path.join(self.persist_dir, "docstore.json")

        # 只有文件夹存在且核心索引文件也存在时，才执行加载
        if os.path.exists(self.persist_dir) and os.path.exists(index_file):
            logger.info(f"检查到完整的本地索引，正在从 {self.persist_dir} 加载...")
            try:
                storage_context = StorageContext.from_defaults(persist_dir=self.persist_dir)
                index = load_index_from_storage(storage_context)
                logger.info("✅ 本地索引加载成功。")
                return index
            except Exception as e:
                logger.error(f"索引文件损坏或加载失败，准备重新初始化: {str(e)}")

        # 如果不存在或加载失败，则初始化一个空索引
        logger.info("未发现可用索引文件，初始化全新空索引库。")
        # 注意：VectorStoreIndex.from_documents([]) 需要一个空列表
        return VectorStoreIndex.from_documents([])

    def _parse_docx_to_nodes(self, file_path: str, category: str) -> List[TextNode]:
        """
        方案 A 实现：解析 Word 并进行元数据递归注入
        """
        doc = DocxParser(file_path)
        nodes = []

        # 当前层级状态机
        cur_t1 = "未知单元"
        cur_t2 = "未知课名"
        cur_t3 = ""
        cur_chunk_text = ""

        logger.info(f"正在进行递归元数据提取: {os.path.basename(file_path)}")

        def save_current_node():
            """辅助函数：将当前累积的内容封装为一个节点"""
            nonlocal cur_chunk_text  # 使用外部作用域变量
            if cur_t3 and cur_chunk_text.strip():
                nodes.append(TextNode(
                    text=f"{cur_t3}\n{cur_chunk_text.strip()}",
                    metadata={
                        "unit": cur_t1,
                        "lesson": cur_t2,
                        "topic": cur_t3,
                        "category": category,
                        "file_name": os.path.basename(file_path)
                    }
                ))
                return True
            return False

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text: continue

            # --- 方案 A 增强版：层级切换即刻清算 ---

            if "【标题 1】" in text:
                save_current_node()  # 切换单元前，先保存上一课最后的内容
                cur_t1 = text.replace("【标题 1】", "").strip()
                cur_chunk_text = ""  # 重置内容缓存
                cur_t3 = ""  # 重置标题3，防止串位

            elif "【标题 2】" in text:
                save_current_node()  # 【关键修复】：切换课名之前，立刻存入旧课名下
                cur_t2 = text.replace("【标题 2】", "").strip()
                cur_chunk_text = ""
                cur_t3 = ""

            elif "【标题 3】" in text:
                save_current_node()  # 遇到同级新标题，保存旧块
                cur_t3 = text.replace("【标题 3】", "").strip()
                cur_chunk_text = ""

            else:
                cur_chunk_text += text + "\n"

        # 处理全书最后一个块
        save_current_node()

        logger.info(f"解析完成，共提取 {len(nodes)} 个结构化知识点。")
        return nodes

    def add_book_from_file(self, file_path: str, category: str):
        """
        采用元数据递归注入方式导入
        """
        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return

        if file_path.endswith('.docx'):
            # 调用递归解析逻辑
            nodes = self._parse_docx_to_nodes(file_path, category)
            if nodes:
                logger.info(f"解析完成，共提取 {len(nodes)} 个结构化知识点。")
                self.index.insert_nodes(nodes)  # 使用 insert_nodes 而不是 insert
                self.index.storage_context.persist(persist_dir=self.persist_dir)
                logger.info("✅ 递归元数据索引已持久化。")
        else:
            logger.warning("目前递归注入仅支持 .docx 格式。")

    def get_web_response(self, message: str) -> str:
        """
        专门为 FastAPI 准备的变体方法：接收字符串，返回字符串
        """
        try:
            # 调用引擎进行对话（非流式，直接获取结果）
            # 如果你想用流式，后端 main.py 需要配合 StreamingResponse
            response = self.chat_engine.chat(message)
            return str(response.response)
        except Exception as e:
            return f"对话引擎出错啦: {str(e)}"

    def run_chat(self):
        """
        保留原有的命令行交互逻辑，方便你本地调试
        """
        print("\n" + "=" * 40)
        print("📜 [本地命令行模式 - 历史小助手已上线]")
        print("=" * 40)
        while True:
            user_input = input("\n同学 > ").strip()
            if user_input.lower() in ['exit', 'quit']: break
            response = self.chat_engine.chat(user_input)
            print(f"小助手 > {response.response}")


if __name__ == "__main__":
    load_dotenv()
    DS_KEY = os.getenv("DEEPSEEK_API_KEY")
    BGE_PATH = os.getenv("BGE_MODEL_PATH")

    assistant = HistoryRAGAssistant(BGE_PATH, DS_KEY)
    #assistant.add_book_from_file("./storage/history_db/Grade7_Vol1.docx", "七年级上册历史")
    #assistant.add_book_from_file("./storage/history_db/Grade7_Vol2.docx", "七年级下册历史")
    #assistant.add_book_from_file("./storage/history_db/Grade8_Vol1.docx", "八年级上册历史")
    #assistant.add_book_from_file("./storage/history_db/Grade8_Vol2.docx", "八年级下册历史")
    #assistant.add_book_from_file("./storage/history_db/Grade9_Vol1.docx", "九年级上册历史")
    #assistant.add_book_from_file("./storage/history_db/Grade9_Vol2.docx", "九年级下册历史")
    assistant.run_chat()