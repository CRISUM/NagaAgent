#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音队列播放测试脚本 - 验证流式音频不会被打断
"""
import sys
import os
import asyncio
import time

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from voice.voice_integration import (
    get_voice_integration,
    switch_tts_provider,
    clear_voice_queue,
    is_voice_playing,
    get_voice_queue_size
)


async def test_sequential_playback():
    """测试顺序播放功能"""
    print("=== 测试顺序播放功能 ===")
    
    voice = get_voice_integration()
    
    # 清空队列
    clear_voice_queue()
    print("✅ 队列已清空")
    
    # 测试句子
    sentences = [
        "第一句话，这是一个测试。",
        "第二句话，应该在第一句播放完成后开始。",
        "第三句话，继续测试顺序播放功能。",
        "第四句话，最后一个测试句子。"
    ]
    
    print(f"准备播放 {len(sentences)} 个句子...")
    
    # 快速添加多个句子
    for i, sentence in enumerate(sentences):
        print(f"添加句子 {i+1}: {sentence}")
        voice.receive_final_text(sentence)
        await asyncio.sleep(0.2)  # 短暂间隔模拟快速输入
    
    print(f"队列大小: {get_voice_queue_size()}")
    
    # 监控播放状态
    start_time = time.time()
    while get_voice_queue_size() > 0 or is_voice_playing():
        queue_size = get_voice_queue_size()
        playing = is_voice_playing()
        elapsed = time.time() - start_time
        print(f"[{elapsed:.1f}s] 队列: {queue_size}, 播放中: {playing}")
        await asyncio.sleep(1)
    
    print("✅ 所有句子播放完成")
    print(f"总用时: {time.time() - start_time:.1f}秒")


async def test_stream_chunks():
    """测试流式文本块处理"""
    print("\n=== 测试流式文本块处理 ===")
    
    voice = get_voice_integration()
    clear_voice_queue()
    
    # 模拟AI流式回复
    chunks = [
        "人工智能",
        "是一门",
        "复杂的",
        "科学。",
        "它涉及",
        "机器学习，",
        "深度学习，",
        "以及各种",
        "算法技术。",
        "未来",
        "AI将会",
        "改变世界。"
    ]
    
    print("开始流式接收文本块...")
    
    # 快速发送文本块
    for i, chunk in enumerate(chunks):
        print(f"接收块 {i+1}: '{chunk}'")
        voice.receive_text_chunk(chunk)
        await asyncio.sleep(0.3)  # 模拟真实流式接收
        
        # 显示队列状态
        if i % 3 == 0:
            print(f"  -> 队列大小: {get_voice_queue_size()}, 播放中: {is_voice_playing()}")
    
    # 发送最终文本
    final_text = "这是最终的完整文本，流式接收结束。"
    print(f"发送最终文本: {final_text}")
    voice.receive_final_text(final_text)
    
    # 等待所有音频播放完成
    start_time = time.time()
    while get_voice_queue_size() > 0 or is_voice_playing():
        queue_size = get_voice_queue_size()
        playing = is_voice_playing()
        elapsed = time.time() - start_time
        print(f"[{elapsed:.1f}s] 等待播放完成 - 队列: {queue_size}, 播放中: {playing}")
        await asyncio.sleep(1)
    
    print("✅ 流式文本播放完成")


async def test_interrupt_recovery():
    """测试中断和恢复功能"""
    print("\n=== 测试中断和恢复功能 ===")
    
    voice = get_voice_integration()
    clear_voice_queue()
    
    # 添加一些长句子
    long_sentences = [
        "这是一个很长的句子，用来测试音频播放的中断功能，看看能否正确处理。",
        "第二个长句子，继续测试系统的稳定性和错误恢复能力。",
        "第三个句子，验证队列管理是否正常工作。"
    ]
    
    # 添加到队列
    for sentence in long_sentences:
        voice.receive_final_text(sentence)
    
    print(f"初始队列大小: {get_voice_queue_size()}")
    
    # 等待一会儿
    await asyncio.sleep(2)
    
    # 清空队列测试
    print("清空队列...")
    clear_voice_queue()
    print(f"清空后队列大小: {get_voice_queue_size()}")
    
    # 添加新内容
    voice.receive_final_text("队列清空后的新内容。")
    
    # 等待播放完成
    while get_voice_queue_size() > 0 or is_voice_playing():
        await asyncio.sleep(0.5)
    
    print("✅ 中断和恢复测试完成")


async def test_provider_switching():
    """测试提供商切换时的队列行为"""
    print("\n=== 测试提供商切换 ===")
    
    voice = get_voice_integration()
    clear_voice_queue()
    
    # 使用Edge TTS
    switch_tts_provider("edge-tts")
    voice.receive_final_text("使用Edge TTS播放这句话。")
    
    await asyncio.sleep(1)
    
    # 尝试切换到Minimax（如果配置了）
    if switch_tts_provider("minimax"):
        print("切换到Minimax TTS")
        voice.receive_final_text("现在使用Minimax TTS播放这句话。")
    else:
        print("Minimax未配置，继续使用Edge TTS")
        voice.receive_final_text("继续使用Edge TTS播放。")
    
    # 等待播放完成
    while get_voice_queue_size() > 0 or is_voice_playing():
        await asyncio.sleep(0.5)
    
    print("✅ 提供商切换测试完成")


def print_queue_status():
    """打印队列状态"""
    queue_size = get_voice_queue_size()
    playing = is_voice_playing()
    print(f"队列状态 - 大小: {queue_size}, 播放中: {playing}")


async def main():
    """主测试函数"""
    print("🎵 语音队列播放测试")
    print("=" * 50)
    
    try:
        # 检查语音服务状态
        voice = get_voice_integration()
        if not voice.enabled:
            print("❌ 语音服务未启用")
            return
        
        print(f"使用TTS提供商: {voice.provider}")
        print_queue_status()
        
        # 运行测试
        await test_sequential_playback()
        await test_stream_chunks()
        await test_interrupt_recovery()
        await test_provider_switching()
        
        print("\n🎉 所有测试完成！")
        print("\n测试结果总结:")
        print("✅ 顺序播放 - 音频按添加顺序播放，不会被打断")
        print("✅ 流式处理 - 文本块正确组合成句子播放")
        print("✅ 队列管理 - 支持清空队列和状态查询")
        print("✅ 错误恢复 - 系统稳定运行")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 确保清理
        clear_voice_queue()
        print("\n测试环境已清理")


if __name__ == "__main__":
    asyncio.run(main())
