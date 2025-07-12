#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音集成使用示例 - 展示如何在项目中使用多TTS服务
"""
import sys
import os
import asyncio

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from voice.voice_integration import (
    get_voice_integration,
    switch_tts_provider,
    get_tts_provider_info,
    set_minimax_voice_config
)


def basic_usage_example():
    """基本使用示例"""
    print("=== 基本使用示例 ===")
    
    # 获取语音集成实例
    voice = get_voice_integration()
    
    # 检查当前配置
    info = get_tts_provider_info()
    print(f"当前使用: {info['current_provider']}")
    print(f"可用服务: {', '.join(info['available_providers'])}")
    
    # 播放简单文本
    voice.receive_final_text("欢迎使用NagaAgent语音系统！")
    print("✅ 基本播放完成")


def provider_switching_example():
    """提供商切换示例"""
    print("\n=== 提供商切换示例 ===")
    
    voice = get_voice_integration()
    
    # 切换到Edge TTS
    if switch_tts_provider("edge-tts"):
        print("✅ 切换到Edge TTS")
        voice.receive_final_text("现在使用的是Edge TTS服务。")
    
    # 切换到Minimax（如果配置了）
    if switch_tts_provider("minimax"):
        print("✅ 切换到Minimax TTS")
        voice.receive_final_text("现在使用的是Minimax TTS服务，音质更佳。")
    else:
        print("❌ Minimax未配置，继续使用Edge TTS")


def stream_usage_example():
    """流式使用示例"""
    print("\n=== 流式使用示例 ===")
    
    voice = get_voice_integration()
    
    # 模拟流式对话响应
    dialogue_chunks = [
        "根据您的问题，",
        "我认为",
        "人工智能",
        "确实在",
        "改变世界。",
        "它不仅提高了",
        "工作效率，",
        "还为我们",
        "带来了",
        "新的可能性。"
    ]
    
    print("模拟AI流式回复...")
    for chunk in dialogue_chunks:
        voice.receive_text_chunk(chunk)
        # 在实际应用中，这里不需要sleep，文本块会自然地流式到达
    
    # 结束对话
    voice.receive_final_text("希望这个回答对您有帮助。")
    print("✅ 流式对话完成")


def minimax_config_example():
    """Minimax配置示例"""
    print("\n=== Minimax配置示例 ===")
    
    # 切换到Minimax
    if not switch_tts_provider("minimax"):
        print("❌ Minimax未配置，跳过此示例")
        return
    
    voice = get_voice_integration()
    
    # 设置不同的语音风格
    styles = [
        {"voice_id": "male-qn-qingse", "emotion": "happy", "desc": "开心的男声"},
        {"voice_id": "female-shaonv", "emotion": "calm", "desc": "平静的女声"},
        {"voice_id": "audiobook_male_1", "emotion": "happy", "desc": "有声书男声"}
    ]
    
    for style in styles:
        print(f"测试: {style['desc']}")
        set_minimax_voice_config(
            voice_id=style['voice_id'],
            emotion=style['emotion']
        )
        voice.receive_final_text(f"这是{style['desc']}的演示。")
    
    print("✅ Minimax配置演示完成")


async def chatbot_simulation():
    """聊天机器人模拟"""
    print("\n=== 聊天机器人模拟 ===")
    
    voice = get_voice_integration()
    
    # 模拟用户提问和AI回答
    conversations = [
        {
            "user": "你好，请介绍一下自己",
            "ai_chunks": [
                "你好！",
                "我是NagaAgent，",
                "一个智能助手。",
                "我可以帮助您",
                "处理各种任务，",
                "包括回答问题、",
                "提供建议等。"
            ],
            "ai_final": "很高兴为您服务！"
        },
        {
            "user": "天气怎么样？",
            "ai_chunks": [
                "抱歉，",
                "我目前",
                "无法获取",
                "实时天气信息。"
            ],
            "ai_final": "建议您查看天气应用或网站获取准确信息。"
        }
    ]
    
    for conv in conversations:
        print(f"\n用户: {conv['user']}")
        
        # 模拟AI思考时间
        await asyncio.sleep(1)
        
        print("AI回复中...")
        # 流式发送回复
        for chunk in conv['ai_chunks']:
            voice.receive_text_chunk(chunk)
            await asyncio.sleep(0.3)  # 模拟生成延迟
        
        # 发送最终回复
        voice.receive_final_text(conv['ai_final'])
        
        # 等待播放完成
        await asyncio.sleep(2)
    
    print("✅ 聊天模拟完成")


def integration_in_project():
    """项目集成示例"""
    print("\n=== 项目集成指南 ===")
    
    code_examples = [
        {
            "title": "在conversation_core.py中集成",
            "code": '''
from voice.voice_integration import get_voice_integration

# 在对话核心中添加语音播放
def stream_response_with_voice(response_text):
    voice = get_voice_integration()
    
    # 对于流式响应
    for chunk in response_chunks:
        voice.receive_text_chunk(chunk)
        yield chunk
    
    # 响应结束
    voice.receive_final_text(complete_response)
'''
        },
        {
            "title": "在API服务中集成",
            "code": '''
from voice.voice_integration import switch_tts_provider

# API端点：切换TTS服务
@app.post("/api/tts/provider")
def set_tts_provider(provider: str):
    if switch_tts_provider(provider):
        return {"status": "success", "provider": provider}
    return {"status": "error", "message": "切换失败"}
'''
        },
        {
            "title": "在配置管理中集成",
            "code": '''
from voice.voice_integration import get_tts_provider_info, set_minimax_voice_config

# 获取TTS状态
def get_voice_status():
    return get_tts_provider_info()

# 更新Minimax配置
def update_voice_config(voice_id, emotion):
    return set_minimax_voice_config(voice_id=voice_id, emotion=emotion)
'''
        }
    ]
    
    for example in code_examples:
        print(f"\n{example['title']}:")
        print(example['code'])
    
    print("\n配置说明:")
    print("1. 在config.json中设置 'provider': 'minimax' 或 'edge-tts'")
    print("2. 为Minimax配置API密钥和Group ID")
    print("3. 可以在运行时动态切换服务提供商")
    print("4. 支持流式文本接收和实时语音播放")


async def main():
    """主演示函数"""
    print("🎤 NagaAgent 语音集成使用示例")
    print("=" * 50)
    
    try:
        # 基本使用
        basic_usage_example()
        await asyncio.sleep(2)
        
        # 提供商切换
        provider_switching_example()
        await asyncio.sleep(3)
        
        # 流式使用
        stream_usage_example()
        await asyncio.sleep(4)
        
        # Minimax配置
        minimax_config_example()
        await asyncio.sleep(3)
        
        # 聊天机器人模拟
        await chatbot_simulation()
        
        # 集成指南
        integration_in_project()
        
        print("\n🎉 所有示例演示完成！")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
    
    print("\n感谢使用NagaAgent语音集成系统！")


if __name__ == "__main__":
    asyncio.run(main())
