#!/usr/bin/env python3
"""
🔧 Agent连接问题诊断和修复验证
测试天气助手的API连接是否正常
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.append('/home/swc/project/NagaAgent')

async def test_weather_agent():
    """测试天气助手连接"""
    print("🔍 诊断天气助手连接问题...")
    
    try:
        # 导入Agent管理器
        from mcpserver.agent_manager import get_agent_manager, call_agent
        
        # 获取管理器实例
        manager = get_agent_manager()
        
        # # 列出所有Agent
        # agents = manager.list_agents()
        # print(f"\n📋 可用Agent列表:")
        # for agent in agents:
        #     print(f"  ✓ {agent['name']} ({agent['base_name']})")
        
        # 获取天气助手详细信息
        if "WeatherAgent" in manager.agents:
            weather_config = manager.agents["WeatherAgent"]
            print(f"\n🌤️  天气助手配置:")
            print(f"  模型ID: {weather_config.id}")
            print(f"  API基础URL: {weather_config.api_base_url}")
            print(f"  API密钥: {'*' * 20 + weather_config.api_key[-6:] if weather_config.api_key else '未配置'}")
            print(f"  模型提供商: {weather_config.model_provider}")
            print(f"  温度: {weather_config.temperature}")
            
            # 测试API连接
            print(f"\n🧪 测试API连接...")
            result = await call_agent("WeatherAgent", "你好，请简单介绍一下你自己")
            
            if result['status'] == 'success':
                print(f"✅ 连接成功！")
                print(f"📝 天气助手回复: {result['result'][:200]}...")
                return True
            else:
                print(f"❌ 连接失败: {result['error']}")
                return False
        else:
            print("❌ 未找到天气助手配置")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def diagnose_connection_issues():
    """诊断连接问题"""
    print("🔧 连接问题诊断报告\n")
    
    # 1. 检查配置文件
    print("1. 📁 检查配置文件...")
    config_file = "/home/swc/project/NagaAgent/agent_configs/example_agent.json"
    if os.path.exists(config_file):
        print(f"   ✅ 配置文件存在: {config_file}")
        
        import json
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if "WeatherAgent" in config:
            weather_config = config["WeatherAgent"]
            print(f"   ✅ 天气助手配置存在")
            print(f"   🔑 API密钥: {'已配置' if weather_config.get('api_key') and not weather_config['api_key'].startswith('{{') else '未配置或使用占位符'}")
            print(f"   🌐 API基础URL: {weather_config.get('api_base_url', '未配置')}")
        else:
            print(f"   ❌ 天气助手配置不存在")
    else:
        print(f"   ❌ 配置文件不存在: {config_file}")
    
    # 2. 检查网络连接
    print(f"\n2. 🌐 检查网络连接...")
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.deepseek.com/", timeout=10) as resp:
                print(f"   ✅ DeepSeek API可访问 (状态码: {resp.status})")
    except Exception as e:
        print(f"   ❌ DeepSeek API不可访问: {e}")
    
    # 3. 测试Agent连接
    print(f"\n3. 🧪 测试Agent连接...")
    success = await test_weather_agent()
    
    # 4. 总结
    print(f"\n📊 诊断总结:")
    if success:
        print("✅ 天气助手连接正常，问题已修复！")
        print("\n🎉 修复内容:")
        print("  • 修复了配置中的占位符问题")
        print("  • 使用了有效的API密钥和基础URL")
        print("  • 添加了环境变量占位符替换功能")
    else:
        print("❌ 仍有连接问题，请检查:")
        print("  • API密钥是否有效")
        print("  • 网络连接是否正常")
        print("  • 配置文件格式是否正确")
    
    return success

def show_solution():
    """显示解决方案"""
    print("\n" + "="*60)
    print("🔧 天气助手连接错误解决方案")
    print("="*60)
    
    print("""
❌ 原始问题:
   ERROR:AgentManager:Agent '天气助手' API调用失败: LLM API调用失败: Connection error.

🔍 问题原因:
   1. 配置文件中使用了未替换的占位符 {{API_BASE_URL}} 和 {{API_KEY}}
   2. Agent管理器在加载配置时没有处理这些占位符
   3. 导致API调用时使用了空的URL和密钥

✅ 修复措施:
   1. 添加了环境变量占位符替换功能 (_replace_environment_placeholders)
   2. 在配置加载时自动处理占位符
   3. 如果占位符为空，自动使用全局配置的API设置
   4. 直接修复了天气助手配置，使用有效的API凭据

🚀 现在天气助手应该可以正常工作了！
""")

async def main():
    """主函数"""
    show_solution()
    success = await diagnose_connection_issues()
    
    if success:
        print("\n🎯 快速测试其他Agent:")
        try:
            from mcpserver.agent_manager import call_agent
            
            # 测试示例助手
            result = await call_agent("ExampleAgent", "你好")
            if result['status'] == 'success':
                print("✅ 示例助手连接正常")
            else:
                print(f"❌ 示例助手连接失败: {result['error']}")
            
            # 测试代码助手  
            result = await call_agent("CodeAgent", "你能做什么？")
            if result['status'] == 'success':
                print("✅ 代码助手连接正常")
            else:
                print(f"❌ 代码助手连接失败: {result['error']}")
                
        except Exception as e:
            print(f"❌ 测试其他Agent时出错: {e}")

if __name__ == "__main__":
    asyncio.run(main())
