# mcp_registry.py # 自动注册所有MCP服务和handoff schema
# 
# 架构说明：
# 基于动态注册系统 - 通过agent-manifest.json定义Agent元数据，支持动态加载和热插拔
# 所有Agent都通过agent-manifest.json文件进行动态注册

import importlib, inspect, os, json
from pathlib import Path
import concurrent.futures # 新增线程池支持
from mcpserver.dynamic_agent_registry import dynamic_registry

MCP_REGISTRY = {} # 全局MCP服务池

async def auto_register_mcp(mcp_dir='mcpserver'):
    """使用动态注册系统自动注册所有MCP服务"""
    print("🔄 使用动态注册系统发现Agent...")
    
    # 使用动态注册系统发现Agent
    await dynamic_registry.discover_agents()
    
    # 将动态注册的Agent同步到MCP_REGISTRY
    for agent_name, manifest in dynamic_registry.agents.items():
        try:
            # 获取Agent实例（延迟初始化）
            instance = dynamic_registry.get_agent_instance(agent_name)
            
            if instance:
                MCP_REGISTRY[agent_name] = {
                    'type': 'dynamic',
                    'manifest': manifest,
                    'instance': instance,
                    'is_distributed': manifest.get('is_distributed', False),
                    'server_id': manifest.get('server_id', None)
                }
                print(f"✅ 动态注册Agent: {agent_name}")
            else:
                print(f"❌ 动态注册Agent失败: {agent_name} - 无法创建实例")
                
        except Exception as e:
            print(f"❌ 动态注册Agent {agent_name} 失败: {e}")
    
    print(f"🎉 动态注册完成，共注册 {len(dynamic_registry.agents)} 个Agent")
    return list(dynamic_registry.agents.keys())

def auto_register_mcp_sync(mcp_dir='mcpserver'):
    """同步版本的自动注册（向后兼容）"""
    import asyncio
    return asyncio.run(auto_register_mcp(mcp_dir))

# 获取Agent实例的统一接口
def get_agent_instance(agent_name):
    """获取Agent实例 - 只支持动态注册方式"""
    if agent_name not in MCP_REGISTRY:
        return None
    
    agent_info = MCP_REGISTRY[agent_name]
    
    if agent_info['type'] == 'dynamic':
        # 动态注册方式：直接从动态注册系统获取实例
        return agent_info['instance']
    
    return None

# 获取Agent元数据的统一接口
def get_agent_metadata(agent_name):
    """获取Agent元数据 - 只支持动态注册方式"""
    if agent_name not in MCP_REGISTRY:
        return None
    
    agent_info = MCP_REGISTRY[agent_name]
    
    if agent_info['type'] == 'dynamic':
        return agent_info.get('manifest')
    
    return None

# 注册所有handoff服务 - 基于动态注册驱动
def register_all_handoffs(mcp_manager):
    """批量注册所有handoff服务 - 基于动态注册驱动"""
    registered = []
    
    # 直接从dynamic_registry获取Agent信息
    for agent_name, manifest in dynamic_registry.agents.items():
        try:
            # 获取Agent实例（延迟初始化）
            instance = dynamic_registry.get_agent_instance(agent_name)
            
            if instance:
                # 同步到MCP_REGISTRY
                MCP_REGISTRY[agent_name] = {
                    'type': 'dynamic',
                    'manifest': manifest,
                    'instance': instance,
                    'is_distributed': manifest.get('is_distributed', False),
                    'server_id': manifest.get('server_id', None)
                }
                
                service_name = manifest.get('name', agent_name).lower().replace('agent', '')
            
            # 构建handoff schema
            schema = {
                "service_name": service_name,
                "tool_name": f"{service_name}_handoff",
                    "tool_description": manifest.get('description', f'{agent_name}服务'),
                    "input_schema": manifest.get('inputSchema', {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "description": "操作类型"},
                        "query": {"type": "string", "description": "查询内容"}
                    },
                    "required": ["action"]
                }),
                "agent_name": agent_name,
                "strict_schema": False
            }
            
            # 注册到MCP管理器
            mcp_manager.register_handoff(
                service_name=schema["service_name"],
                tool_name=schema["tool_name"],
                tool_description=schema["tool_description"],
                input_schema=schema["input_schema"],
                agent_name=schema["agent_name"],
                strict_schema=schema.get("strict_schema", False)
            )
            registered.append(schema["service_name"])
        except Exception as e:
            import sys
            sys.stderr.write(f"❌ 注册Agent {agent_name} 失败: {e}\n")
    
    import sys
    sys.stderr.write(f'✅ 动态注册驱动注册完成:\n')
    sys.stderr.write(f'   - 注册服务: {registered}\n')
    sys.stderr.write(f'   - 总计注册服务: {len(registered)}\n')

# 注意：自动注册已移至conversation_core.py中处理，避免重复注册
# auto_register_mcp_sync()  # 已删除，避免重复注册