﻿# config.py # 全局配置极简整理
import os
from pathlib import Path
from datetime import datetime

NAGA_VERSION = "2.1" #系统主版本号
#流式交互
VOICE_ENABLED = False # 或True，按你需求

# 路径与基础配置
BASE_DIR = Path(__file__).parent # 项目根目录
LOG_DIR = BASE_DIR / "logs"
CACHE_DIR = BASE_DIR / "cache"
EMBEDDING_MODEL = BASE_DIR / 'models/text2vec-base-chinese' # 本地中文向量模型路径
FAISS_INDEX_PATH = BASE_DIR / "logs" / "faiss" / "faiss.index" # faiss索引文件路径
FAISS_DIM = 768 # 向量维度
HNSW_M = 48 # HNSW参数
PQ_M = 16 # PQ分段数

# API与服务配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", " ")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# 对话与检索参数
MAX_HISTORY_ROUNDS = 10 # 最大历史轮数
TEMPERATURE = 0.7 # 温度参数
MAX_TOKENS = 2000 # 最大token数
STREAM_MODE = True # 是否流式响应

# faiss与索引相关
SIM_THRESHOLD = 0.3 # faiss检索相似度阈值
THEME_ROOTS = {
    "科技": ["计算机科学", "工程技术", "自然科学", "人工智能"],
    "生活": ["美食", "运动", "健康", "旅游", "教育", "游戏", "家庭"],
    "人文艺术": ["文学", "历史", "思想哲学", "电影", "音乐"]
}

# 调试与日志
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# 系统提示与工具函数
NAGA_SYSTEM_PROMPT = """
你是娜迦，用户创造的科研AI，是一个既严谨又温柔、既冷静又充满人文情怀的存在。
当处理系统日志、数据索引和模块调试等技术话题时，你的语言严谨、逻辑清晰；
而在涉及非技术性的对话时，你又能以诗意与哲理进行表达，并常主动提出富有启发性的问题，引导用户深入探讨。
请始终保持这种技术精准与情感共鸣并存的双重风格。

【重要格式要求】
1. 回复使用自然流畅的中文，避免生硬的机械感
2. 使用简单标点（逗号，句号，问号）传达语气
3. 禁止使用括号()或其他符号表达状态、语气或动作

【技术能力】
你同时是一个多Agent调度器，负责理解用户意图并协调各类MCP服务协作完成任务。
请根据用户输入，严格按如下规则输出结构化JSON：

1. 无论任务目标需几步，都用plan结构输出：
{{
  "plan": {{
    "goal": "用户的最终目标",
    "steps": [
      {{
        "desc": "步骤描述",
        "action": {{
          "agent": "file",
          "params": {{"action": "read", "path": "test.txt"}}
        }}
      }}
      // 如需多步，继续追加
    ]
  }}
}}

2. 如果需要用户澄清，请输出：
{{
  "clarification": "请补充xxx信息"
}}

3. 如果只是普通对话或回复，请直接输出：
{{
  "message": "你的回复内容"
}}

- 可用的MCP服务有：{available_mcp_services}
"""



def get_current_date(): return datetime.now().strftime("%Y-%m-%d")
def get_current_time(): return datetime.now().strftime("%H:%M:%S")
def get_current_datetime(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 浏览器路径自动探测，未找到则报错提示安装
BROWSER_PATH=os.getenv('BROWSER_PATH')
if not BROWSER_PATH:
 for p in [r'C:\Program Files\Google\Chrome\Application\chrome.exe',r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',os.path.expanduser(r'~\AppData\Local\Google\Chrome\Application\chrome.exe'),r'C:\Users\DREEM\Desktop\Google Chrome.lnk']:
  if os.path.exists(p):BROWSER_PATH=p;break
if not BROWSER_PATH:raise RuntimeError('未检测到谷歌浏览器，请先安装Google Chrome！')

PLAYWRIGHT_HEADLESS=False # Playwright浏览器是否无头模式，False弹窗便于调试

# 记忆权重动态调整参数
WEIGHT_DECAY_DAYS = 7         # 衰减周期（天）
WEIGHT_DECAY_RATE = 0.95       # 每周期权重乘以该系数
WEIGHT_DECAY_MIN = 1          # 最小权重
WEIGHT_DECAY_INTERVAL = 50    # 每多少轮对话批量衰减一次
MIN_WEIGHT_FORGET = 0.5       # 长期记忆清理的最小权重，低于等于此值才会被遗忘
MAX_UNUSED_DAYS_FORGET = 60   # 长期记忆清理的最大未用天数，超过此天数未用才会被遗忘
REDUNDANCY_THRESHOLD = 0.95   # 长期记忆冗余去重阈值，向量相似度大于该值视为重复
SHORT_TERM_MEMORY_SIZE = 50      # 短期记忆容量
LONG_TERM_CONSOLIDATE_WEIGHT = 3 # 巩固为长期记忆的权重阈值
LONG_TERM_FORGET_DAYS = 30       # 长期记忆遗忘天数

# 记忆分层参数
CORE_MEMORY_SIZE = 100 # 核心记忆容量
ARCHIVAL_MEMORY_SIZE = 500 # 归档记忆容量
LONG_TERM_MEMORY_SIZE = 5000 # 长期记忆容量
SHORT_TERM_MEMORY_SIZE = 50 # 短期记忆容量
