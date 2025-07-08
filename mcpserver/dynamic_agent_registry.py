#!/usr/bin/env python3
# dynamic_agent_registry.py - 基于Plugin.js机制的动态Agent注册系统
import os
import json
import importlib
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class DynamicAgentRegistry:
    """动态Agent注册系统，参考Plugin.js的机制"""
    
    def __init__(self, agent_dir: str = 'mcpserver'):
        self.agent_dir = Path(agent_dir)
        self.agents = {}  # 存储所有Agent
        self.agent_instances = {}  # 存储Agent实例
        self.agent_configs = {}  # 存储Agent配置
        self.distributed_agents = {}  # 存储分布式Agent
        self.debug_mode = os.getenv('DebugMode', 'False').lower() == 'true'
        
    async def discover_agents(self):
        """动态发现所有Agent"""
        logger.debug(f"[DynamicAgentRegistry] 开始Agent发现...")
        
        # 清除本地Agent，保留分布式Agent
        local_agents = {k: v for k, v in self.agents.items() 
                       if not v.get('is_distributed', False)}
        self.agents = local_agents
        
        try:
            # 扫描Agent目录
            for agent_folder in self.agent_dir.iterdir():
                if agent_folder.is_dir() and not agent_folder.name.startswith('__'):
                    await self._load_agent_from_folder(agent_folder)
                    
            logger.debug(f"[DynamicAgentRegistry] Agent发现完成，共加载 {len(self.agents)} 个Agent")
            
        except Exception as e:
            logger.error(f"[DynamicAgentRegistry] Agent发现失败: {e}")
    
    async def _load_agent_from_folder(self, agent_folder: Path):
        """从文件夹加载Agent"""
        manifest_path = agent_folder / 'agent-manifest.json'
        
        if not manifest_path.exists():
            if self.debug_mode:
                logger.debug(f"[DynamicAgentRegistry] {agent_folder.name} 没有agent-manifest.json，跳过")
            return
            
        try:
            # 读取manifest文件
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            if not self._validate_manifest(manifest):
                logger.warn(f"[DynamicAgentRegistry] {agent_folder.name} 的manifest无效，跳过")
                return
                
            # 加载Agent特定的配置文件
            config = await self._load_agent_config(agent_folder)
            manifest['config'] = config
            manifest['base_path'] = str(agent_folder)
            
            # 注册Agent
            agent_name = manifest['name']
            if agent_name in self.agents:
                logger.warn(f"[DynamicAgentRegistry] Agent名称 {agent_name} 重复，跳过")
                return
                
            self.agents[agent_name] = manifest
            logger.debug(f"[DynamicAgentRegistry] 加载Agent: {manifest.get('displayName', agent_name)} ({agent_name})")
            
        except Exception as e:
            logger.error(f"[DynamicAgentRegistry] 加载Agent {agent_folder.name} 失败: {e}")
    
    def _validate_manifest(self, manifest: Dict) -> bool:
        """验证manifest文件"""
        # 必需字段
        required_fields = ['name', 'displayName', 'version', 'description', 'author', 'agentType', 'entryPoint']
        if not all(field in manifest for field in required_fields):
            missing_fields = [field for field in required_fields if field not in manifest]
            logger.warn(f"[DynamicAgentRegistry] manifest缺少必需字段: {missing_fields}")
            return False
        
        # 验证agentType字段
        valid_agent_types = ['mcp', 'synchronous', 'asynchronous']
        if manifest.get('agentType') not in valid_agent_types:
            logger.warn(f"[DynamicAgentRegistry] agentType必须是以下之一: {valid_agent_types}")
            return False
        
        # 验证entryPoint结构
        entry_point = manifest.get('entryPoint', {})
        if not isinstance(entry_point, dict):
            logger.warn(f"[DynamicAgentRegistry] entryPoint必须是对象")
            return False
        
        required_entry_fields = ['module', 'class']
        if not all(field in entry_point for field in required_entry_fields):
            missing_entry_fields = [field for field in required_entry_fields if field not in entry_point]
            logger.warn(f"[DynamicAgentRegistry] entryPoint缺少必需字段: {missing_entry_fields}")
            return False
        
        # 验证factory结构（如果存在）
        factory = manifest.get('factory')
        if factory and not isinstance(factory, dict):
            logger.warn(f"[DynamicAgentRegistry] factory必须是对象")
            return False
        
        # 验证communication结构（如果存在）
        communication = manifest.get('communication')
        if communication and not isinstance(communication, dict):
            logger.warn(f"[DynamicAgentRegistry] communication必须是对象")
            return False
        
        # 验证capabilities结构（如果存在）
        capabilities = manifest.get('capabilities')
        if capabilities and not isinstance(capabilities, dict):
            logger.warn(f"[DynamicAgentRegistry] capabilities必须是对象")
            return False
        
        # 验证inputSchema结构（如果存在）
        input_schema = manifest.get('inputSchema')
        if input_schema and not isinstance(input_schema, dict):
            logger.warn(f"[DynamicAgentRegistry] inputSchema必须是对象")
            return False
        
        # 验证configSchema结构（如果存在）
        config_schema = manifest.get('configSchema')
        if config_schema and not isinstance(config_schema, dict):
            logger.warn(f"[DynamicAgentRegistry] configSchema必须是对象")
            return False
        
        return True
    
    async def _load_agent_config(self, agent_folder: Path) -> Dict:
        """加载Agent特定的配置文件"""
        config = {}
        
        # 尝试加载config.env文件
        config_env_path = agent_folder / 'config.env'
        if config_env_path.exists():
            try:
                with open(config_env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            config[key.strip()] = value.strip()
                if self.debug_mode:
                    pass  # 调试模式下可以添加日志
            except Exception as e:
                logger.warn(f"[DynamicAgentRegistry] 读取 {agent_folder.name} 的config.env失败: {e}")
        
        return config
    
    def get_agent_instance(self, agent_name: str):
        """获取Agent实例（延迟初始化）"""
        if agent_name not in self.agents:
            return None
            
        # 如果实例已存在，直接返回
        if agent_name in self.agent_instances:
            return self.agent_instances[agent_name]
            
        # 创建新实例
        try:
            manifest = self.agents[agent_name]
            instance = self._create_agent_instance(manifest)
            if instance:
                self.agent_instances[agent_name] = instance
                pass
            return instance
        except Exception as e:
            logger.error(f"[DynamicAgentRegistry] 创建Agent实例 {agent_name} 失败: {e}")
            return None
    
    def _create_agent_instance(self, manifest: Dict):
        """创建Agent实例"""
        try:
            # 从manifest中获取模块信息
            entry_point = manifest.get('entryPoint', {})
            module_name = entry_point.get('module')
            class_name = entry_point.get('class')
            
            if not module_name or not class_name:
                logger.error(f"[DynamicAgentRegistry] Agent {manifest['name']} 缺少entryPoint信息")
                return None
                
            # 动态导入模块
            module = importlib.import_module(module_name)
            
            # 优先使用工厂函数
            factory = manifest.get('factory', {})
            create_func_name = factory.get('create_instance')
            
            if create_func_name:
                # 使用工厂函数创建实例
                create_func = getattr(module, create_func_name, None)
                if create_func:
                    instance = create_func()
                    return instance
                else:
                    logger.error(f"[DynamicAgentRegistry] 工厂函数 {create_func_name} 不存在")
            
            # 回退到直接实例化类
            agent_class = getattr(module, class_name)
            
            # 检查是否是类还是实例
            if hasattr(agent_class, '__call__') and not isinstance(agent_class, type):
                # 如果agent_class是可调用的但不是类，说明它已经是实例
                return agent_class
            else:
                # 创建新实例
                instance = agent_class()
                return instance
            
        except Exception as e:
            logger.error(f"[DynamicAgentRegistry] 创建Agent实例失败: {e}")
            return None
    
    def register_distributed_agent(self, server_id: str, agent_manifests: List[Dict]):
        """注册分布式Agent"""
        logger.info(f"[DynamicAgentRegistry] 注册来自 {server_id} 的 {len(agent_manifests)} 个分布式Agent")
        
        for manifest in agent_manifests:
            if not self._validate_manifest(manifest):
                logger.warn(f"[DynamicAgentRegistry] 分布式Agent manifest无效，跳过")
                continue
                
            agent_name = manifest['name']
            if agent_name in self.agents:
                logger.warn(f"[DynamicAgentRegistry] 分布式Agent {agent_name} 与本地Agent冲突，跳过")
                continue
                
            # 标记为分布式Agent
            manifest['is_distributed'] = True
            manifest['server_id'] = server_id
            manifest['displayName'] = f"[云端] {manifest.get('displayName', agent_name)}"
            
            self.agents[agent_name] = manifest
            logger.info(f"[DynamicAgentRegistry] 注册分布式Agent: {manifest['displayName']} ({agent_name})")
    
    def unregister_distributed_agents(self, server_id: str):
        """注销指定服务器的所有分布式Agent"""
        logger.info(f"[DynamicAgentRegistry] 注销来自 {server_id} 的所有分布式Agent")
        
        agents_to_remove = []
        for agent_name, manifest in self.agents.items():
            if manifest.get('is_distributed', False) and manifest.get('server_id') == server_id:
                agents_to_remove.append(agent_name)
                # 同时移除实例
                if agent_name in self.agent_instances:
                    del self.agent_instances[agent_name]
        
        for agent_name in agents_to_remove:
            del self.agents[agent_name]
            logger.info(f"[DynamicAgentRegistry] 注销分布式Agent: {agent_name}")
    
    def get_available_agents(self) -> List[Dict]:
        """获取所有可用的Agent信息"""
        return [
            {
                'name': name,
                'displayName': manifest.get('displayName', name),
                'description': manifest.get('description', ''),
                'is_distributed': manifest.get('is_distributed', False),
                'server_id': manifest.get('server_id', None)
            }
            for name, manifest in self.agents.items()
        ]
    
    def get_agent_manifest(self, agent_name: str) -> Optional[Dict]:
        """获取Agent的manifest信息"""
        return self.agents.get(agent_name)
    
    async def reload_agents(self):
        """重新加载所有Agent（热重载）"""
        logger.info(f"[DynamicAgentRegistry] 重新加载所有Agent...")
        
        # 清除所有本地Agent实例
        local_agent_names = [name for name, manifest in self.agents.items() 
                           if not manifest.get('is_distributed', False)]
        for name in local_agent_names:
            if name in self.agent_instances:
                del self.agent_instances[name]
        
        # 重新发现Agent
        await self.discover_agents()
        
        logger.info(f"[DynamicAgentRegistry] Agent重新加载完成")

# 全局实例
dynamic_registry = DynamicAgentRegistry()

# 便捷函数
async def discover_agents():
    """发现所有Agent"""
    await dynamic_registry.discover_agents()

def get_agent_instance(agent_name: str):
    """获取Agent实例"""
    return dynamic_registry.get_agent_instance(agent_name)

def register_distributed_agent(server_id: str, agent_manifests: List[Dict]):
    """注册分布式Agent"""
    dynamic_registry.register_distributed_agent(server_id, agent_manifests)

def unregister_distributed_agents(server_id: str):
    """注销分布式Agent"""
    dynamic_registry.unregister_distributed_agents(server_id)

def get_available_agents() -> List[Dict]:
    """获取所有可用Agent"""
    return dynamic_registry.get_available_agents()

async def reload_agents():
    """重新加载Agent"""
    await dynamic_registry.reload_agents() 