#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音集成模块 - 负责接收文本并调用TTS服务播放音频
支持Edge TTS和Minimax TTS两种服务
"""
import asyncio
import json
import logging
import base64
import tempfile
import os
import ssl
import threading
from typing import Optional, List
import aiohttp
import websockets
from pathlib import Path
from io import BytesIO

# 添加项目根目录到路径
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import config

logger = logging.getLogger("VoiceIntegration")

class VoiceIntegration:
    """语音集成类 - 负责文本接收和TTS播放，支持多种TTS服务"""
    
    def __init__(self):
        self.enabled = config.system.voice_enabled
        self.provider = getattr(config.tts, 'provider', 'edge-tts')
        
        # 通用配置
        self.tts_url = f"http://127.0.0.1:{config.tts.port}/v1/audio/speech"
        self.text_buffer = []  # 文本缓冲区
        self.sentence_endings = ['.', '!', '?', '。', '！', '？', '；', ';']
        self.min_sentence_length = 10  # 最小句子长度
        self.max_buffer_size = 5  # 最大缓冲区大小
        
        # Minimax配置
        self.api_key = getattr(config.tts, 'api_key', '')
        self.group_id = getattr(config.tts, 'group_id', '')
        self.tts_model = getattr(config.tts, 'tts_model', 'speech-02-hd')
        self.default_voice = getattr(config.tts, 'default_voice', 'male-qn-qingse')
        self.minimax_emotion = getattr(config.tts, 'minimax_emotion', 'happy')
        
        # WebSocket连接管理
        self.ws_connection = None
        self.ws_lock = threading.Lock()
        
        # 验证Minimax配置
        if self.provider == 'minimax' and (not self.api_key or not self.group_id):
            logger.warning("Minimax配置不完整，切换到Edge TTS")
            self.provider = 'edge-tts'
        
        logger.info(f"语音集成初始化完成，使用提供商: {self.provider}")
        
    def receive_text_chunk(self, text: str):
        """接收文本片段"""
        if not self.enabled:
            return
            
        if text and text.strip():
            self.text_buffer.append(text.strip())
            logger.debug(f"接收文本片段: {text[:50]}...")
            
            # 检查是否有完整句子
            self._check_and_play_sentences()
    
    def receive_final_text(self, final_text: str):
        """接收最终完整文本"""
        if not self.enabled:
            return
            
        if final_text and final_text.strip():
            logger.info(f"接收最终文本: {final_text[:100]}...")
            # 在后台线程播放最终文本
            self._play_text_in_background(final_text)
    
    def _check_and_play_sentences(self):
        """检查并播放完整句子"""
        if len(self.text_buffer) < 2:
            return
            
        # 合并缓冲区文本
        combined_text = ' '.join(self.text_buffer)
        
        # 查找句子结束位置
        sentence_end_pos = -1
        for ending in self.sentence_endings:
            pos = combined_text.rfind(ending)
            if pos > sentence_end_pos:
                sentence_end_pos = pos
        
        # 如果有完整句子且长度足够
        if sentence_end_pos > 0 and sentence_end_pos >= self.min_sentence_length:
            complete_sentence = combined_text[:sentence_end_pos + 1]
            remaining_text = combined_text[sentence_end_pos + 1:].strip()
            
            # 在后台线程播放完整句子
            self._play_text_in_background(complete_sentence)
            
            # 更新缓冲区
            if remaining_text:
                self.text_buffer = [remaining_text]
            else:
                self.text_buffer = []
        
        # 防止缓冲区过大
        if len(self.text_buffer) > self.max_buffer_size:
            # 强制播放缓冲区内容
            forced_text = ' '.join(self.text_buffer)
            self._play_text_in_background(forced_text)
            self.text_buffer = []
    
    async def _play_text(self, text: str):
        """播放文本音频"""
        try:
            # 根据配置选择TTS服务
            if self.provider == 'minimax':
                audio_data = await self._generate_minimax_audio(text)
            else:
                # 使用默认的Edge TTS或本地TTS API
                audio_data = await self._generate_audio(text)
            
            if audio_data:
                await self._play_audio(audio_data)
                logger.info(f"成功播放音频 ({self.provider}): {text[:50]}...")
            else:
                logger.warning(f"音频生成失败 ({self.provider}): {text[:50]}...")
                
        except Exception as e:
            logger.error(f"播放音频失败: {e}")
            # 如果Minimax失败，尝试回退到Edge TTS
            if self.provider == 'minimax':
                logger.info("尝试回退到Edge TTS")
                try:
                    audio_data = await self._generate_audio(text)
                    if audio_data:
                        await self._play_audio(audio_data)
                        logger.info(f"回退播放成功: {text[:50]}...")
                except Exception as fallback_error:
                    logger.error(f"回退播放也失败: {fallback_error}")
    
    async def _generate_audio(self, text: str) -> Optional[bytes]:
        """生成音频数据"""
        try:
            headers = {}
            if config.tts.require_api_key:
                headers["Authorization"] = f"Bearer {config.tts.api_key}"
            
            payload = {
                "input": text,
                "voice": config.tts.default_voice,
                "response_format": config.tts.default_format,
                "speed": config.tts.default_speed
            }
            
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    self.tts_url,
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        error_text = await response.text()
                        logger.error(f"TTS API调用失败: {response.status} - {error_text}")
                        return None
        except Exception as e:
            logger.error(f"生成音频异常: {e}")
            return None
    
    async def _play_audio(self, audio_data: bytes):
        """播放音频数据"""
        try:
            # 尝试使用pydub播放（更好的音频处理）
            if await self._play_with_pydub(audio_data):
                return
            
            # 回退到文件播放方式
            with tempfile.NamedTemporaryFile(suffix=f".{config.tts.default_format}", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            # 使用pygame播放
            await self._play_with_pygame(temp_file_path)
            
            # 清理临时文件
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
        except Exception as e:
            logger.error(f"播放音频文件失败: {e}")
    
    async def _play_with_pydub(self, audio_data: bytes) -> bool:
        """使用pydub播放音频（首选方法）"""
        try:
            from pydub import AudioSegment
            from pydub.playback import play
            
            # 从字节数据创建音频段
            audio = AudioSegment.from_file(BytesIO(audio_data), format=config.tts.default_format)
            
            # 在后台线程播放以避免阻塞
            def play_audio():
                play(audio)
            
            thread = threading.Thread(target=play_audio, daemon=True)
            thread.start()
            thread.join(timeout=30)  # 最多等待30秒
            
            return True
            
        except ImportError:
            logger.debug("pydub未安装，使用备选播放方案")
            return False
        except Exception as e:
            logger.warning(f"pydub播放失败: {e}")
            return False
    
    async def _play_audio_file(self, file_path: str):
        """播放音频文件"""
        try:
            import platform
            import subprocess
            import asyncio
            
            system = platform.system()
            
            if system == "Windows":
                # Windows使用winsound或windows media player
                try:
                    import winsound
                    os.startfile(file_path)
                except ImportError:
                    subprocess.run(["start", "", file_path], shell=True, check=False)
                except Exception as e:
                    logger.error(f"os.startfile 播放失败: {e}")
            elif system == "Darwin":  # macOS
                subprocess.run(["afplay", file_path], check=False)
            elif system == "Linux":
                # Linux尝试多种播放器
                players = ["aplay", "paplay", "mpg123", "mpv", "vlc", "xdg-open"]
                for player in players:
                    try:
                        result = subprocess.run([player, file_path], 
                                               check=False, 
                                               capture_output=True, 
                                               timeout=10)
                        if result.returncode == 0:
                            break
                    except (subprocess.TimeoutExpired, FileNotFoundError):
                        continue
                else:
                    logger.warning("找不到可用的音频播放器")
            else:
                logger.warning(f"不支持的操作系统: {system}")
                
        except Exception as e:
            logger.error(f"系统播放器调用失败: {e}")
            # 尝试使用 pygame 作为备选方案
            try:
                await self._play_with_pygame(file_path)
            except Exception as pygame_error:
                logger.error(f"pygame播放也失败: {pygame_error}")
    
    async def _play_with_pygame(self, file_path: str):
        """使用pygame播放音频（备选方案）"""
        try:
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            
            # 等待播放完成
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)
                
        except ImportError:
            logger.warning("pygame未安装，无法作为备选播放器")
        except Exception as e:
            logger.error(f"pygame播放失败: {e}")
    
    def _play_text_in_background(self, text: str):
        """在后台线程中播放文本音频"""
        import threading
        
        def run_in_thread():
            """在线程中运行异步函数"""
            try:
                # 创建新的事件循环
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(self._play_text(text))
                finally:
                    loop.close()
            except Exception as e:
                logger.error(f"后台播放音频失败: {e}")
        
        # 在后台线程中运行
        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()
    
    async def _establish_minimax_connection(self):
        """建立Minimax WebSocket连接"""
        url = "wss://api.minimaxi.com/ws/v1/t2a_v2"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        try:
            ws = await websockets.connect(url, additional_headers=headers, ssl=ssl_context)
            connected = json.loads(await ws.recv())
            if connected.get("event") == "connected_success":
                logger.info("Minimax WebSocket连接成功")
                return ws
            else:
                logger.error(f"Minimax连接失败: {connected}")
                return None
        except Exception as e:
            logger.error(f"Minimax WebSocket连接异常: {e}")
            return None
    
    async def _start_minimax_task(self, websocket):
        """启动Minimax任务"""
        start_msg = {
            "event": "task_start",
            "model": self.tts_model,
            "voice_setting": {
                "voice_id": self.default_voice,
                "speed": config.tts.default_speed,
                "vol": 1,
                "pitch": 0,
                "emotion": self.minimax_emotion
            },
            "audio_setting": {
                "sample_rate": 32000,
                "bitrate": 128000,
                "format": config.tts.default_format,
                "channel": 1
            }
        }
        
        await websocket.send(json.dumps(start_msg))
        response = json.loads(await websocket.recv())
        return response.get("event") == "task_started"
    
    async def _continue_minimax_task(self, websocket, text):
        """继续Minimax任务并收集音频数据"""
        await websocket.send(json.dumps({
            "event": "task_continue",
            "text": text
        }))
        
        audio_chunks = []
        try:
            while True:
                response = json.loads(await websocket.recv())
                if "data" in response and "audio" in response["data"]:
                    audio = response["data"]["audio"]
                    audio_chunks.append(audio)
                if response.get("is_final"):
                    break
        except Exception as e:
            logger.error(f"接收音频数据异常: {e}")
        
        return "".join(audio_chunks)
    
    async def _close_minimax_connection(self, websocket):
        """关闭Minimax连接"""
        if websocket:
            try:
                await websocket.send(json.dumps({"event": "task_finish"}))
                await websocket.close()
                logger.info("Minimax连接已关闭")
            except Exception as e:
                logger.error(f"关闭Minimax连接异常: {e}")
    
    async def _generate_minimax_audio(self, text: str) -> Optional[bytes]:
        """使用Minimax生成音频"""
        try:
            ws = await self._establish_minimax_connection()
            if not ws:
                return None
            
            # 启动任务
            if not await self._start_minimax_task(ws):
                logger.error("Minimax任务启动失败")
                await self._close_minimax_connection(ws)
                return None
            
            # 继续任务并获取音频
            hex_audio = await self._continue_minimax_task(ws, text)
            
            # 关闭连接
            await self._close_minimax_connection(ws)
            
            # 将十六进制数据转换为字节
            if hex_audio:
                return bytes.fromhex(hex_audio)
            return None
            
        except Exception as e:
            logger.error(f"Minimax音频生成异常: {e}")
            return None
    
    def switch_provider(self, provider: str):
        """切换TTS服务提供商"""
        if provider not in ['edge-tts', 'minimax']:
            logger.error(f"不支持的TTS提供商: {provider}")
            return False
        
        if provider == 'minimax' and (not self.api_key or not self.group_id):
            logger.error("Minimax配置不完整，无法切换")
            return False
        
        old_provider = self.provider
        self.provider = provider
        config.tts.provider = provider
        
        logger.info(f"TTS提供商已从 {old_provider} 切换到 {provider}")
        return True
    
    def get_provider_info(self) -> dict:
        """获取当前提供商信息"""
        info = {
            "current_provider": self.provider,
            "enabled": self.enabled,
            "available_providers": []
        }
        
        # 检查可用的提供商
        info["available_providers"].append("edge-tts")
        
        if self.api_key and self.group_id:
            info["available_providers"].append("minimax")
        
        # 添加配置信息
        if self.provider == 'minimax':
            info["minimax_config"] = {
                "model": self.tts_model,
                "voice_id": self.default_voice,
                "emotion": self.minimax_emotion,
                "api_key_configured": bool(self.api_key),
                "group_id_configured": bool(self.group_id)
            }
        
        return info
    
    def set_minimax_config(self, voice_id: str = None, emotion: str = None, model: str = None):
        """动态设置Minimax配置"""
        changed = []
        
        if voice_id and voice_id != self.default_voice:
            self.default_voice = voice_id
            config.tts.default_voice = voice_id
            changed.append(f"voice_id: {voice_id}")
        
        if emotion and emotion != self.minimax_emotion:
            self.minimax_emotion = emotion
            config.tts.minimax_emotion = emotion
            changed.append(f"emotion: {emotion}")
        
        if model and model != self.tts_model:
            self.tts_model = model
            config.tts.tts_model = model
            changed.append(f"model: {model}")
        
        if changed:
            logger.info(f"Minimax配置已更新: {', '.join(changed)}")
            return True
        return False
    
    async def test_provider(self, provider: str = None) -> bool:
        """测试TTS提供商是否可用"""
        test_provider = provider or self.provider
        test_text = "这是一个TTS服务测试。"
        
        try:
            if test_provider == 'minimax':
                audio_data = await self._generate_minimax_audio(test_text)
            else:
                audio_data = await self._generate_audio(test_text)
            
            success = audio_data is not None and len(audio_data) > 0
            logger.info(f"TTS提供商 {test_provider} 测试{'成功' if success else '失败'}")
            return success
            
        except Exception as e:
            logger.error(f"TTS提供商 {test_provider} 测试异常: {e}")
            return False

# 全局实例
_voice_integration_instance: Optional[VoiceIntegration] = None

def get_voice_integration() -> VoiceIntegration:
    """获取语音集成实例（单例模式）"""
    global _voice_integration_instance
    if _voice_integration_instance is None:
        _voice_integration_instance = VoiceIntegration()
    return _voice_integration_instance

def switch_tts_provider(provider: str) -> bool:
    """全局切换TTS提供商"""
    voice = get_voice_integration()
    return voice.switch_provider(provider)

def get_tts_provider_info() -> dict:
    """获取TTS提供商信息"""
    voice = get_voice_integration()
    return voice.get_provider_info()

async def test_tts_provider(provider: str = None) -> bool:
    """测试TTS提供商"""
    voice = get_voice_integration()
    return await voice.test_provider(provider)

def set_minimax_voice_config(voice_id: str = None, emotion: str = None, model: str = None) -> bool:
    """设置Minimax语音配置"""
    voice = get_voice_integration()
    return voice.set_minimax_config(voice_id, emotion, model)