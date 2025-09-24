# -*- coding: utf-8 -*-
"""
Enhanced Data Fetcher - 增强版数据获取器
支持多种数据源：newsnow API + 直接爬取 + RSS订阅
"""

import asyncio
import aiohttp
import feedparser
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, UTC
from dataclasses import dataclass, field
from urllib.parse import urljoin
import json
import os
from pydantic import BaseModel, HttpUrl, Field
from enum import StrEnum, auto

# 配置日志 - 只获取logger，不重新配置basicConfig
import logging
logger = logging.getLogger(__name__)  # 只获取logger，不配置basicConfig

@dataclass(frozen=True, slots=True)
class NewsItem:
    """不可变新闻项数据结构"""
    title: str
    source: str
    rank: int
    url: str
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    description: str = ""

class SourceType(StrEnum):
    """新闻源类型枚举"""
    NEWSNOW_API = "newsnow_api"
    RSS = "rss"
    WEB_SCRAPER = "web_scraper"

class SourceConfig(BaseModel):
    """新闻源配置模型"""
    id: str
    name: str
    type: SourceType
    url: HttpUrl
    selector: Optional[str] = None
    enabled: bool = True
    timeout: Optional[int] = None  # 可选，由代码统一管理默认值

class NewsFetcher:
    """简洁优雅的新闻获取器"""
    # 统一管理的超时默认值
    DEFAULT_TIMEOUTS = {
        SourceType.NEWSNOW_API: 5,   # API通常响应较快
        SourceType.RSS: 8,           # RSS稍慢
        SourceType.WEB_SCRAPER: 15   # 网页抓取最慢
    }
    
    def __init__(self, config_path: str = "news_sources.json", max_concurrent: int = None):
        # 只保留核心配置项
        self.config_path = config_path
        # 允许从外部传入并发限制，若未提供则根据配置文件或自动调整
        self._explicit_concurrent = max_concurrent
        self.sources = self._load_sources()
        self.max_concurrent = self._adjust_concurrency()

    def _load_sources(self) -> List[SourceConfig]:
        """加载并验证新闻源配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 获取类型默认设置
            type_defaults = data.get('type_defaults', {})
            
            # 扁平化配置结构
            all_sources = []
            for source_type, sources in data.get('news_sources', {}).items():
                if isinstance(sources, list):
                    # 检查此类型是否被默认禁用
                    type_enabled = type_defaults.get(source_type, True)
                    
                    for source in sources:
                        try:
                            # 确保类型正确映射
                            source['type'] = source_type
                            # 应用类型默认设置，但保留源自己的enabled设置优先级
                            if 'enabled' not in source and not type_enabled:
                                source['enabled'] = False
                            
                            all_sources.append(SourceConfig(**source))
                        except Exception as e:
                            logger.warning(f"无效的源配置: {source.get('name', '未知')}")
            
            logger.info(f"加载了 {len(all_sources)} 个新闻源")
            return all_sources
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"配置文件错误: {str(e).split(':')[0]}")  # 简化错误信息
            return []

    def _adjust_concurrency(self) -> int:
        """根据源数量动态调整并发度"""
        # 如果明确指定了并发限制，则使用该值
        if self._explicit_concurrent is not None:
            logger.info(f"使用显式并发限制: {self._explicit_concurrent}")
            return self._explicit_concurrent
        
        # 否则根据启用的源数量自动调整
        enabled_count = sum(1 for source in self.sources if source.enabled)
        concurrent = min(20, max(3, enabled_count // 2))
        logger.info(f"自动调整并发度为: {concurrent}")
        return concurrent

    def _get_optimized_timeout(self, source: SourceConfig) -> int:
        """获取优化的超时值，优先使用源自定义值"""
        if source.timeout is not None:
            return source.timeout
        return self.DEFAULT_TIMEOUTS.get(source.type, 10)

    async def _fetch_newsnow(self, session: aiohttp.ClientSession, source: SourceConfig) -> List[NewsItem]:
        """获取NewsNow API数据"""
        try:
            async with session.get(str(source.url), timeout=self._get_optimized_timeout(source)) as response:
                response.raise_for_status()
                data = await response.json()
                items = data.get('items', [])[:50]  # 限制最多50条
                
                return [NewsItem(
                    title=item.get('title', '无标题'),
                    source=source.name,
                    rank=idx + 1,
                    url=item.get('url', ''),
                    description=""
                ) for idx, item in enumerate(items)]
        except Exception as e:
            status_info = f"状态码: {e.status}" if hasattr(e, 'status') else "连接超时"
            logger.error(f"{source.name} 新闻获取失败: {status_info}")  # 简化错误信息
            return []

    async def _fetch_rss(self, session: aiohttp.ClientSession, source: SourceConfig) -> List[NewsItem]:
        """获取RSS订阅数据"""
        try:
            async with session.get(str(source.url), timeout=self._get_optimized_timeout(source)) as response:
                response.raise_for_status()
                content = await response.text()
                feed = feedparser.parse(content)
                
                return [NewsItem(
                    title=entry.get('title', '').strip(),
                    source=source.name,
                    rank=idx + 1,
                    url=entry.get('link', ''),
                    description=entry.get('summary', '')[:100]  # 摘要前100字符
                ) for idx, entry in enumerate(feed.entries[:30])]  # 限制30条
        except Exception as e:
            status_info = f"状态码: {e.status}" if hasattr(e, 'status') else "连接超时"
            logger.error(f"{source.name} RSS订阅失败: {status_info}")  # 简化错误信息
            return []

    async def _fetch_web(self, session: aiohttp.ClientSession, source: SourceConfig) -> List[NewsItem]:
        """抓取网页内容"""
        try:
            async with session.get(str(source.url), timeout=self._get_optimized_timeout(source)) as response:
                response.raise_for_status()
                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')
                
                items = []
                if source.selector:
                    elements = soup.select(source.selector)[:20]  # 限制20条
                    
                    for idx, element in enumerate(elements):
                        title = element.get_text().strip()
                        url = element.get('href', '')
                        
                        # 处理相对URL
                        if url and not url.startswith(('http://', 'https://')):
                            url = urljoin(str(source.url), url)
                        
                        if title and len(title) > 5:  # 过滤太短的标题
                            items.append(NewsItem(
                                title=title,
                                source=source.name,
                                rank=idx + 1,
                                url=url
                            ))
                
                return items
        except Exception as e:
            status_info = f"状态码: {e.status}" if hasattr(e, 'status') else "连接超时"
            logger.error(f"{source.name} 网页抓取失败: {status_info}")  # 简化错误信息
            return []

    async def _fetch_source(self, session: aiohttp.ClientSession, source: SourceConfig) -> List[NewsItem]:
        """获取单个新闻源数据并应用重试逻辑"""
        # 根据源类型选择获取器
        fetcher_map = {
            SourceType.NEWSNOW_API: self._fetch_newsnow,
            SourceType.RSS: self._fetch_rss,
            SourceType.WEB_SCRAPER: self._fetch_web
        }
        
        fetcher = fetcher_map.get(source.type)
        if not fetcher:
            logger.warning(f"未知的源类型: {source.type}")
            return []
            
        # 应用重试逻辑
        for attempt in range(3):
            try:
                result = await fetcher(session, source)
                if result:
                    logger.info(f"{source.name}: 成功获取 {len(result)} 条新闻")
                return result
            except (aiohttp.ClientResponseError, asyncio.TimeoutError) as e:
                if attempt == 2:
                    break
                # 指数退避
                backoff_time = 0.1 * (2 ** attempt)
                logger.warning(f"{source.name} 重试中 ({attempt+1}/3)，{backoff_time:.2f}s后重试...")
                await asyncio.sleep(backoff_time)
            except Exception as e:
                error_type = type(e).__name__
                logger.error(f"{source.name} 发生未预期错误({error_type}): {str(e)[:50]}...")  # 限制错误长度
                break
        
        return []

    async def _fetch_all(self) -> List[NewsItem]:
        """异步获取所有启用的新闻源数据"""
        all_news: List[NewsItem] = []
        
        # 创建优化的客户端会话
        timeout = aiohttp.ClientTimeout(total=60, connect=10, sock_connect=10, sock_read=30)
        
        # 增强的请求头，模拟现代浏览器
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://newsnow.busiyi.world/',
            'Origin': 'https://newsnow.busiyi.world',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache'
        }
        
        async with aiohttp.ClientSession(
            timeout=timeout,
            headers=headers,
            connector=aiohttp.TCPConnector(limit=self.max_concurrent, ttl_dns_cache=300)
        ) as session:
            # 使用现代TaskGroup管理并发任务
            enabled_sources = [source for source in self.sources if source.enabled]
            
            if not enabled_sources:
                logger.warning("没有启用的新闻源")
                return []
            
            async with asyncio.TaskGroup() as tg:
                tasks = [tg.create_task(self._fetch_source(session, source)) 
                         for source in enabled_sources]
            
            # 收集结果
            success_count = 0
            for task in tasks:
                if task.done() and not task.cancelled():
                    result = task.result()
                    if result:
                        all_news.extend(result)
                        success_count += 1
        
        logger.info(f"总共获取到 {len(all_news)} 条新闻，来自 {success_count} 个源")
        return all_news

    def fetch(self) -> List[NewsItem]:
        """主接口：获取所有新闻（简化版，隐藏事件循环复杂性）"""
        try:
            # 尝试使用当前事件循环
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果事件循环正在运行，则创建一个新的
                    return asyncio.run_coroutine_threadsafe(self._fetch_all(), loop).result()
                else:
                    return loop.run_until_complete(self._fetch_all())
            except RuntimeError:
                # 没有运行中的事件循环，创建新的
                return asyncio.run(self._fetch_all())
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"获取新闻失败({error_type}): {str(e).split(':')[0]}")  # 简化错误信息
            return []

    def get_available_sources(self) -> List[Dict[str, Any]]:
        """获取所有可用新闻源列表"""
        return [{
            'id': source.id,
            'name': source.name,
            'type': source.type,
            'enabled': source.enabled
        } for source in self.sources]

    def reload_config(self) -> None:
        """重新加载新闻源配置"""
        logger.info("重新加载新闻源配置...")
        # 保存当前启用状态
        enabled_status = {source.id: source.enabled for source in self.sources}
        # 重新加载配置
        self.sources = self._load_sources()
        # 恢复启用状态
        for source in self.sources:
            if source.id in enabled_status:
                source.enabled = enabled_status[source.id]
        # 重新调整并发度
        self.max_concurrent = self._adjust_concurrency()

# 使用示例
if __name__ == "__main__":
    # 简单测试
    fetcher = NewsFetcher()
    
    # 获取所有可用源
    sources = fetcher.get_available_sources()
    print("可用新闻源:")
    for source in sources[:5]:  # 只显示前5个源
        print(f"  - {source['name']} ({source['type']})" + (" [已禁用]" if not source['enabled'] else ""))
    print(f"  ... 等共{len(sources)}个源")
    
    # 测试获取新闻
    print("\n开始获取新闻...")
    news = fetcher.fetch()
    print(f"获取到 {len(news)} 条新闻")
    
    # 显示前5条
    if news:
        print("\n前5条新闻:")
        for i, item in enumerate(news[:5], 1):
            print(f"{i}. [{item.source}] {item.title}")