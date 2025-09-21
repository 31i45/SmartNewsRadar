#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Data Fetcher - 增强版数据获取器
支持多种数据源：newsnow API + 直接爬取 + RSS订阅

Author: Inspired by Jobs' philosophy of comprehensiveness
"""

import asyncio
import aiohttp
import feedparser
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Union
import logging
import json
import re
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class NewsSource:
    """新闻源配置"""
    id: str
    name: str
    source_type: str  # 'newsnow_api', 'rss', 'web_scraper'
    url: str
    selector: Optional[str] = None  # 用于网页抓取的CSS选择器
    enabled: bool = True

class EnhancedDataFetcher:
    """增强版数据获取器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # 预定义的新闻源配置
        self.news_sources = self._init_news_sources()
    
    def _init_news_sources(self) -> List[NewsSource]:
        """初始化新闻源配置"""
        sources = []
        
        # NewNow API 数据源（完整38个源）
        newsnow_sources = [
            # 社交媒体平台 (6个)
            NewsSource("weibo", "微博热搜", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=weibo&latest"),
            NewsSource("douyin", "抖音热搜", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=douyin&latest"),
            NewsSource("kuaishou", "快手热搜", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=kuaishou&latest"),
            NewsSource("tieba", "百度贴吧", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=tieba&latest"),
            NewsSource("coolapk", "酷安社区", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=coolapk&latest"),
            NewsSource("hupu", "虎扑社区", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=hupu&latest"),
            
            # 传统新闻媒体 (5个)
            NewsSource("toutiao", "今日头条", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=toutiao&latest"),
            NewsSource("ifeng", "凤凰网", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=ifeng&latest"),
            NewsSource("thepaper", "澎湃新闻", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=thepaper&latest"),
            NewsSource("cankaoxiaoxi", "参考消息", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=cankaoxiaoxi&latest"),
            NewsSource("zaobao", "联合早报", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=zaobao&latest"),
            
            # 财经金融媒体 (7个)
            NewsSource("wallstreetcn", "华尔街见闻", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=wallstreetcn-hot&latest"),
            NewsSource("_36kr", "36氪", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=_36kr&latest"),
            NewsSource("xueqiu", "雪球", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=xueqiu&latest"),
            NewsSource("gelonghui", "格隆汇", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=gelonghui&latest"),
            NewsSource("fastbull", "快牛财经", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=fastbull&latest"),
            NewsSource("jin10", "金十数据", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=jin10&latest"),
            NewsSource("mktnews", "市场新闻", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=mktnews&latest"),
            
            # 科技数码媒体 (6个)
            NewsSource("ithome", "IT之家", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=ithome&latest"),
            NewsSource("juejin", "掘金", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=juejin&latest"),
            NewsSource("sspai", "少数派", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=sspai&latest"),
            NewsSource("smzdm", "什么值得买", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=smzdm&latest"),
            NewsSource("chongbuluo", "虫部落", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=chongbuluo&latest"),
            NewsSource("pcbeta", "远景论坛", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=pcbeta&latest"),
            
            # 技术开发社区 (4个)
            NewsSource("github", "GitHub趋势", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=github&latest"),
            NewsSource("v2ex", "V2EX", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=v2ex&latest"),
            NewsSource("linuxdo", "Linux Do", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=linuxdo&latest"),
            NewsSource("hackernews", "Hacker News", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=hackernews&latest"),
            
            # 知识学习平台 (3个)
            NewsSource("zhihu", "知乎热榜", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=zhihu&latest"),
            NewsSource("nowcoder", "牛客网", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=nowcoder&latest"),
            NewsSource("kaopu", "考普网", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=kaopu&latest"),
            
            # 娱乐视频平台 (2个)
            NewsSource("bilibili", "B站热搜", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=bilibili-hot-search&latest"),
            NewsSource("ghxi", "光华喜", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=ghxi&latest"),
            
            # 其他特色平台 (5个)
            NewsSource("baidu", "百度热搜", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=baidu&latest"),
            NewsSource("producthunt", "Product Hunt", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=producthunt&latest"),
            NewsSource("solidot", "Solidot", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=solidot&latest"),
            NewsSource("sputniknewscn", "俄罗斯卫星通讯社", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=sputniknewscn&latest"),
            NewsSource("cls", "财联社", "newsnow_api", "https://newsnow.busiyi.world/api/s?id=cls&latest"),
        ]
        sources.extend(newsnow_sources)
        
        # RSS 数据源
        rss_sources = [
            # 综合新闻媒体
            NewsSource("sina_news", "新浪新闻", "rss", "http://rss.sina.com.cn/news/allnews/sports.xml"),
            NewsSource("sina_headlines", "新浪头条", "rss", "http://rss.sina.com.cn/news/marquee/ddt.xml"),
            NewsSource("163_news", "网易新闻", "rss", "http://news.163.com/special/00011K6L/rss_newstop.xml"),
            NewsSource("163_tech", "网易科技", "rss", "http://tech.163.com/special/00097UHL/tech_datalist.xml"),
            NewsSource("qq_news", "腾讯新闻", "rss", "https://news.qq.com/newsgn/rss_newsgn.xml"),
            NewsSource("sohu_news", "搜狐新闻", "rss", "http://news.sohu.com/rss/guonei.xml"),
            NewsSource("ifeng_news", "凤凰网", "rss", "https://news.ifeng.com/rss/index.xml"),
            
            # 财经金融媒体
            NewsSource("caixin", "财新网", "rss", "http://rss.caixin.com/blog/rss.xml"),
            NewsSource("36kr", "36氪", "rss", "https://36kr.com/feed"),
            NewsSource("huxiu", "虎嗅", "rss", "https://www.huxiu.com/rss/0.xml"),
            NewsSource("nbd", "每日经济新闻", "rss", "https://www.nbd.com.cn/rss/"),
            NewsSource("yicai", "第一财经", "rss", "https://m.yicai.com/rss/yicaihome.xml"),
            NewsSource("eastmoney", "东方财富网", "rss", "https://finance.eastmoney.com/rss/default.xml"),
            NewsSource("jrj", "金融界", "rss", "https://www.jrj.com.cn/rss/jryw.xml"),
            
            # 科技媒体
            NewsSource("cnbeta", "CNBeta", "rss", "https://www.cnbeta.com/backend.php"),
            NewsSource("ithome_tech", "IT之家科技", "rss", "https://rss.ithome.com/rss/ithome.xml"),
            NewsSource("ifanr", "爱范儿", "rss", "https://www.ifanr.com/feed"),
            NewsSource("sspai", "少数派", "rss", "https://sspai.com/feed"),
            
            # 权威媒体
            NewsSource("cctv", "央视新闻", "rss", "https://news.cctv.com/rss/news.shtml"),
            NewsSource("jiemian", "界面新闻", "rss", "https://a.jiemian.com/index.php/Api/Rss/getList/cid/1"),
            NewsSource("ecns", "中国日报网", "rss", "https://www.ecns.cn/rss/rss.xml"),
            NewsSource("ceweekly", "中国经济周刊", "rss", "https://www.ceweekly.cn/feed/"),
            
            # 国际媒体（中文）
            NewsSource("globaltimes", "环球时报", "rss", "https://www.globaltimes.cn/rss/china.xml"),
            NewsSource("scmp", "南华早报", "rss", "https://www.scmp.com/rss/4/feed"),
            NewsSource("reuters_cn", "路透中文网", "rss", "https://cn.reuters.com/rssFeed/CNAheadlinesNews"),
        ]
        sources.extend(rss_sources)
        
        # 网页抓取数据源（备用）
        web_sources = [
            NewsSource("qq_news", "腾讯新闻", "web_scraper", "https://news.qq.com/", ".Q-tpWrap .linkto"),
            NewsSource("sohu_news", "搜狐新闻", "web_scraper", "https://news.sohu.com/", ".news-text h4 a"),
            NewsSource("ifeng", "凤凰网", "web_scraper", "https://news.ifeng.com/", ".news_1 a"),
            NewsSource("jiemian", "界面新闻", "web_scraper", "https://www.jiemian.com/", ".news-list .news-item h3 a"),
            # 扩展网页抓取源 - 综合新闻
            NewsSource("people", "人民网", "web_scraper", "http://www.people.com.cn/", ".headlineNews a"),
            NewsSource("xinhua", "新华网", "web_scraper", "http://www.xinhuanet.com/", ".news-list li a"),
            NewsSource("china", "中国网", "web_scraper", "https://www.china.com.cn/", ".headline a"),
            NewsSource("cctv", "央视新闻", "web_scraper", "https://news.cctv.com/", ".cm-content a"),
            NewsSource("thepaper", "澎湃新闻", "web_scraper", "https://www.thepaper.cn/", ".news_title a"),
            # 扩展网页抓取源 - 财经金融
            NewsSource("eastmoney", "东方财富网", "web_scraper", "https://finance.eastmoney.com/", ".news_list .news_item a"),
            NewsSource("jrj", "金融界", "web_scraper", "https://www.jrj.com.cn/", ".news-list a"),
            NewsSource("wallstreetcn", "华尔街见闻", "web_scraper", "https://wallstreetcn.com/", ".news-item__title a"),
            NewsSource("huxiu", "虎嗅", "web_scraper", "https://www.huxiu.com/", ".article-item-title a"),
            # 扩展网页抓取源 - 科技数码
            NewsSource("ithome", "IT之家", "web_scraper", "https://www.ithome.com/", ".news_title a"),
            NewsSource("cnbeta", "CNBeta", "web_scraper", "https://www.cnbeta.com/", ".title h2 a"),
            NewsSource("ifanr", "爱范儿", "web_scraper", "https://www.ifanr.com/", ".article-title a"),
            NewsSource("36kr", "36氪", "web_scraper", "https://36kr.com/", ".article-item-title a"),
            # 扩展网页抓取源 - 娱乐时尚
            NewsSource("ent163", "网易娱乐", "web_scraper", "https://ent.163.com/", ".main-news a"),
            NewsSource("sohu_ent", "搜狐娱乐", "web_scraper", "https://yule.sohu.com/", ".news-item-title a"),
            NewsSource("mtime", "时光网", "web_scraper", "https://www.mtime.com/", ".news-item h3 a"),
            NewsSource("elle", "ELLE中文网", "web_scraper", "https://www.ellechina.com/", ".article-title a"),
        ]
        sources.extend(web_sources)
        
        return sources
    
    async def fetch_all_news_async(self) -> List[Dict]:
        """异步获取所有新闻源的数据"""
        all_news = []
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'Mozilla/5.0 (compatible; SmartNewsRadar/1.0)'}
        ) as session:
            tasks = []
            
            for source in self.news_sources:
                if not source.enabled:
                    continue
                    
                if source.source_type == "newsnow_api":
                    task = self._fetch_newsnow_api(session, source)
                elif source.source_type == "rss":
                    task = self._fetch_rss_feed(session, source)
                elif source.source_type == "web_scraper":
                    task = self._fetch_web_content(session, source)
                else:
                    continue
                
                tasks.append(task)
            
            # 并发执行所有任务
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"获取 {self.news_sources[i].name} 失败: {result}")
                elif result:
                    all_news.extend(result)
        
        logger.info(f"总共获取到 {len(all_news)} 条新闻，来自 {len([r for r in results if not isinstance(r, Exception)])} 个源")
        return all_news
    
    async def _fetch_newsnow_api(self, session: aiohttp.ClientSession, source: NewsSource) -> List[Dict]:
        """获取 NewNow API 数据"""
        try:
            async with session.get(source.url) as response:
                if response.status == 200:
                    data = await response.json()
                    items = data.get('items', [])
                    
                    news_items = []
                    for idx, item in enumerate(items, 1):
                        news_items.append({
                            'title': item['title'],
                            'source': source.name,
                            'rank': idx,
                            'url': item.get('url', ''),
                            'timestamp': datetime.now().isoformat()
                        })
                    
                    logger.info(f"NewNow API - {source.name}: {len(news_items)} 条新闻")
                    return news_items
                else:
                    logger.warning(f"NewNow API - {source.name} 返回状态码: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"NewNow API - {source.name} 请求失败: {e}")
            return []
    
    async def _fetch_rss_feed(self, session: aiohttp.ClientSession, source: NewsSource) -> List[Dict]:
        """获取 RSS 订阅数据"""
        try:
            async with session.get(source.url) as response:
                if response.status == 200:
                    content = await response.text()
                    feed = feedparser.parse(content)
                    
                    news_items = []
                    for idx, entry in enumerate(feed.entries[:30], 1):  # 限制30条
                        news_items.append({
                            'title': entry.get('title', '').strip(),
                            'source': source.name,
                            'rank': idx,
                            'url': entry.get('link', ''),
                            'timestamp': datetime.now().isoformat(),
                            'description': entry.get('summary', '')[:100]  # 摘要前100字符
                        })
                    
                    logger.info(f"RSS - {source.name}: {len(news_items)} 条新闻")
                    return news_items
                else:
                    logger.warning(f"RSS - {source.name} 返回状态码: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"RSS - {source.name} 请求失败: {e}")
            return []
    
    async def _fetch_web_content(self, session: aiohttp.ClientSession, source: NewsSource) -> List[Dict]:
        """网页内容抓取（简单实现）"""
        try:
            async with session.get(source.url) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    news_items = []
                    if source.selector:
                        elements = soup.select(source.selector)[:20]  # 限制20条
                        
                        for idx, element in enumerate(elements, 1):
                            title = element.get_text().strip()
                            url = element.get('href', '')
                            
                            # 处理相对URL
                            if url and not url.startswith('http'):
                                if url.startswith('/'):
                                    base_url = '/'.join(source.url.split('/')[:3])
                                    url = base_url + url
                                else:
                                    url = source.url.rstrip('/') + '/' + url.lstrip('/')
                            
                            if title and len(title) > 5:  # 过滤太短的标题
                                news_items.append({
                                    'title': title,
                                    'source': source.name,
                                    'rank': idx,
                                    'url': url,
                                    'timestamp': datetime.now().isoformat()
                                })
                    
                    logger.info(f"Web Scraper - {source.name}: {len(news_items)} 条新闻")
                    return news_items
                else:
                    logger.warning(f"Web Scraper - {source.name} 返回状态码: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Web Scraper - {source.name} 请求失败: {e}")
            return []
    
    def fetch_all_news(self) -> List[Dict]:
        """同步方法包装异步获取"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.fetch_all_news_async())
    
    def add_custom_source(self, source: NewsSource):
        """添加自定义新闻源"""
        self.news_sources.append(source)
        logger.info(f"添加自定义新闻源: {source.name}")
    
    def enable_source(self, source_id: str):
        """启用指定新闻源"""
        for source in self.news_sources:
            if source.id == source_id:
                source.enabled = True
                logger.info(f"启用新闻源: {source.name}")
                return
        logger.warning(f"未找到新闻源: {source_id}")
    
    def disable_source(self, source_id: str):
        """禁用指定新闻源"""
        for source in self.news_sources:
            if source.id == source_id:
                source.enabled = False
                logger.info(f"禁用新闻源: {source.name}")
                return
        logger.warning(f"未找到新闻源: {source_id}")
    
    def get_available_sources(self) -> List[Dict]:
        """获取所有可用新闻源列表"""
        return [
            {
                'id': source.id,
                'name': source.name,
                'type': source.source_type,
                'enabled': source.enabled
            }
            for source in self.news_sources
        ]

# 使用示例
if __name__ == "__main__":
    import asyncio
    
    # 简单测试
    fetcher = EnhancedDataFetcher({})
    
    # 获取所有可用源
    sources = fetcher.get_available_sources()
    print("可用新闻源:")
    for source in sources:
        print(f"  - {source['name']} ({source['type']})")
    
    # 测试获取新闻
    print("\n开始获取新闻...")
    news = fetcher.fetch_all_news()
    print(f"获取到 {len(news)} 条新闻")
    
    # 显示前5条
    for i, item in enumerate(news[:5], 1):
        print(f"{i}. [{item['source']}] {item['title']}")