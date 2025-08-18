
# bocha_search_agent.py - 博查搜索Agent
import json
import os
from pathlib import Path
import requests
from typing import Dict, Any
from config import config

class BochaSearchAgent:
    """博查搜索Agent - 调用博查API进行网页搜索"""
    
    name = "BochaSearchAgent"
    instructions = "调用博查API进行网页搜索，并将结果作为外部信息提供给AI参考"
    
    def __init__(self):
        # 从配置中获取API密钥和URL
        self.api_key = None
        self.api_url = "https://api.bochaai.com/v1/web-search"
        
        # 方法1: 从全局config对象读取（优先级最高）
        try:
            if hasattr(config, 'bocha_search'):
                bocha_config = config.bocha_search
                if hasattr(bocha_config, 'API_KEY') and bocha_config.API_KEY:
                    self.api_key = bocha_config.API_KEY
                if hasattr(bocha_config, 'Url') and bocha_config.Url:
                    self.api_url = bocha_config.Url
        except Exception as e:
            print(f"[WARN] 从全局配置读取博查API配置时出错: {e}")
            
        # 方法2: 直接从根目录config.json文件读取（备选方案）
        if not self.api_key:
            try:
                config_path = Path(__file__).parent.parent.parent / "config.json"
                if config_path.exists():
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                    if 'bocha_search' in config_data and 'API_KEY' in config_data['bocha_search']:
                        self.api_key = config_data['bocha_search']['API_KEY']
                    if 'bocha_search' in config_data and 'Url' in config_data['bocha_search']:
                        self.api_url = config_data['bocha_search']['Url']
            except Exception as e:
                print(f"[WARN] 从config.json文件读取博查API配置时出错: {e}")
        
        # 方法3: 从环境变量读取（最低优先级）
        if not self.api_key:
            env_api_key = os.getenv("BOCHA_API_KEY")
            if env_api_key:
                self.api_key = env_api_key
            
        # 如果仍然没有API密钥，使用默认值（用于测试）
        if not self.api_key:
            self.api_key = "your-bocha-api-key-here"

        # 从配置中获取count，如果未配置则默认为5
        self.count = 5
        try:
            if hasattr(config, 'bocha_search') and hasattr(config.bocha_search, 'count'):
                self.count = int(config.bocha_search.count)
        except (ValueError, TypeError) as e:
            print(f"[WARN] 从全局配置读取博查count配置时出错，将使用默认值5: {e}")
        except Exception as e:
            print(f"[WARN] 从全局配置读取博cha count配置时出现未知错误: {e}")
            
        print(f"[OK] BochaSearchAgent初始化完成，API URL: {self.api_url}, Count: {self.count}")
    
    async def search(self, query: str) -> Dict[str, Any]:
        """执行博查搜索"""
        try:
            payload = json.dumps({
                "query": query,
                "summary": True,
                "count": self.count
            })
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(self.api_url, headers=headers, data=payload, timeout=15)
            response.raise_for_status()  # 对于错误状态码抛出异常
            search_data = response.json()

            if search_data.get("code") == 200 and search_data.get("data"):
                # 提取相关信息
                web_pages = search_data["data"].get("webPages", {}).get("value", [])
                results = []
                for page in web_pages:
                    results.append({
                        "title": page.get("name"),
                        "url": page.get("url"),
                        "snippet": page.get("snippet"),
                        "summary": page.get("summary")
                    })
                
                # 格式化为AI可用的格式
                formatted_results = "外部搜索信息:\n"
                for i, result in enumerate(results, 1):
                    formatted_results += f"  - 结果 {i}:\n"
                    formatted_results += f"    - 标题: {result['title']}\n"
                    formatted_results += f"    - 链接: {result['url']}\n"
                    formatted_results += f"    - 摘要: {result['snippet']}\n"
                    if result['summary']:
                        formatted_results += f"    - 总结: {result['summary']}\n"

                return {
                    "success": True, 
                    "data": formatted_results,
                    "raw_data": results  # 保留原始数据供进一步处理
                }
            else:
                return {
                    "success": False, 
                    "error": f"API error: {search_data.get('msg', 'Unknown error')}"
                }

        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}"}

    async def handle_handoff(self, data: dict) -> str:
        """处理搜索请求"""
        try:
            tool_name = data.get("tool_name", "").lower()
            
            if tool_name == "search":
                query = data.get("query")
                if not query:
                    return json.dumps({
                        "status": "error",
                        "message": "搜索需要指定查询内容（query参数）",
                        "data": {}
                    }, ensure_ascii=False)
                
                # 执行搜索
                search_result = await self.search(query)
                
                if search_result["success"]:
                    return json.dumps({
                        "status": "ok",
                        "message": "搜索完成",
                        "data": search_result["data"],
                        "raw_data": search_result.get("raw_data", [])
                    }, ensure_ascii=False)
                else:
                    return json.dumps({
                        "status": "error",
                        "message": f"搜索失败: {search_result['error']}",
                        "data": {}
                    }, ensure_ascii=False)
            else:
                return json.dumps({
                    "status": "error",
                    "message": f"不支持的操作: {tool_name}，支持的操作：search",
                    "data": {}
                }, ensure_ascii=False)
                
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"搜索Agent处理异常: {str(e)}",
                "data": {}
            }, ensure_ascii=False)


def create_bocha_search_agent():
    """创建BochaSearchAgent实例"""
    return BochaSearchAgent()


def validate_agent_config():
    """验证Agent配置"""
    try:
        # 检查API密钥
        api_key = None
        
        # 方法1: 从全局配置读取
        try:
            if hasattr(config, 'bocha_search') and hasattr(config.bocha_search, 'API_KEY'):
                api_key = config.bocha_search.API_KEY
        except Exception:
            pass
            
        # 方法2: 从config.json文件读取
        if not api_key:
            try:
                config_path = Path(__file__).parent.parent.parent / "config.json"
                if config_path.exists():
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                    if 'bocha_search' in config_data and 'API_KEY' in config_data['bocha_search']:
                        api_key = config_data['bocha_search']['API_KEY']
            except Exception:
                pass
        
        # 方法3: 从环境变量读取
        if not api_key:
            api_key = os.getenv("BOCHA_API_KEY")
        
        if not api_key or api_key == "your-bocha-api-key-here":
            return False, "API密钥未配置"
        
        return True, "配置验证通过"
    except Exception as e:
        return False, f"配置验证失败: {str(e)}"


def get_agent_dependencies():
    """获取Agent依赖"""
    return [
        "requests",
        "json",
        "os"
    ]

