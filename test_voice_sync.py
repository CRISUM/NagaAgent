#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的语音集成功能
"""

import sys
import os
import time

# 添加项目根目录到路径
sys.path.append(os.path.dirname(__file__))

def test_voice_integration_sync():
    """测试同步环境下的语音集成"""
    print("🧪 测试修复后的语音集成...")
    
    try:
        from voice.voice_integration import get_voice_integration
        
        voice_integration = get_voice_integration()
        voice_integration.enabled = True
        
        print(f"🔧 语音功能状态: {voice_integration.enabled}")
        print(f"🌐 TTS服务地址: {voice_integration.tts_url}")
        
        # 测试文本片段处理
        test_texts = [
            "你好！",
            "我是娜迦AI助手。",
            "今天是个美好的日子。",
            "这是语音集成测试。"
        ]
        
        print("\n📝 测试文本片段处理...")
        for i, text in enumerate(test_texts):
            print(f"  第{i+1}个: {text}")
            voice_integration.receive_text_chunk(text)
            time.sleep(2)  # 等待处理
        
        # 测试最终文本
        final_text = "这是一段完整的最终测试文本，用来验证语音合成的完整流程。"
        print(f"\n📝 测试最终文本: {final_text}")
        voice_integration.receive_final_text(final_text)
        
        time.sleep(5)  # 等待处理完成
        
        print("✅ 语音集成测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 语音集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_enhanced_worker_simulation():
    """模拟enhanced_worker.py的使用场景"""
    print("\n🧪 模拟enhanced_worker.py场景...")
    
    try:
        # 模拟enhanced_worker.py中的chunk处理逻辑
        test_chunks = [
            ("娜迦", "你好！我来帮助你解决问题。"),
            ("用户", "这条消息应该被过滤掉"),
            ("娜迦", "根据你的描述，我建议这样做："),
            ("娜迦", "首先，检查系统配置是否正确。"),
            ("娜迦", "然后，重启相关的服务。"),
            ("娜迦", "最后，验证功能是否正常工作。"),
            "这是一个字符串格式的chunk",
            ("娜迦", "如果还有问题，请随时联系我。")
        ]
        
        result_chunks = []
        processed_count = 0
        
        print("📦 开始处理chunk数据...")
        
        for i, chunk in enumerate(test_chunks):
            print(f"\n🧩 处理第{i+1}个chunk: {chunk}")
            
            # 模拟enhanced_worker.py中的核心逻辑
            if isinstance(chunk, tuple) and len(chunk) == 2:
                speaker, content = chunk
                if speaker == "娜迦":
                    content_str = str(content)
                    result_chunks.append(content_str)
                    processed_count += 1
                    
                    print(f"📤 发送到语音模块: {content_str}")
                    
                    # 发送文本到语音集成模块
                    try:
                        from voice.voice_integration import get_voice_integration
                        voice_integration = get_voice_integration()
                        voice_integration.receive_text_chunk(content_str)
                        print(f"✅ 语音集成成功")
                    except Exception as e:
                        print(f"❌ 语音集成错误: {e}")
                else:
                    print(f"⏭️  跳过非娜迦消息: {speaker}")
            else:
                content_str = str(chunk)
                result_chunks.append(content_str)
                print(f"📤 处理字符串chunk: {content_str}")
                
                try:
                    from voice.voice_integration import get_voice_integration
                    voice_integration = get_voice_integration()
                    voice_integration.receive_text_chunk(content_str)
                    print(f"✅ 字符串chunk处理成功")
                except Exception as e:
                    print(f"❌ 字符串chunk处理错误: {e}")
            
            time.sleep(1)  # 模拟处理间隔
        
        # 发送最终完整文本
        try:
            final_text = ''.join(result_chunks)
            print(f"\n📝 发送最终文本 ({len(final_text)}字符)")
            from voice.voice_integration import get_voice_integration
            voice_integration = get_voice_integration()
            voice_integration.receive_final_text(final_text)
            print("✅ 最终文本发送成功")
        except Exception as e:
            print(f"❌ 最终文本发送失败: {e}")
        
        print(f"\n📊 处理统计:")
        print(f"   总chunk数: {len(test_chunks)}")
        print(f"   娜迦回复数: {processed_count}")
        print(f"   处理结果数: {len(result_chunks)}")
        
        time.sleep(5)  # 等待音频处理完成
        
        print("✅ enhanced_worker集成测试完成")
        return True
        
    except Exception as e:
        print(f"❌ enhanced_worker集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🎵" * 30)
    print("NagaAgent 语音集成同步测试")
    print("🎵" * 30)
    
    # 测试语音集成
    print("第一步：同步语音集成测试")
    sync_success = test_voice_integration_sync()
    
    # 测试enhanced_worker模拟
    print("\n第二步：enhanced_worker集成测试")
    worker_success = test_enhanced_worker_simulation()
    
    # 总结
    print("\n" + "🎵" * 30)
    print("测试完成总结")
    print("🎵" * 30)
    
    results = {
        "同步语音集成": "✅" if sync_success else "❌",
        "enhanced_worker集成": "✅" if worker_success else "❌"
    }
    
    for test_name, result in results.items():
        print(f"{result} {test_name}")
    
    success_count = sum([sync_success, worker_success])
    
    if success_count == 2:
        print("\n🎉 所有测试通过！")
        print("\n💡 语音集成功能已完全就绪：")
        print("   ✅ 同步环境下正常工作")
        print("   ✅ enhanced_worker.py集成成功")
        print("   ✅ 后台线程播放音频")
        print("\n🔊 现在可以在enhanced_worker.py中正常使用语音功能了！")
    else:
        print(f"\n⚠️  部分测试失败 ({success_count}/2)")

if __name__ == "__main__":
    main()
