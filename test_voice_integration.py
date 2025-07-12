#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音集成测试脚本 - 测试Edge TTS和Minimax TTS切换
"""
import sys
import os
import asyncio
import time

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
from voice.voice_integration import (
    get_voice_integration,
    switch_tts_provider,
    get_tts_provider_info,
    test_tts_provider,
    set_minimax_voice_config
)


def print_banner():
    """打印测试横幅"""
    print("=" * 60)
    print("        NagaAgent 语音集成测试")
    print("    支持 Edge TTS 和 Minimax TTS 切换")
    print("=" * 60)


def print_config_info():
    """打印当前配置信息"""
    print("\n=== 当前配置信息 ===")
    info = get_tts_provider_info()
    
    print(f"当前提供商: {info['current_provider']}")
    print(f"语音功能启用: {info['enabled']}")
    print(f"可用提供商: {', '.join(info['available_providers'])}")
    
    if 'minimax_config' in info:
        print("\nMinimax配置:")
        minimax = info['minimax_config']
        print(f"  模型: {minimax['model']}")
        print(f"  语音ID: {minimax['voice_id']}")
        print(f"  情感: {minimax['emotion']}")
        print(f"  API密钥已配置: {minimax['api_key_configured']}")
        print(f"  Group ID已配置: {minimax['group_id_configured']}")
    
    print()


async def test_edge_tts():
    """测试Edge TTS"""
    print("=== 测试 Edge TTS ===")
    
    # 切换到Edge TTS
    if switch_tts_provider("edge-tts"):
        print("✅ 成功切换到Edge TTS")
    else:
        print("❌ 切换到Edge TTS失败")
        return
    
    # 测试连接
    if await test_tts_provider("edge-tts"):
        print("✅ Edge TTS连接测试成功")
    else:
        print("❌ Edge TTS连接测试失败")
        return
    
    # 测试语音播放
    voice = get_voice_integration()
    test_text = "你好，这是Edge TTS测试。"
    
    print(f"播放测试文本: {test_text}")
    voice.receive_final_text(test_text)
    
    # 等待播放完成
    await asyncio.sleep(3)
    print("✅ Edge TTS测试完成\n")


async def test_minimax_tts():
    """测试Minimax TTS"""
    print("=== 测试 Minimax TTS ===")
    
    # 检查配置
    info = get_tts_provider_info()
    if "minimax" not in info['available_providers']:
        print("❌ Minimax配置不完整，跳过测试")
        print("请在config.json中配置:")
        print('  "minimax_api_key": "你的API密钥"')
        print('  "minimax_group_id": "你的Group ID"')
        return
    
    # 切换到Minimax
    if switch_tts_provider("minimax"):
        print("✅ 成功切换到Minimax TTS")
    else:
        print("❌ 切换到Minimax TTS失败")
        return
    
    # 测试连接
    print("正在测试Minimax连接...")
    if await test_tts_provider("minimax"):
        print("✅ Minimax TTS连接测试成功")
    else:
        print("❌ Minimax TTS连接测试失败")
        return
    
    # 测试语音播放
    voice = get_voice_integration()
    test_text = "你好，这是Minimax TTS测试。真正的危险不是计算机开始像人一样思考，而是人开始像计算机一样思考。"
    
    print(f"播放测试文本: {test_text}")
    voice.receive_final_text(test_text)
    
    # 等待播放完成
    await asyncio.sleep(5)
    print("✅ Minimax TTS测试完成\n")


async def test_voice_config():
    """测试语音配置"""
    print("=== 测试语音配置 ===")
    
    # 确保使用Minimax
    if not switch_tts_provider("minimax"):
        print("❌ 无法切换到Minimax，跳过配置测试")
        return
    
    # 测试不同语音配置
    configs = [
        {"voice_id": "danya_xuejie", "emotion": "neutral", "description": "女声清澈-平静"},
        {"voice_id": "audiobook_male_1", "emotion": "happy", "description": "有声书男声-开心"}
    ]
    
    voice = get_voice_integration()
    
    for i, conf in enumerate(configs):
        print(f"\n测试配置 {i+1}: {conf['description']}")
        
        # 设置配置
        if set_minimax_voice_config(voice_id=conf['voice_id'], emotion=conf['emotion']):
            print(f"✅ 配置更新成功")
        else:
            print(f"❌ 配置更新失败")
            continue
        
        # 播放测试
        test_text = f"这是{conf['description']}的测试。"
        print(f"播放: {test_text}")
        voice.receive_final_text(test_text)
        
        # 等待播放完成
        await asyncio.sleep(4)
    
    print("✅ 语音配置测试完成\n")


async def test_stream_receive():
    """测试流式接收"""
    print("=== 测试流式接收 ===")
    
    voice = get_voice_integration()
    
    # 模拟流式文本接收
    chunks = [
        "人工智能",
        "正在",
        "快速",
        "发展，",
        "它将",
        "改变",
        "我们的",
        "生活方式。",
        "这是一个",
        "令人兴奋的",
        "时代。"
    ]
    
    print("模拟流式文本接收...")
    for i, chunk in enumerate(chunks):
        print(f"接收片段 {i+1}: {chunk}")
        voice.receive_text_chunk(chunk)
        await asyncio.sleep(0.5)  # 模拟真实的流式接收间隔
    
    # 发送最终文本
    final_text = "这是最终的完整文本，用于测试流式接收功能的结束。"
    print(f"发送最终文本: {final_text}")
    voice.receive_final_text(final_text)
    
    # 等待播放完成
    await asyncio.sleep(8)
    print("✅ 流式接收测试完成\n")


def print_usage_guide():
    """打印使用指南"""
    print("=== 使用指南 ===")
    print("1. 配置文件 (config.json):")
    print('   设置 "provider": "edge-tts" 使用免费的Edge TTS')
    print('   设置 "provider": "minimax" 使用高质量的Minimax TTS')
    print()
    print("2. 代码中动态切换:")
    print("   from voice.voice_integration import switch_tts_provider")
    print('   switch_tts_provider("minimax")  # 切换到Minimax')
    print('   switch_tts_provider("edge-tts")  # 切换到Edge TTS')
    print()
    print("3. 基本使用:")
    print("   from voice.voice_integration import get_voice_integration")
    print("   voice = get_voice_integration()")
    print("   voice.receive_final_text('你好世界')")
    print()
    print("4. 流式使用:")
    print("   voice.receive_text_chunk('文本片段')")
    print("   voice.receive_final_text('最终文本')")
    print()
    print("5. Minimax配置:")
    print("   from voice.voice_integration import set_minimax_voice_config")
    print("   set_minimax_voice_config(voice_id='female-shaonv', emotion='calm')")
    print()


async def run_all_tests():
    """运行所有测试"""
    print_banner()
    print_config_info()
    
    # 检查基本配置
    voice = get_voice_integration()
    if not voice.enabled:
        print("❌ 语音功能未启用，请检查配置")
        return
    
    # 运行测试
    #await test_edge_tts()
    await test_minimax_tts()
    await test_voice_config()
    #await test_stream_receive()
    
    # print("🎉 所有测试完成！")
    # print_usage_guide()


def main():
    """主函数"""
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
    finally:
        print("感谢使用NagaAgent语音集成测试！")


if __name__ == "__main__":
    main()
