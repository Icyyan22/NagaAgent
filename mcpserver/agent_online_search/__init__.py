# __init__.py - 博查搜索Agent包初始化
"""
联网搜索Agent - 调用博查API进行网页搜索。

功能特性：
- 网页搜索功能
- 搜索结果格式化
- 支持AI参考使用

使用方法：
1. 通过MCP调用 search 工具执行搜索

Author: Icyyan22
Version: 1.0.0
"""

from .online_search_agent import OnlineSearchAgent, create_online_search_agent

__all__ = [
    'OnlineSearchAgent',
    'create_online_search_agent'
]

__version__ = '1.0.0'
__author__ = 'Naga搜索模块'
__description__ = '实时搜索MCP Agent'
