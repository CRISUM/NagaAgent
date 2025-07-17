#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Word文档处理子Agent
专门负责处理Word文档相关任务，通过调用Word MCP服务来执行具体操作
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from openai import AsyncOpenAI

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WordAgent")

class WordAgent:
    """Word文档处理子Agent"""
    
    def __init__(self):
        """初始化Word Agent"""
        self.mcp_service = None
        self.client = None
        self.model_id = "deepseek-chat"
        self.api_base_url = "https://api.deepseek.com/v1"
        self.api_key = ""
        self.temperature = 0.7
        self.max_tokens = 8192
        
        # 初始化MCP服务连接
        self._init_mcp_service()
        
        # 初始化LLM客户端
        self._init_llm_client()
        
        logger.info("Word Agent初始化完成")
    
    def _init_mcp_service(self):
        """初始化MCP服务连接"""
        try:
            from mcpserver.mcp_manager import get_mcp_manager
            mcp_manager = get_mcp_manager()
            self.mcp_service = mcp_manager.get_mcp("word-document-server")
            
            if not self.mcp_service:
                logger.warning("Word MCP服务未找到，将尝试动态启动")
                # 这里可以添加动态启动MCP服务的逻辑
                
        except Exception as e:
            logger.error(f"初始化MCP服务失败: {e}")
    
    def _init_llm_client(self):
        """初始化LLM客户端"""
        try:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.api_base_url
            )
        except Exception as e:
            logger.error(f"初始化LLM客户端失败: {e}")
    
    async def handle_handoff(self, task: Dict[str, Any]) -> str:
        """处理任务转接
        
        Args:
            task: 任务参数，包含action和具体参数
            
        Returns:
            str: 执行结果
        """
        try:
            action = task.get('action', '')
            
            # 如果是直接调用MCP工具，直接执行
            if self._is_direct_mcp_call(action):
                return await self._call_mcp_tool(task)
            
            # 否则，使用LLM分析任务并调用相应工具
            return await self._process_with_llm(task)
            
        except Exception as e:
            logger.error(f"处理任务失败: {e}")
            return f"任务处理失败: {str(e)}"
    
    def _is_direct_mcp_call(self, action: str) -> bool:
        """检查是否是直接调用MCP工具"""
        mcp_tools = [
            'create_document', 'add_heading', 'add_paragraph', 'add_table', 'add_picture',
            'format_text', 'search_and_replace', 'get_document_info', 'get_document_text',
            'get_document_outline', 'list_available_documents', 'copy_document',
            'convert_to_pdf', 'add_footnote_to_document', 'add_endnote_to_document',
            'protect_document', 'unprotect_document', 'create_custom_style',
            'format_table', 'add_page_break', 'delete_paragraph',
            'get_paragraph_text_from_document', 'find_text_in_document',
            'customize_footnote_style'
        ]
        return action in mcp_tools
    
    async def _call_mcp_tool(self, task: Dict[str, Any]) -> str:
        """直接调用MCP工具
        
        Args:
            task: 任务参数
            
        Returns:
            str: 执行结果
        """
        if not self.mcp_service:
            return "Word MCP服务未可用"
        
        action = task.get('action', '')
        
        try:
            # 检查MCP服务是否有对应的方法
            if hasattr(self.mcp_service, action):
                method = getattr(self.mcp_service, action)
                if callable(method):
                    # 移除action参数，保留其他参数
                    params = {k: v for k, v in task.items() if k != 'action'}
                    
                    # 调用方法
                    if asyncio.iscoroutinefunction(method):
                        result = await method(**params)
                    else:
                        result = method(**params)
                    
                    return str(result)
                else:
                    return f"Word MCP服务中的 {action} 不是一个可调用的方法"
            else:
                return f"Word MCP服务不支持动作: {action}"
                
        except Exception as e:
            logger.error(f"调用MCP工具失败: {e}")
            return f"MCP工具调用失败: {str(e)}"
    
    async def _process_with_llm(self, task: Dict[str, Any]) -> str:
        """使用LLM处理任务
        
        Args:
            task: 任务参数
            
        Returns:
            str: 执行结果
        """
        if not self.client:
            return "LLM客户端未初始化"
        
        try:
            # 构建系统提示词
            system_prompt = """你是一个专业的Microsoft Word文档处理助手。你的任务是分析用户需求，并调用相应的Word MCP工具来完成任务。

可用的工具包括：
1. create_document - 创建新文档
2. add_heading - 添加标题
3. add_paragraph - 添加段落
4. add_table - 添加表格
5. add_picture - 添加图片
6. format_text - 格式化文本
7. search_and_replace - 搜索替换
8. get_document_info - 获取文档信息
9. get_document_text - 获取文档文本
10. convert_to_pdf - 转换为PDF
11. protect_document - 保护文档
12. 等等...

请分析用户需求，确定需要调用的工具，并以JSON格式返回：
{
    "action": "工具名称",
    "参数1": "值1",
    "参数2": "值2"
}

如果任务需要多个步骤，请按顺序列出每个步骤的JSON。"""

            # 构建用户消息
            user_message = f"用户需求: {json.dumps(task, ensure_ascii=False)}"
            
            # 调用LLM
            response = await self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # 解析LLM响应
            llm_response = response.choices[0].message.content
            
            # 尝试解析JSON响应
            try:
                # 提取JSON部分
                import re
                json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
                if json_match:
                    action_plan = json.loads(json_match.group())
                    
                    # 执行动作计划
                    if isinstance(action_plan, list):
                        # 多个步骤
                        results = []
                        for step in action_plan:
                            result = await self._call_mcp_tool(step)
                            results.append(f"步骤 {step.get('action', 'unknown')}: {result}")
                        return "\n".join(results)
                    else:
                        # 单个步骤
                        return await self._call_mcp_tool(action_plan)
                else:
                    return f"LLM响应格式错误，无法解析JSON: {llm_response}"
                    
            except json.JSONDecodeError as e:
                return f"LLM响应JSON解析失败: {e}\n响应内容: {llm_response}"
                
        except Exception as e:
            logger.error(f"LLM处理失败: {e}")
            return f"LLM处理失败: {str(e)}"
    
    async def call_tool(self, tool_name: str, **kwargs) -> str:
        """调用指定工具
        
        Args:
            tool_name: 工具名称
            **kwargs: 工具参数
            
        Returns:
            str: 执行结果
        """
        task = {"action": tool_name, **kwargs}
        return await self._call_mcp_tool(task)
    
    def get_available_tools(self) -> list:
        """获取可用工具列表"""
        if not self.mcp_service:
            return []
        
        # 获取MCP服务的所有方法
        tools = []
        for attr_name in dir(self.mcp_service):
            if not attr_name.startswith('_') and callable(getattr(self.mcp_service, attr_name)):
                tools.append(attr_name)
        
        return tools
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """获取工具信息
        
        Args:
            tool_name: 工具名称
            
        Returns:
            Optional[Dict[str, Any]]: 工具信息
        """
        if not self.mcp_service or not hasattr(self.mcp_service, tool_name):
            return None
        
        method = getattr(self.mcp_service, tool_name)
        if not callable(method):
            return None
        
        import inspect
        sig = inspect.signature(method)
        
        return {
            "name": tool_name,
            "parameters": str(sig),
            "doc": method.__doc__ or "无文档说明"
        } 