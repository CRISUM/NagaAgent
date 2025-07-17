# config.py # Playwright Agent配置文件
import os
import platform

# Playwright配置
PLAYWRIGHT_HEADLESS = False  # 是否无头模式

# Edge浏览器路径配置
if platform.system() == "Windows":
    # Edge快捷方式路径
    EDGE_LNK_PATH = os.path.expandvars(r'%APPDATA%\Microsoft\Windows\Start Menu\Programs\Microsoft Edge.lnk')
    
    # Edge常见安装路径
    EDGE_COMMON_PATHS = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%PROGRAMFILES%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%PROGRAMFILES(X86)%\Microsoft\Edge\Application\msedge.exe")
    ]
else:
    # 非Windows系统
    EDGE_LNK_PATH = ""
    EDGE_COMMON_PATHS = [] 