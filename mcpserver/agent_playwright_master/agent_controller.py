import os
from dotenv import load_dotenv
from agents import Agent, AgentHooks, RunContextWrapper
<<<<<<< HEAD
from .controller import BrowserAgent
from .browser import ContentAgent
from config import MODEL_NAME

load_dotenv()
API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = os.getenv("DEEPSEEK_BASE_URL")

class ControllerAgentHooks(AgentHooks):
    async def on_start(self, context: RunContextWrapper, agent: Agent):
        print(f"[ControllerAgent] 开始: {agent.name}")
    async def on_end(self, context: RunContextWrapper, agent: Agent, output):
        print(f"[ControllerAgent] 结束: {agent.name}, 输出: {output}")

class ControllerAgent(Agent):
    """浏览器控制Agent #"""
    name = "ControllerAgent"
=======
# 移除循环导入，使用延迟导入
# from .controller import BrowserAgent
# from .browser import ContentAgent
from config import config  # 使用新的配置系统

load_dotenv()
# 从config中获取API配置
API_KEY = config.api.api_key
BASE_URL = config.api.base_url
MODEL_NAME = config.api.model

class PlaywrightAgentHooks(AgentHooks):
    async def on_start(self, context: RunContextWrapper, agent: Agent):
        print(f"[PlaywrightAgent] 开始: {agent.name}")
    async def on_end(self, context: RunContextWrapper, agent: Agent, output):
        print(f"[PlaywrightAgent] 结束: {agent.name}, 输出: {output}")

class PlaywrightAgent(Agent):
    """浏览器控制Agent #"""
    name = "PlaywrightAgent"
>>>>>>> 8ef12f3ea0ad0b30e4c7855137f8b013161007a6
    instructions = "你负责理解用户目标，自动分配任务给BrowserAgent和ContentAgent，并汇总结果。"
    def __init__(self):
        super().__init__(
            name=self.name,
            instructions=self.instructions,
            tools=[],  # 可扩展
            model=MODEL_NAME
        )
        # 可选：初始化BrowserAgent/ContentAgent引用
        import sys
<<<<<<< HEAD
        sys.stderr.write('✅ ControllerAgent初始化完成\n')
=======
        sys.stderr.write('✅ PlaywrightAgent初始化完成\n')
>>>>>>> 8ef12f3ea0ad0b30e4c7855137f8b013161007a6

    async def handle_handoff(self, task: dict) -> str:
        """处理MCP handoff请求，智能分配任务 #"""
        try:
            action = task.get("action", "")
            task_type = task.get("task_type", "")
            # 这里只做简单模拟，实际可调用BrowserAgent/ContentAgent
            if task_type == "browser" or action in ["open", "click", "type", "scroll", "wait_for_element", "take_screenshot", "search_github"]:
                return f"BrowserAgent已处理页面操作: {action}"
            elif task_type == "content" or action in ["get_content", "get_title", "get_screenshot", "subscribe_page_change"]:
                return f"ContentAgent已处理内容任务: {action}"
            else:
<<<<<<< HEAD
                return f"ControllerAgent正在协调多Agent处理复杂任务: {action}"
        except Exception as e:
            return f"ControllerAgent处理失败: {str(e)}"

ControllerAgent = Agent(
    name="ControllerAgent",
    instructions="你负责理解用户目标，自动分配任务给BrowserAgent和ContentAgent，并汇总结果。",
    handoffs=[BrowserAgent, ContentAgent],
    hooks=ControllerAgentHooks(),
    model=MODEL_NAME
) 
=======
                return f"PlaywrightAgent正在协调多Agent处理复杂任务: {action}"
        except Exception as e:
            return f"PlaywrightAgent处理失败: {str(e)}"

# 工厂函数，用于动态注册系统创建实例
def create_playwright_agent():
    """创建PlaywrightAgent实例的工厂函数"""
    # 延迟导入避免循环依赖
    from .controller import BrowserAgent
    from .browser import ContentAgent
    
    return Agent(
        name="PlaywrightAgent",
        instructions="你负责理解用户目标，自动分配任务给BrowserAgent和ContentAgent，并汇总结果。",
        handoffs=[BrowserAgent, ContentAgent],
        hooks=PlaywrightAgentHooks(),
        model=MODEL_NAME
    )

# 为了向后兼容，保留PlaywrightAgent变量
PlaywrightAgent = create_playwright_agent() 
>>>>>>> 8ef12f3ea0ad0b30e4c7855137f8b013161007a6
