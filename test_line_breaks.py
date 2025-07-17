#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
换行符处理测试脚本
测试前端换行符显示功能是否正常工作
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from ui.response_utils import extract_message

def test_line_break_processing():
    """测试换行符处理功能"""
    print("=== 换行符处理测试 ===")
    
    # 测试用例1：普通换行符
    test1 = "第一行\n第二行\n第三行"
    print(f"测试1 - 普通换行符:")
    print(f"输入: {repr(test1)}")
    result1 = extract_message(test1)
    print(f"输出: {repr(result1)}")
    print(f"显示效果:\n{result1}")
    print("-" * 50)
    
    # 测试用例2：JSON转义的换行符
    test2 = '{"content": "第一行\\n第二行\\n第三行"}'
    print(f"测试2 - JSON转义换行符:")
    print(f"输入: {repr(test2)}")
    result2 = extract_message(test2)
    print(f"输出: {repr(result2)}")
    print(f"显示效果:\n{result2}")
    print("-" * 50)
    
    # 测试用例3：Windows换行符
    test3 = "第一行\r\n第二行\r\n第三行"
    print(f"测试3 - Windows换行符:")
    print(f"输入: {repr(test3)}")
    result3 = extract_message(test3)
    print(f"输出: {repr(result3)}")
    print(f"显示效果:\n{result3}")
    print("-" * 50)
    
    # 测试用例4：复杂JSON响应
    test4 = '''{
        "choices": [{
            "message": {
                "content": "设备控制类\\n1. 智能家居控制：通过MQTT协议同时操控两个设备的开关状态\\n\\n知识管理类\\n2. 记忆检索：基于三元组知识图谱进行语义查询"
            }
        }]
    }'''
    print(f"测试4 - 复杂JSON响应:")
    print(f"输入: {repr(test4)}")
    result4 = extract_message(test4)
    print(f"输出: {repr(result4)}")
    print(f"显示效果:\n{result4}")
    print("-" * 50)
    
    # 测试用例5：数组格式响应
    test5 = '''[
        {"content": "第一段内容\\n包含换行符"},
        {"content": "第二段内容\\n也包含换行符"}
    ]'''
    print(f"测试5 - 数组格式响应:")
    print(f"输入: {repr(test5)}")
    result5 = extract_message(test5)
    print(f"输出: {repr(result5)}")
    print(f"显示效果:\n{result5}")
    print("-" * 50)

def test_html_conversion():
    """测试HTML转换功能"""
    print("\n=== HTML转换测试 ===")
    
    # 模拟前端HTML转换逻辑
    def convert_to_html(text):
        """模拟前端的HTML转换逻辑"""
        content_text = str(text)
        # 处理各种可能的换行符格式
        content_text = content_text.replace('\\n', '\n')  # JSON转义的换行符
        content_text = content_text.replace('\\r\\n', '\n')  # Windows换行符
        content_text = content_text.replace('\\r', '\n')  # 旧版Mac换行符
        content_text = content_text.replace('\r\n', '\n')  # 实际Windows换行符
        content_text = content_text.replace('\r', '\n')  # 实际旧版Mac换行符
        
        # 转换为HTML，保持段落结构
        content_html = content_text.replace('\n', '<br>')
        return content_html
    
    # 测试用例
    test_cases = [
        "第一行\n第二行\n第三行",
        "第一行\\n第二行\\n第三行",
        "第一行\r\n第二行\r\n第三行",
        "设备控制类\\n1. 智能家居控制\\n\\n知识管理类\\n2. 记忆检索"
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"测试{i}:")
        print(f"原始文本: {repr(test_case)}")
        html_result = convert_to_html(test_case)
        print(f"HTML结果: {html_result}")
        print(f"预期显示效果:")
        # 模拟HTML显示效果
        display_text = html_result.replace('<br>', '\n')
        print(display_text)
        print("-" * 30)

if __name__ == "__main__":
    test_line_break_processing()
    test_html_conversion()
    print("\n✅ 换行符处理测试完成！") 