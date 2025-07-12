#!/usr/bin/env python3
"""
测试占位符处理逻辑
"""

import os
import sys
import json

# 添加项目根目录到路径
sys.path.append('/home/swc/project/NagaAgent')

def test_placeholder_processing():
    """测试当前的占位符处理逻辑"""
    print("🔍 分析占位符处理问题\n")
    
    # 1. 读取配置文件
    print("1. 📁 读取配置文件...")
    config_file = "/home/swc/project/NagaAgent/agent_configs/example_agent.json"
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    weather_config = config["WeatherAgent"]
    print(f"   WeatherAgent原始配置:")
    print(f"   - api_key: {weather_config['api_key']}")
    print(f"   - api_base_url: {weather_config['api_base_url']}")
    
    # 2. 检查环境变量
    print(f"\n2. 🌐 检查环境变量...")
    api_key_env = os.getenv('API_KEY', '')
    api_base_url_env = os.getenv('API_BASE_URL', '')
    deepseek_api_key_env = os.getenv('DEEPSEEK_API_KEY', '')
    
    print(f"   - API_KEY环境变量: '{api_key_env}' (长度: {len(api_key_env)})")
    print(f"   - API_BASE_URL环境变量: '{api_base_url_env}' (长度: {len(api_base_url_env)})")
    print(f"   - DEEPSEEK_API_KEY环境变量: '{deepseek_api_key_env}' (长度: {len(deepseek_api_key_env)})")
    
    # 3. 模拟当前的占位符替换逻辑
    print(f"\n3. 🔄 模拟当前的占位符替换逻辑...")
    
    import re
    
    def simulate_current_replacement(text):
        """模拟当前agent_manager.py中的_replace_placeholders方法"""
        if not text:
            return ""
        
        processed_text = str(text)
        
        # 当前代码中只处理环境变量格式: {{ENV_VAR_NAME}}
        env_pattern = r'\{\{([A-Z_][A-Z0-9_]*)\}\}'
        for match in re.finditer(env_pattern, processed_text):
            env_var_name = match.group(1)
            env_value = os.getenv(env_var_name, '')
            processed_text = processed_text.replace(f"{{{{{env_var_name}}}}}", env_value)
        
        return processed_text
    
    api_key_result = simulate_current_replacement(weather_config['api_key'])
    api_base_url_result = simulate_current_replacement(weather_config['api_base_url'])
    
    print(f"   替换后的结果:")
    print(f"   - api_key: '{api_key_result}' (长度: {len(api_key_result)})")
    print(f"   - api_base_url: '{api_base_url_result}' (长度: {len(api_base_url_result)})")
    
    # 4. 检查全局配置
    print(f"\n4. 📋 检查全局配置文件...")
    global_config_file = "/home/swc/project/NagaAgent/config.json"
    with open(global_config_file, 'r', encoding='utf-8') as f:
        global_config = json.load(f)
    
    api_config = global_config.get('api', {})
    print(f"   全局API配置:")
    print(f"   - api_key: {api_config.get('api_key', 'None')}")
    print(f"   - base_url: {api_config.get('base_url', 'None')}")
    
    # 5. 问题分析
    print(f"\n📊 问题分析:")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    if not api_key_result and not api_base_url_result:
        print("❌ 问题确认: 占位符没有被正确替换")
        print(f"   • 配置文件中使用了占位符: {{{{API_KEY}}}} 和 {{{{API_BASE_URL}}}}")
        print(f"   • 但对应的环境变量没有设置")
        print(f"   • 当前的_replace_placeholders方法只处理环境变量")
        print(f"   • 结果: API调用时使用了空的密钥和URL")
        
        print(f"\n💡 解决方案:")
        print(f"   方案1: 设置环境变量")
        print(f"     export API_KEY='{api_config.get('api_key', '')}'")
        print(f"     export API_BASE_URL='{api_config.get('base_url', '')}'")
        
        print(f"\n   方案2: 修改agent_manager.py，在配置加载时自动回退到全局配置")
        print(f"     - 如果占位符替换后为空，使用config.json中的API配置")
        
        print(f"\n   方案3: 直接修改agent_configs/example_agent.json")
        print(f"     - 将{{{{API_KEY}}}}替换为实际的API密钥")
        print(f"     - 将{{{{API_BASE_URL}}}}替换为实际的API URL")
    else:
        print("✅ 占位符替换正常")

if __name__ == "__main__":
    test_placeholder_processing()
