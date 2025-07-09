#!/usr/bin/env python3
# test_controller_agent.py - 测试ControllerAgent注册和实例创建

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_controller_agent():
    """测试ControllerAgent的注册和实例创建"""
    print("🔍 开始测试ControllerAgent...")
    
    try:
        # 1. 测试动态注册系统
        from mcpserver.dynamic_agent_registry import dynamic_registry
        print("✅ 导入动态注册系统成功")
        
        # 2. 发现Agent
        await dynamic_registry.discover_agents()
        print(f"✅ 发现Agent完成，共 {len(dynamic_registry.agents)} 个Agent")
        
        # 3. 检查ControllerAgent是否被发现
        if "ControllerAgent" in dynamic_registry.agents:
            print("✅ ControllerAgent被发现")
            manifest = dynamic_registry.agents["ControllerAgent"]
            print(f"   - 显示名称: {manifest.get('displayName')}")
            print(f"   - 描述: {manifest.get('description')}")
            print(f"   - 入口点: {manifest.get('entryPoint')}")
            print(f"   - 工厂函数: {manifest.get('factory')}")
        else:
            print("❌ ControllerAgent未被发现")
            print(f"   发现的Agent: {list(dynamic_registry.agents.keys())}")
            return
        
        # 4. 测试实例创建
        print("\n🔧 测试实例创建...")
        instance = dynamic_registry.get_agent_instance("ControllerAgent")
        if instance:
            print("✅ ControllerAgent实例创建成功")
            print(f"   - 实例类型: {type(instance)}")
            print(f"   - 实例名称: {getattr(instance, 'name', 'N/A')}")
            
            # 5. 测试handle_handoff方法
            if hasattr(instance, 'handle_handoff'):
                print("✅ ControllerAgent有handle_handoff方法")
                # 测试调用
                result = await instance.handle_handoff({
                    "action": "open",
                    "url": "https://www.google.com",
                    "task_type": "browser"
                })
                print(f"   - 测试调用结果: {result}")
            else:
                print("❌ ControllerAgent缺少handle_handoff方法")
        else:
            print("❌ ControllerAgent实例创建失败")
        
        # 6. 测试MCP注册
        print("\n🔧 测试MCP注册...")
        from mcpserver.mcp_registry import MCP_REGISTRY, get_agent_instance
        
        # 检查是否在MCP_REGISTRY中
        if "ControllerAgent" in MCP_REGISTRY:
            print("✅ ControllerAgent在MCP_REGISTRY中")
            agent_info = MCP_REGISTRY["ControllerAgent"]
            print(f"   - 类型: {agent_info.get('type')}")
            print(f"   - 实例: {agent_info.get('instance')}")
        else:
            print("❌ ControllerAgent不在MCP_REGISTRY中")
        
        # 7. 测试通过get_agent_instance获取
        mcp_instance = get_agent_instance("ControllerAgent")
        if mcp_instance:
            print("✅ 通过MCP注册中心获取ControllerAgent实例成功")
        else:
            print("❌ 通过MCP注册中心获取ControllerAgent实例失败")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_controller_agent()) 