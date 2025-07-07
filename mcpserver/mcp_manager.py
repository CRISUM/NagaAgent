import asyncio
import logging
import inspect
from typing import Dict, Optional, List, Any, Callable, Awaitable, Generic, TypeVar, Union, cast
from contextlib import AsyncExitStack
import sys
from pydantic import BaseModel, TypeAdapter
from dataclasses import dataclass
import json
from datetime import datetime
import importlib,os,inspect # 自动注册相关
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcpserver.mcp_registry import MCP_REGISTRY, register_all_handoffs, get_agent_instance # MCP服务注册表和handoff批量注册

from config import DEBUG, LOG_LEVEL

# 配置日志
logging.basicConfig(
    level=logging.DEBUG if DEBUG else getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MCPManager")

_builtin_print=print
print=lambda *a,**k:sys.stderr.write('[print] '+(' '.join(map(str,a)))+'\n')

TContext = TypeVar("TContext")
THandoffInput = TypeVar("THandoffInput")

class HandoffError(Exception):
    """Handoff基础异常类"""
    pass

class ModelBehaviorError(HandoffError):
    """模型行为异常"""
    pass

class HandoffValidationError(HandoffError):
    """Handoff数据验证异常"""
    pass

class HandoffConnectionError(HandoffError):
    """Handoff连接异常"""
    pass

@dataclass
class HandoffInputData:
    """Handoff输入数据结构"""
    input_history: Union[str, tuple[Any, ...]] #历史输入
    pre_handoff_items: tuple[Any, ...] #handoff前的items
    new_items: tuple[Any, ...] #当前turn生成的items
    context: Optional[Dict[str, Any]] = None #上下文数据
    metadata: Optional[Dict[str, Any]] = None #元数据

    @classmethod
    def create(cls, 
        input_history: Any = None,
        pre_items: Any = None,
        new_items: Any = None,
        context: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None
    ) -> 'HandoffInputData':
        """创建HandoffInputData实例"""
        return cls(
            input_history=input_history if input_history is not None else (),
            pre_handoff_items=pre_items if pre_items is not None else (),
            new_items=new_items if new_items is not None else (),
            context=context,
            metadata=metadata
        )

def remove_tools_filter(messages: list) -> list:
    """移除工具调用的过滤器函数"""
    return [
        msg for msg in messages
        if not any(tool in str(msg) for tool in ["[tool]", "[handoff]"])
    ]

@dataclass
class Handoff(Generic[TContext]):
    """Handoff配置类"""
    tool_name: str
    tool_description: str
    input_json_schema: dict[str, Any]
    agent_name: str
    on_invoke_handoff: Callable[[Any, str], Awaitable[Any]]
    strict_json_schema: bool = True
    
    async def invoke(self, ctx: Any, input_json: Optional[str] = None) -> Any:
        """执行handoff调用"""
        if self.input_json_schema and not input_json:
            raise ModelBehaviorError("Handoff需要输入但未提供")
            
        try:
            if input_json:
                # 验证输入
                type_adapter = TypeAdapter(dict[str, Any])
                validated_input = type_adapter.validate_json(
                    input_json,
                    strict=self.strict_json_schema
                )
            else:
                validated_input = None
                
            # 验证回调函数签名
            sig = inspect.signature(self.on_invoke_handoff)
            if len(sig.parameters) != 2:
                raise HandoffValidationError(
                    "Handoff回调函数必须接受两个参数(context, input)"
                )
                
            return await self.on_invoke_handoff(ctx, validated_input)
        except Exception as e:
            if isinstance(e, HandoffError):
                raise
            raise HandoffError(f"Handoff执行失败: {str(e)}")

class MCPManager:
    """MCP服务管理器，负责管理所有MCP服务的连接和调用"""
    
    def __init__(self):
        """初始化MCP管理器"""
        self.services = {}
        self.tools_cache = {}
        self.exit_stack = AsyncExitStack()
        self.handoffs = {} # 服务对应的handoff对象
        self.handoff_filters = {} # 服务对应的handoff过滤器
        self.handoff_callbacks = {} # 服务对应的handoff回调
        self.logger = logging.getLogger("MCPManager")
        sys.stderr.write("MCPManager初始化\n")
        
    def register_handoff(
        self,
        service_name: str,
        tool_name: str,
        tool_description: str,
        input_schema: dict,
        agent_name: str,
        filters=None,
        strict_schema=False
    ):
        """注册handoff服务"""
        if service_name in self.services:
            sys.stderr.write(f"服务{service_name}已注册，跳过重复注册\n")
            return
        self.services[service_name] = {
            "tool_name": tool_name,
            "tool_description": tool_description,
            "input_schema": input_schema,
            "agent_name": agent_name,
            "filter_fn": remove_tools_filter,  # 使用函数而不是类实例
            "strict_schema": strict_schema
        }
        
    async def _default_handoff_callback(
        self,
        ctx: Any,
        input_json: Optional[str]
    ) -> Any:
        """默认的handoff回调处理"""
        return None
            
    async def handoff(
        self,
        service_name: str,
        task: dict,
        input_history: Any = None,
        pre_items: Any = None,
        new_items: Any = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """执行handoff"""
        try:
            # 修复中文编码问题
            task_json = json.dumps(task, ensure_ascii=False)
            sys.stderr.write(f"执行handoff: service={service_name}, task={task_json}\n".encode('utf-8', errors='replace').decode('utf-8'))
            
            if service_name not in self.services:
                raise ValueError(f"未注册的服务: {service_name}")
                
            service = self.services[service_name]
            # 只打印服务配置中的安全字段
            safe_service_info = {
                "name": service.get("name", ""),
                "description": service.get("description", ""),
                "agent_name": service.get("agent_name", ""),
                "strict_schema": service.get("strict_schema", False)
            }
            safe_info_json = json.dumps(safe_service_info, ensure_ascii=False)
            sys.stderr.write(f"找到服务配置: {safe_info_json}\n".encode('utf-8', errors='replace').decode('utf-8'))
            
            # 简单验证必需字段
            if service["strict_schema"]:
                required_fields = service["input_schema"].get("required", [])
                for field in required_fields:
                    if field not in task:
                        raise ValueError(f"缺少必需字段: {field}")
                
            # 应用过滤器函数
            if "messages" in task and service["filter_fn"]:
                try:
                    task["messages"] = service["filter_fn"](task["messages"])
                except Exception as e:
                    sys.stderr.write(f"消息过滤失败: {e}\n".encode('utf-8', errors='replace').decode('utf-8'))
                    # 继续执行，使用原始消息
                
            # 创建代理实例
            from mcpserver.mcp_registry import MCP_REGISTRY, get_agent_instance # 统一注册中心
            agent_name = service["agent_name"]
            agent = get_agent_instance(agent_name)  # 使用新的统一接口
            if not agent:
                raise ValueError(f"找不到已注册的Agent实例: {agent_name}")
            sys.stderr.write(f"使用注册中心中的Agent实例: {agent_name}\n".encode('utf-8', errors='replace').decode('utf-8'))
            # 执行handoff
            sys.stderr.write("开始执行代理handoff\n".encode('utf-8', errors='replace').decode('utf-8'))
            result = await agent.handle_handoff(task)
            sys.stderr.write(f"代理handoff执行结果: {result}\n".encode('utf-8', errors='replace').decode('utf-8'))
            
            return result
            
        except Exception as e:
            error_msg = f"Handoff执行失败: {str(e)}"
            sys.stderr.write(f"{error_msg}\n".encode('utf-8', errors='replace').decode('utf-8'))
            import traceback
            traceback.print_exc(file=sys.stderr)
            
            return json.dumps({
                "status": "error",
                "message": error_msg
            }, ensure_ascii=False)
            
    async def connect_service(self, service_name: str) -> Optional[ClientSession]:
        """连接到指定的MCP服务
        
        Args:
            service_name: MCP服务名称
            
        Returns:
            Optional[ClientSession]: 成功返回会话对象，失败返回None
        """
        # 直接返回None，或根据MCP_REGISTRY判断服务是否存在
        if service_name not in MCP_REGISTRY:
            logger.warning(f"MCP服务 {service_name} 不存在")
            return None
            
        # 如果已连接，直接返回会话
        if service_name in self.services:
            return self.services[service_name]
            
        service_config = MCP_REGISTRY[service_name]
        command = "python" if service_config["type"] == "python" else "node"
        
        try:
            logger.info(f"正在连接MCP服务: {service_name}")
            server_params = StdioServerParameters(
                command=command,
                args=[service_config["script_path"]],
                env=None
            )
            
            # 创建服务连接
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            stdio, write = stdio_transport
            
            # 创建并初始化会话
            session = await self.exit_stack.enter_async_context(
                ClientSession(stdio, write)
            )
            await session.initialize()
            
            # 缓存会话
            self.services[service_name] = session
            logger.info(f"MCP服务 {service_name} 连接成功")
            return session
            
        except Exception as e:
            logger.error(f"连接MCP服务 {service_name} 失败: {str(e)}")
            import traceback;traceback.print_exc(file=sys.stderr)
            return None
            
    async def get_service_tools(self, service_name: str) -> list:
        """获取指定MCP服务的可用工具列表
        
        Args:
            service_name: MCP服务名称
            
        Returns:
            list: 工具列表
        """
        # 检查缓存
        if service_name in self.tools_cache:
            return self.tools_cache[service_name]
            
        session = await self.connect_service(service_name)
        if not session:
            return []
            
        try:
            response = await session.list_tools()
            tools = response.tools
            # 缓存工具列表
            self.tools_cache[service_name] = tools
            return tools
        except Exception as e:
            logger.error(f"获取服务 {service_name} 的工具列表失败: {str(e)}")
            import traceback;traceback.print_exc(file=sys.stderr)
            return []
            
    async def call_service_tool(self, service_name: str, tool_name: str, args: dict):
        """调用指定MCP服务的工具
        
        Args:
            service_name: MCP服务名称
            tool_name: 工具名称
            args: 工具参数
            
        Returns:
            工具调用结果
        """
        session = await self.connect_service(service_name)
        if not session:
            return None
            
        try:
            logger.debug(f"调用工具: {service_name}.{tool_name} 参数: {args}")
            result = await session.call_tool(tool_name, args)
            logger.debug(f"工具调用结果: {result}")
            return result
        except Exception as e:
            logger.error(f"调用工具 {service_name}.{tool_name} 失败: {str(e)}")
            import traceback;traceback.print_exc(file=sys.stderr)
            return None
            
    def get_available_services(self) -> list:
        """获取所有可用的MCP服务列表
        
        Returns:
            list: 可用服务列表
        """
        services = []
        for k, v in MCP_REGISTRY.items():
            if isinstance(v, dict):
                if v.get('type') == 'dynamic':
                    # 动态注册方式
                    manifest = v.get('manifest', {})
                    services.append({
                        "name": k,
                        "description": manifest.get('description', ''),
                        "id": k,
                        "type": "dynamic",
                        "displayName": manifest.get('displayName', k)
                    })
                elif v.get('type') == 'metadata':
                    # 元数据对象方式
                    metadata = v.get('metadata', {})
                    services.append({
                        "name": k,
                        "description": metadata.get('description', ''),
                        "id": k,
                        "type": "metadata",
                        "displayName": metadata.get('displayName', k)
                    })
        return services
            
    def format_available_services(self) -> str:
        """格式化可用服务列表为字符串
        
        Returns:
            str: 格式化后的服务列表字符串
        """
        services = []
        for name, info in self.services.items():
            if isinstance(info, dict):
                services.append(f"- {name}: {info.get('tool_description', '')}")
            else:
                services.append(f"- {name}: {getattr(info, 'instructions', '')}")
        return "\n".join(services)
            
    async def cleanup(self):
        """清理所有MCP服务连接"""
        logger.info("正在清理MCP服务连接...")
        try:
            await self.exit_stack.aclose()
            self.services.clear();self.tools_cache.clear()
            logger.info("MCP服务连接清理完成")
        except Exception as e:
            logger.error(f"清理MCP服务连接时出错: {str(e)}")
            import traceback;traceback.print_exc(file=sys.stderr)

    def get_mcp(self, name): 
        """获取MCP服务，支持动态注册和元数据对象两种方式"""
        agent_info = MCP_REGISTRY.get(name)
        if agent_info is None:
            return None
        
        if isinstance(agent_info, dict):
            if agent_info.get('type') == 'dynamic':
                # 动态注册方式：返回manifest
                return agent_info.get('manifest')
            elif agent_info.get('type') == 'metadata':
                # 元数据对象方式：返回元数据
                return agent_info.get('metadata')
        
        return None

    def list_mcps(self): return list(MCP_REGISTRY.keys()) # 列出所有MCP服务 

_MCP_MANAGER=None
def get_mcp_manager():
    global _MCP_MANAGER
    if not _MCP_MANAGER:_MCP_MANAGER=MCPManager()
    return _MCP_MANAGER 