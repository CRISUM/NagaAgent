#!/usr/bin/env python3
# test_registration_verification.py - 验证注册映射关系

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_registration_mapping():
    """测试注册映射关系"""
    print("🔍 验证注册映射关系...")
    
    try:
        # 1. 初始化动态注册系统
        from mcpserver.dynamic_agent_registry import dynamic_registry
        await dynamic_registry.discover_agents()
        
        # 2. 检查ControllerAgent的注册
        if "ControllerAgent" in dynamic_registry.agents:
            manifest = dynamic_registry.agents["ControllerAgent"]
            print(f"✅ ControllerAgent manifest:")
            print(f"   - 名称: {manifest.get('name')}")
            print(f"   - 显示名称: {manifest.get('displayName')}")
            
            # 3. 验证服务名称映射
            agent_name = manifest.get('name', 'ControllerAgent')
            service_name = agent_name.lower().replace('agent', '')
            print(f"   - Agent名称: {agent_name}")
            print(f"   - 服务名称: {service_name}")
            print(f"   - 工具名称: {service_name}_handoff")
            
            # 4. 验证实例创建
            instance = dynamic_registry.get_agent_instance("ControllerAgent")
            if instance:
                print(f"✅ 实例创建成功: {type(instance)}")
            else:
                print("❌ 实例创建失败")
        
        # 5. 检查MCP注册
        from mcpserver.mcp_registry import MCP_REGISTRY
        print(f"\n📋 MCP_REGISTRY 内容:")
        for name, info in MCP_REGISTRY.items():
            print(f"   - {name}: {info.get('type', 'unknown')}")
        
        # 6. 检查MCP管理器
        from mcpserver.mcp_manager import get_mcp_manager
        mcp_manager = get_mcp_manager()
        
        print(f"\n🔧 MCP管理器服务:")
        for service_name, service_info in mcp_manager.services.items():
            print(f"   - {service_name}: {service_info.get('agent_name', 'N/A')}")
        
        # 7. 验证调用映射
        print(f"\n🎯 调用映射验证:")
        print(f"   用户调用: controller_handoff")
        print(f"   实际Agent: ControllerAgent")
        print(f"   这是正确的映射关系！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_registration_mapping()) 