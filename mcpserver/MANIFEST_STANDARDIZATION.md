# Agent Manifest 标准化规范

## 概述

本文档定义了 `agent-manifest.json` 文件的标准化规范，确保所有Agent的manifest文件具有一致的结构和字段。

## 必需字段

### 基础信息
- `name`: Agent的唯一标识符（字符串）
- `displayName`: Agent的显示名称（字符串）
- `version`: Agent版本号（字符串，格式：x.y.z）
- `description`: Agent功能描述（字符串）
- `author`: 作者或模块名称（字符串）

### 类型和入口
- `agentType`: Agent类型，必须是以下之一：
  - `"mcp"`: MCP服务类型
  - `"synchronous"`: 同步Agent类型
  - `"asynchronous"`: 异步Agent类型
- `entryPoint`: 入口点配置
  - `module`: 模块路径（字符串）
  - `class`: 类名（字符串）

## 可选字段

### 工厂配置
- `factory`: 工厂函数配置（对象）
  - `create_instance`: 创建实例的函数名（字符串）
  - `validate_config`: 验证配置的函数名（字符串，可选）
  - `get_dependencies`: 获取依赖的函数名（字符串，可选）

### 通信配置
- `communication`: 通信配置（对象）
  - `protocol`: 协议类型（字符串，默认"stdio"）
  - `timeout`: 超时时间（整数，毫秒）

### 能力描述
- `capabilities`: 能力描述（对象）
  - `invocationCommands`: 调用命令列表（数组）
    - `command`: 命令名称（字符串）
    - `description`: 命令描述（字符串）
    - `example`: 调用示例（字符串）

### 输入模式
- `inputSchema`: 输入模式定义（对象，JSON Schema格式）
  - `type`: 类型（字符串）
  - `properties`: 属性定义（对象）
  - `required`: 必需字段列表（数组）

### 配置模式
- `configSchema`: 配置模式定义（对象）
  - 键值对形式，键为配置项名称，值为类型描述

### 运行时信息
- `runtime`: 运行时信息（对象）
  - `instance`: 实例对象（null或对象）
  - `is_initialized`: 是否已初始化（布尔值）
  - `last_used`: 最后使用时间（null或时间戳）
  - `usage_count`: 使用次数（整数）

## 字段顺序规范

为了保持一致性，建议按以下顺序排列字段：

1. 基础信息（name, displayName, version, description, author）
2. 类型和入口（agentType, entryPoint）
3. 工厂配置（factory）
4. 通信配置（communication）
5. 能力描述（capabilities）
6. 输入模式（inputSchema）
7. 配置模式（configSchema）
8. 运行时信息（runtime）

## 验证规则

动态注册系统会验证以下内容：

1. **必需字段存在性**: 检查所有必需字段是否存在
2. **agentType有效性**: 验证agentType是否为有效值
3. **entryPoint结构**: 验证entryPoint对象结构
4. **对象类型验证**: 验证可选字段的对象类型
5. **字段完整性**: 检查entryPoint的必需子字段

## 示例

参考 `AGENT_MANIFEST_TEMPLATE.json` 文件获取完整的模板示例。

## 迁移指南

### 从旧版本迁移

1. **字段名修正**:
   - `agenttype` → `agentType`
   - 确保所有字段名使用驼峰命名法

2. **字段补充**:
   - 添加缺失的必需字段
   - 补充 `author` 字段
   - 确保 `entryPoint` 结构完整

3. **字段顺序调整**:
   - 按照标准顺序重新排列字段
   - 保持JSON格式的一致性

4. **验证测试**:
   - 使用动态注册系统验证manifest
   - 检查日志中的验证信息

## 最佳实践

1. **描述清晰**: 提供详细的功能描述和参数说明
2. **示例完整**: 为每个命令提供完整的调用示例
3. **类型准确**: 确保JSON Schema类型定义准确
4. **版本管理**: 遵循语义化版本控制
5. **文档同步**: 保持manifest与代码实现的一致性 