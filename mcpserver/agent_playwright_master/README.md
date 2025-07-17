# Playwright浏览器Agent

## 概述
这是一个基于Playwright的浏览器控制Agent，支持使用Edge浏览器打开网页和搜索功能。

## 功能特性
- 使用Edge浏览器打开网页
- 支持多种搜索引擎（Google、Bing、百度）
- 自动检测Edge浏览器路径
- 支持新建标签页

## 依赖问题解决

### Windows系统依赖
如果在Windows系统上遇到以下错误：
```
ImportError: No module named 'pythoncom'
ImportError: No module named 'win32com'
```

请安装以下依赖：
```bash
pip install pywin32
```

### 其他系统依赖
```bash
pip install playwright
playwright install chromium
```

## 配置说明

### Edge浏览器路径检测
Agent会自动检测Edge浏览器的安装路径：

1. **Windows系统**：
   - 优先解析快捷方式文件（.lnk）
   - 如果失败，尝试常见安装路径
   - 支持自动路径检测

2. **非Windows系统**：
   - 使用系统默认的Edge通道

### 配置文件
`config.py` 包含以下配置：
- `PLAYWRIGHT_HEADLESS`: 是否无头模式运行
- `EDGE_LNK_PATH`: Edge快捷方式路径
- `EDGE_COMMON_PATHS`: Edge常见安装路径列表

## 使用方法

### 基本调用
```python
# 打开网页
{
    "tool_name": "open",
    "url": "https://www.baidu.com"
}

# 搜索内容
{
    "tool_name": "search", 
    "query": "Python教程",
    "engine": "google"
}
```

### 支持的操作
- `open`: 打开指定URL
- `search`: 使用搜索引擎搜索内容

### 支持的搜索引擎
- `google`: Google搜索
- `bing`: Bing搜索  
- `baidu`: 百度搜索

## 故障排除

### 1. Edge浏览器未找到
- 确保已安装Microsoft Edge
- 检查配置文件中的路径是否正确
- 在非Windows系统上，确保Edge可用

### 2. 依赖库缺失
```bash
# 安装所有依赖
pip install pywin32 playwright
playwright install chromium
```

### 3. 权限问题
- 确保有足够的权限访问浏览器
- 检查防火墙设置

## 注意事项
- 仅在Windows系统上支持.lnk文件解析
- 需要安装Microsoft Edge浏览器
- 首次运行可能需要下载浏览器驱动 