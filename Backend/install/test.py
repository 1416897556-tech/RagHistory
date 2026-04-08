import os
import logging
import asyncio
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    Settings,
    StorageContext,
    load_index_from_storage
)
# 导入对应的集成库
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.deepseek import DeepSeek

# 1. 日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 2. 常量配置
# 注意：Windows 路径建议使用双反斜杠或原始字符串 r""
EMBED_MODEL_PATH = r"E:\home\ai_project\model\Xorbits\bge-base-zh-v1___5"
PERSIST_DIR = "./storage"  # 索引持久化目录


async def setup_engine():
    # --- 全局组件配置 (Settings) ---

    # 配置本地 Embedding 模型 (BGE-Base-ZH)
    # device="cuda" 如果你有 NVIDIA 显卡，否则使用 "cpu"
    logger.info("正在加载本地 Embedding 模型...")
    Settings.embed_model = HuggingFaceEmbedding(
        model_name=EMBED_MODEL_PATH,
        device="cuda" if os.environ.get("USE_CUDA") else "cpu"
    )


    Settings.llm = DeepSeek(
        model="deepseek-chat",
        api_key="sk-1ed3638e833a4c0b956c4c97f61f2ac9",
        api_base="https://api.deepseek.com",  # 对应官方 base_url
        temperature=0.1
    )

    Settings.chunk_size = 512
    Settings.chunk_overlap = 50

    # --- 索引管理 (持久化逻辑) ---
    if not os.path.exists(PERSIST_DIR):
        logger.info("创建新索引...")
        # 确保 ./data 目录下有你的文档
        if not os.path.exists("./data"):
            os.makedirs("./data")

        documents = SimpleDirectoryReader("./data").load_data()
        index = VectorStoreIndex.from_documents(documents)
        # 将索引保存到磁盘，下次无需重新计算 Embedding
        index.storage_context.persist(persist_dir=PERSIST_DIR)
    else:
        logger.info("从磁盘加载现有索引...")
        storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
        index = load_index_from_storage(storage_context)

    # --- 查询引擎配置 ---
    # 针对中文场景，建议在查询时适当调整相似度阈值
    query_engine = index.as_query_engine(
        similarity_top_k=3,
        system_prompt="你是一个专业的 AI 助手。请根据提供的上下文回答问题。如果上下文中没有相关信息，请诚实回答不知道。",
        streaming=False
    )

    return query_engine


async def main():
    engine = await setup_engine()

    while True:
        question = input("\n请输入问题 (输入 'exit' 退出): ")
        if question.lower() == 'exit':
            break

        try:
            response = engine.query(question)
            print(f"\n[DeepSeek 回答]:\n{response}")
        except Exception as e:
            logger.error(f"查询出错: {e}")


if __name__ == "__main__":
    asyncio.run(main())

