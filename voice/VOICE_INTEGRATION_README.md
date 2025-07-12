# NagaAgent 语音集成系统

本文档介绍了NagaAgent中集成的多TTS服务支持，包括免费的Edge TTS和高质量的Minimax TTS。

## 🎯 功能特性

### ✅ 支持的TTS服务
- **Edge TTS**: 微软免费语音服务，支持多种语言和语音
- **Minimax TTS**: 高质量商业语音服务，支持情感控制和更自然的语音

### ✅ 核心功能
- 🔄 **动态切换**: 运行时无缝切换TTS服务提供商
- 📡 **流式支持**: 支持流式文本接收和实时语音播放
- 🎛️ **配置管理**: 灵活的配置系统，支持多种语音参数
- 🔧 **错误处理**: 自动回退机制，确保服务稳定性
- 🎨 **情感控制**: Minimax支持多种情感和语音风格

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

关键依赖包括：
- `websockets>=12.0` - WebSocket支持
- `pydub>=0.25.1` - 音频处理
- `aiohttp>=3.11.18` - 异步HTTP客户端

### 2. 配置TTS服务

在 `config.json` 中配置：

```json
{
  "tts": {
    "provider": "edge-tts",
    "default_format": "mp3",
    "default_speed": 1.0,
    "minimax_api_key": "your_minimax_api_key",
    "minimax_group_id": "your_minimax_group_id",
    "minimax_model": "speech-02-hd",
    "minimax_voice_id": "male-qn-qingse",
    "minimax_emotion": "happy"
  }
}
```

### 3. 基本使用

```python
from voice.voice_integration import get_voice_integration

# 获取语音集成实例
voice = get_voice_integration()

# 播放文本
voice.receive_final_text("你好，欢迎使用NagaAgent！")

# 流式播放
voice.receive_text_chunk("这是")
voice.receive_text_chunk("流式")
voice.receive_text_chunk("文本。")
```

## 📖 详细使用

### TTS服务切换

```python
from voice.voice_integration import switch_tts_provider, get_tts_provider_info

# 查看当前状态
info = get_tts_provider_info()
print(f"当前提供商: {info['current_provider']}")
print(f"可用提供商: {info['available_providers']}")

# 切换到Edge TTS
switch_tts_provider("edge-tts")

# 切换到Minimax TTS
switch_tts_provider("minimax")
```

### Minimax配置管理

```python
from voice.voice_integration import set_minimax_voice_config

# 设置语音风格
set_minimax_voice_config(
    voice_id="female-shaonv",
    emotion="calm",
    model="speech-02-hd"
)
```

### 服务测试

```python
import asyncio
from voice.voice_integration import test_tts_provider

# 测试当前提供商
async def test_current():
    result = await test_tts_provider()
    print(f"当前服务可用: {result}")

# 测试特定提供商
async def test_specific():
    edge_ok = await test_tts_provider("edge-tts")
    minimax_ok = await test_tts_provider("minimax")
    print(f"Edge TTS: {edge_ok}, Minimax: {minimax_ok}")

asyncio.run(test_current())
```

## 🛠️ 配置详解

### TTS提供商配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `provider` | string | "edge-tts" | TTS服务提供商 |
| `default_format` | string | "mp3" | 音频格式 |
| `default_speed` | float | 1.0 | 播放速度 |

### Minimax特有配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `minimax_api_key` | string | "" | API密钥 |
| `minimax_group_id` | string | "" | 组ID |
| `minimax_model` | string | "speech-02-hd" | 模型版本 |
| `minimax_voice_id` | string | "male-qn-qingse" | 语音ID |
| `minimax_emotion` | string | "happy" | 情感设置 |

### 可用的Minimax语音

| 语音ID | 描述 | 性别 | 特点 |
|--------|------|------|------|
| `male-qn-qingse` | 清澈男声 | 男 | 清晰自然 |
| `female-shaonv` | 少女女声 | 女 | 甜美清新 |
| `audiobook_male_1` | 有声书男声1 | 男 | 适合朗读 |
| `audiobook_female_1` | 有声书女声1 | 女 | 适合朗读 |
| `presenter_male` | 播音员男声 | 男 | 专业播音 |
| `presenter_female` | 播音员女声 | 女 | 专业播音 |

### 支持的情感

- `happy` - 开心
- `calm` - 平静
- `excited` - 兴奋
- `sad` - 悲伤
- `angry` - 生气
- `neutral` - 中性

## 🔧 高级功能

### 在对话系统中集成

```python
# conversation_core.py 示例集成
from voice.voice_integration import get_voice_integration

class ConversationCore:
    def __init__(self):
        self.voice = get_voice_integration()
    
    def stream_response_with_voice(self, user_input):
        # 生成回复并同时播放
        for chunk in self.generate_response(user_input):
            # 发送给用户界面
            yield chunk
            # 同时发送给语音系统
            self.voice.receive_text_chunk(chunk)
        
        # 响应结束
        self.voice.receive_final_text(complete_response)
```

### API接口集成

```python
# api_server.py 示例集成
from fastapi import FastAPI
from voice.voice_integration import switch_tts_provider, get_tts_provider_info

app = FastAPI()

@app.get("/api/voice/status")
def get_voice_status():
    return get_tts_provider_info()

@app.post("/api/voice/provider")
def set_voice_provider(provider: str):
    success = switch_tts_provider(provider)
    return {"success": success, "provider": provider}
```

### 错误处理和回退

系统内置了多层错误处理：

1. **配置验证**: 启动时检查配置完整性
2. **连接测试**: 支持测试服务可用性
3. **自动回退**: Minimax失败时自动切换到Edge TTS
4. **音频播放回退**: pydub失败时使用系统播放器

## 📊 性能对比

| 特性 | Edge TTS | Minimax TTS |
|------|----------|-------------|
| **费用** | 免费 | 按使用量计费 |
| **音质** | 良好 | 优秀 |
| **延迟** | 低 | 中等 |
| **语音数量** | 多 | 精选高质量 |
| **情感控制** | 有限 | 丰富 |
| **语言支持** | 广泛 | 主要中英文 |

## 🧪 测试和调试

### 运行测试套件

```bash
# 完整测试
python test_voice_integration.py

# 使用示例
python voice_integration_examples.py
```

### 调试日志

启用详细日志：

```python
import logging
logging.getLogger("VoiceIntegration").setLevel(logging.DEBUG)
```

### 常见问题

1. **Minimax连接失败**
   - 检查API密钥和Group ID
   - 确认网络连接
   - 验证账户余额

2. **音频播放失败**
   - 安装pydub: `pip install pydub`
   - 确保系统有音频播放器
   - 检查音频设备

3. **WebSocket连接问题**
   - 检查防火墙设置
   - 确认websockets库版本
   - 验证SSL证书配置

## 🔄 更新和维护

### 版本兼容性

- Python 3.8+
- WebSockets 12.0+
- Pydub 0.25.1+

### 配置迁移

从旧版本升级时：

1. 备份现有配置
2. 添加新的Minimax配置项
3. 运行测试验证功能

## 📞 技术支持

如果遇到问题：

1. 查看日志输出
2. 运行测试脚本诊断
3. 检查配置文件格式
4. 验证API密钥有效性

更多信息请参考 [Minimax API文档](https://api.minimaxi.com/document/guides/text-to-speech/overview)。

---

🎉 **享受高质量的语音体验！**
