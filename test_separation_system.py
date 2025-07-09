#!/usr/bin/env python3
# test_separation_system.py - 测试MCP服务和Agent服务分离系统

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_separation_system():
    """测试MCP服务和Agent服务分离系统"""
    print("🔍 测试MCP服务和Agent服务分离系统...")
    
    try:
        # 1. 初始化动态注册系统
        from mcpserver.dynamic_agent_registry import dynamic_registry
        await dynamic_registry.discover_agents()
        print(f"✅ 发现Agent完成，共 {len(dynamic_registry.agents)} 个Agent")
        
        # 2. 初始化MCP管理器
        from mcpserver.mcp_manager import get_mcp_manager
        mcp_manager = get_mcp_manager()
        
        # 3. 自动注册服务
        mcp_manager.auto_register_services()
        print("✅ 自动注册服务完成")
        
        # 4. 测试服务分离
        print("\n📋 服务分离测试:")
        
        # Agent服务
        agent_services = mcp_manager.list_agent_services()
        print(f"Agent服务 ({len(agent_services)}): {agent_services}")
        
        # MCP服务
        mcp_services = mcp_manager.list_mcp_services()
        print(f"MCP服务 ({len(mcp_services)}): {mcp_services}")
        
        # 5. 测试服务类型判断
        print("\n🔍 服务类型判断测试:")
        for service_name in agent_services[:3]:  # 测试前3个Agent服务
            service_type = mcp_manager.get_service_type(service_name)
            is_agent = mcp_manager.is_agent_service(service_name)
            is_mcp = mcp_manager.is_mcp_service(service_name)
            print(f"  {service_name}: type={service_type}, is_agent={is_agent}, is_mcp={is_mcp}")
        
        for service_name in mcp_services[:3]:  # 测试前3个MCP服务
            service_type = mcp_manager.get_service_type(service_name)
            is_agent = mcp_manager.is_agent_service(service_name)
            is_mcp = mcp_manager.is_mcp_service(service_name)
            print(f"  {service_name}: type={service_type}, is_agent={is_agent}, is_mcp={is_mcp}")
        
        # 6. 测试可用服务列表
        print("\n📋 可用服务列表测试:")
        available_services = mcp_manager.get_available_services_filtered()
        print(f"MCP服务列表: {len(available_services['mcp_services'])} 个")
        for service in available_services['mcp_services'][:3]:
            print(f"  - {service['name']}: {service['description']}")
        
        print(f"Agent服务列表: {len(available_services['agent_services'])} 个")
        for service in available_services['agent_services'][:3]:
            print(f"  - {service['name']}: {service['description']}")
        
        # 7. 测试prompt格式化
        print("\n📝 Prompt格式化测试:")
        from conversation_core import NagaConversation
        conv = NagaConversation()
        formatted_services = conv._format_services_for_prompt(available_services)
        print("MCP服务格式化:")
        print(formatted_services['available_mcp_services'])
        print("\nAgent服务格式化:")
        print(formatted_services['available_agent_services'])
        
        # 8. 测试调用分离
        print("\n🎯 调用分离测试:")
        # 测试Agent调用
        if agent_services:
            test_agent = agent_services[0]
            result = await mcp_manager.unified_call(
                service_name=test_agent,
                tool_name="agent",
                args={"action": "test"}
            )
            print(f"Agent调用测试 ({test_agent}): {result}")
        
        # 测试MCP调用（如果有MCP服务）
        if mcp_services:
            test_mcp = mcp_services[0]
            result = await mcp_manager.unified_call(
                service_name=test_mcp,
                tool_name="test_tool",
                args={"action": "test"}
            )
            print(f"MCP调用测试 ({test_mcp}): {result}")
        
        # 9. 验证分离完整性
        print("\n✅ 分离完整性验证:")
        agent_set = set(agent_services)
        mcp_set = set(mcp_services)
        intersection = agent_set & mcp_set
        
        if not intersection:
            print("✅ 服务完全分离，无重复")
        else:
            print(f"❌ 发现重复服务: {intersection}")
        
        print(f"✅ 分离系统测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_separation_system()) 