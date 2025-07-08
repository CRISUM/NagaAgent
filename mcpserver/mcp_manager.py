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
from mcpserver.dynamic_agent_registry import dynamic_registry # 动态注册系统

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
        
        # 新增：服务分类管理
        self.agent_services = {}  # Agent服务池
        self.mcp_services = {}    # MCP服务池
        self.service_type_map = {}  # 服务类型映射
        
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
            # 静默跳过重复注册，不打印信息
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
        """获取所有可用的MCP服务列表（不包含Agent服务）
        
        Returns:
            list: 可用MCP服务列表
        """
        services = []
        for k, v in MCP_REGISTRY.items():
            if isinstance(v, dict):
                if v.get('type') == 'dynamic':
                    # 检查是否已注册为Agent服务
                    if k in self.agent_services:
                        continue  # 跳过已注册为Agent的服务
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
                    # 检查是否已注册为Agent服务
                    if k in self.agent_services:
                        continue  # 跳过已注册为Agent的服务
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
        """格式化可用MCP服务列表为字符串（不包含Agent服务）
        
        Returns:
            str: 格式化后的MCP服务列表字符串
        """
        services = []
        for name, info in self.mcp_services.items():
            if isinstance(info, dict):
                services.append(f"- {name}: {info.get('description', '')}")
            else:
                services.append(f"- {name}: {getattr(info, 'instructions', '')}")
        return "\n".join(services) if services else "无可用MCP服务"

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

    # 新增：统一调用接口
    async def unified_call(self, service_name: str, tool_name: str, args: dict):
        """
        统一调用接口 - 支持MCP工具调用和Agent任务转交，严格分开
        
        Args:
            service_name: 服务名称
            tool_name: 工具名称
            args: 调用参数
        
        Returns:
            调用结果
        """
        from config import config
        # 检查是否是Agent调用
        if service_name in self.agent_services:
            if tool_name == config.mcp.agent_tool_name:
                return await self._call_agent(service_name, args)
            else:
                return {"status": "error", "message": f"Agent服务{service_name}只支持特殊工具名{config.mcp.agent_tool_name}"}
        elif service_name in self.mcp_services:
            # 普通MCP工具调用
            return await self.call_service_tool(service_name, tool_name, args)
        else:
            return {"status": "error", "message": f"服务{service_name}未注册为MCP或Agent"}

    async def _call_agent(self, agent_name: str, args: dict):
        """
        调用Agent处理任务
        
        Args:
            agent_name: Agent名称
            args: 任务参数
        
        Returns:
            Agent处理结果
        """
        try:
            # 从动态注册系统获取Agent实例
            agent = get_agent_instance(agent_name)
            if not agent:
                raise ValueError(f"Agent {agent_name} 未找到")
            
            # 调用Agent的handle_handoff方法
            if hasattr(agent, 'handle_handoff'):
                result = await agent.handle_handoff(args)
                return result
            else:
                raise ValueError(f"Agent {agent_name} 不支持handle_handoff方法")
                
        except Exception as e:
            logger.error(f"调用Agent {agent_name} 失败: {e}")
            return {"status": "error", "message": str(e)}

    def register_agent_service(self, agent_name: str, agent_instance):
        """
        注册Agent为服务
        
        Args:
            agent_name: Agent名称
            agent_instance: Agent实例
        """
        from config import config
        
        # 注册到Agent服务池
        self.agent_services[agent_name] = {
            "type": "agent",
            "agent_name": agent_name,
            "instance": agent_instance,
            "tools": [config.mcp.agent_tool_name],  # 支持agent工具名
            "description": f"Agent服务: {agent_name}"
        }
        
        # 更新服务类型映射
        self.service_type_map[agent_name] = "agent"
        
        # 同时注册handoff服务
        self.register_handoff(
            service_name=agent_name,
            tool_name=config.mcp.agent_tool_name,
            tool_description=f"将任务转交给{agent_name}处理",
            input_schema={
                "type": "object",
                "properties": {
                    "action": {"type": "string"},
                    "data": {"type": "object"}
                }
            },
            agent_name=agent_name
        )
        
        logger.info(f"注册Agent服务: {agent_name}")

    def register_mcp_service(self, service_name: str, service_config: dict):
        """
        注册MCP服务
        
        Args:
            service_name: 服务名称
            service_config: 服务配置
        """
        # 注册到MCP服务池
        self.mcp_services[service_name] = service_config
        
        # 更新服务类型映射
        self.service_type_map[service_name] = "mcp"
        
        logger.info(f"注册MCP服务: {service_name}")

    def get_service_type(self, service_name: str) -> str:
        """
        获取服务类型
        
        Args:
            service_name: 服务名称
        
        Returns:
            服务类型: "agent" 或 "mcp" 或 "unknown"
        """
        if service_name in self.agent_services:
            return "agent"
        elif service_name in self.mcp_services:
            return "mcp"
        else:
            return "unknown"

    def get_available_services_filtered(self) -> dict:
        """
        获取过滤后的可用服务列表，MCP服务和Agent服务彻底分开
        """
        from config import config
        result = {
            "mcp_services": [],
            "agent_services": []
        }
        # MCP服务（排除已注册为Agent的服务）
        for service_name, service_info in self.mcp_services.items():
            if config.mcp.exclude_agent_tools_from_mcp and service_name in self.agent_services:
                continue
            result["mcp_services"].append({
                "name": service_name,
                "description": service_info.get("description", ""),
                "type": "mcp"
            })
        # Agent服务
        for agent_name, agent_info in self.agent_services.items():
            result["agent_services"].append({
                "name": agent_name,
                "description": agent_info.get("description", ""),
                "type": "agent",
                "tool_name": config.mcp.agent_tool_name
            })
        return result

    def auto_register_services(self):
        """
        自动注册所有服务，MCP服务和Agent服务彻底分开，使用agentType区分
        """
        from config import config
        
        # 清空现有服务，避免重复注册
        self.agent_services.clear()
        self.mcp_services.clear()
        self.service_type_map.clear()
        
        # 自动注册Agent服务，并根据agentType决定是否注册为MCP服务
        if config.mcp.auto_discover_agents:
            for agent_name, manifest in dynamic_registry.agents.items():
                try:
                    agent_instance = get_agent_instance(agent_name)
                    if agent_instance:
                        # 读取agentType，默认"synchronous"
                        agent_type = manifest.get("agentType", "synchronous").lower()
                        self.register_agent_service(agent_name, agent_instance)
                        print(f"✅ 注册Agent服务: {agent_name} (type: {agent_type})")
                        # 只有agentType=="mcp"才注册为MCP服务
                        if agent_type == "mcp":
                            self.register_mcp_service(agent_name, {
                                'type': 'dynamic',
                                'manifest': manifest,
                                'instance': agent_instance,
                                'is_distributed': manifest.get('is_distributed', False),
                                'server_id': manifest.get('server_id', None)
                            })
                            print(f"✅ 注册MCP服务: {agent_name}")
                            # 注册handoff
                            self.register_handoff(
                                service_name=agent_name,
                                tool_name=f"{agent_name}_handoff",
                                tool_description=manifest.get('description', f'{agent_name}服务'),
                                input_schema=manifest.get('inputSchema', {
                                    "type": "object",
                                    "properties": {
                                        "action": {"type": "string", "description": "操作类型"},
                                        "query": {"type": "string", "description": "查询内容"}
                                    },
                                    "required": ["action"]
                                }),
                                agent_name=agent_name,
                                strict_schema=False
                            )
                    else:
                        print(f"❌ 无法创建Agent实例: {agent_name}")
                except Exception as e:
                    print(f"❌ 注册Agent服务失败 {agent_name}: {e}")
        
        # 自动注册MCP服务（仅注册未被动态Agent覆盖的MCP工具服务）
        if config.mcp.auto_discover_mcp:
            for service_name, service_info in MCP_REGISTRY.items():
                try:
                    # 跳过已注册为Agent服务的（即动态Agent）
                    if service_name in self.agent_services:
                        continue
                    self.register_mcp_service(service_name, service_info)
                    print(f"✅ 注册MCP服务: {service_name}")
                    manifest = service_info.get('manifest', {})
                    self.register_handoff(
                        service_name=service_name,
                        tool_name=f"{service_name}_handoff",
                        tool_description=manifest.get('description', f'{service_name}服务'),
                        input_schema=manifest.get('inputSchema', {
                            "type": "object",
                            "properties": {
                                "action": {"type": "string", "description": "操作类型"},
                                "query": {"type": "string", "description": "查询内容"}
                            },
                            "required": ["action"]
                        }),
                        agent_name=service_name,
                        strict_schema=False
                    )
                except Exception as e:
                    print(f"❌ 注册MCP服务失败 {service_name}: {e}")
        
        print(f"🎉 自动注册完成 - Agent服务: {len(self.agent_services)}, MCP服务: {len(self.mcp_services)}")

    def list_agent_services(self) -> list:
        """
        列出所有Agent服务
        
        Returns:
            list: Agent服务列表
        """
        return list(self.agent_services.keys())

    def list_mcp_services(self) -> list:
        """
        列出所有MCP服务
        
        Returns:
            list: MCP服务列表
        """
        return list(self.mcp_services.keys())

    def is_agent_service(self, service_name: str) -> bool:
        """
        检查是否是Agent服务
        
        Args:
            service_name: 服务名称
        
        Returns:
            bool: 是否是Agent服务
        """
        return service_name in self.agent_services

    def is_mcp_service(self, service_name: str) -> bool:
        """
        检查是否是MCP服务
        
        Args:
            service_name: 服务名称
        
        Returns:
            bool: 是否是MCP服务
        """
        return service_name in self.mcp_services

_MCP_MANAGER=None
def get_mcp_manager():
    global _MCP_MANAGER
    if not _MCP_MANAGER:_MCP_MANAGER=MCPManager()
    return _MCP_MANAGER 