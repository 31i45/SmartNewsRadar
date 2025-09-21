# -*- coding: utf-8 -*-
"""
SmartNewsRadar - 智能新闻关键词发现系统
基于AI驱动的真实世界热点关键词自动发现

Author: Inspired by Jobs' philosophy of simplicity
Version: 1.0.0
License: MIT
"""

import json
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from collections import Counter, defaultdict
import math
import logging
import asyncio

import requests
import yaml
from dataclasses import dataclass

# 导入自定义模块
from smart_learning import AdaptiveLearningEngine
from smart_notifier import SmartNotifier
# 使用更高级的分词库
import jieba
import jieba.analyse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('smart_radar.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

VERSION = "1.0.0"

@dataclass
class NewsItem:
    """新闻项数据类"""
    title: str
    source: str
    rank: int
    url: str = ""
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class Keyword:
    """关键词数据类"""
    word: str
    frequency: int
    trend_score: float
    sentiment_score: float
    importance: float = 0.0
    
    def calculate_importance(self, weights=None):
        """计算关键词重要性"""
        if weights is None:
            weights = {
                'frequency_weight': 0.4,
                'trend_weight': 0.4,
                'sentiment_weight': 0.2
            }
        
        self.importance = (
            self.frequency * weights['frequency_weight'] +
            self.trend_score * weights['trend_weight'] +
            abs(self.sentiment_score) * weights['sentiment_weight']
        )

class SmartKeywordAnalyzer:
    """智能关键词分析器"""
    
    def __init__(self, learning_engine=None):
        self.stopwords = self._load_stopwords()
        self.keyword_history = defaultdict(list)
        self.learning_engine = learning_engine  # 自适应学习引擎
        
        # 配置jieba分词
        self._setup_jieba()
        
    def _setup_jieba(self):
        """配置jieba分词器"""
        # 添加自定义词典（如果有）
        # jieba.load_userdict('custom_dict.txt')
        
        # 导入platform模块检测操作系统
        import platform
        if platform.system() != 'Windows':
            # 只在非Windows系统上开启并行分词
            try:
                jieba.enable_parallel(4)  # 使用4个进程
            except Exception as e:
                logger.warning(f"启用并行分词失败: {e}")
        
        # 移除set_idf_path(None)调用，直接使用默认的TF-IDF配置
        # jieba会自动使用内置的idf权重，不需要额外配置
        
    def _load_stopwords(self) -> Set[str]:
        """加载停用词表"""
        default_stopwords = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
            '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
            '自己', '这', '那', '为', '与', '或', '以及', '因为', '所以', '但是', '然而',
            '网友', '用户', '表示', '认为', '称', '据', '显示', '报道', '消息', '记者',
            '今日', '昨日', '明日', '今天', '昨天', '明天', '上午', '下午', '晚上',
            '最新', '热门', '热搜', '排行', '榜单', '第一', '第二', '第三'
        }
        return default_stopwords
    
    def extract_keywords(self, news_items: List[NewsItem], max_keywords: int = 20) -> List[Keyword]:
        """从新闻中提取关键词"""
        # 提取所有标题文本
        all_titles = [item.title for item in news_items]
        
        # 使用jieba的TF-IDF提取关键词
        # 首先合并所有标题
        combined_text = ' '.join(all_titles)
        
        # 提取关键词及其权重
        keywords_with_weight = jieba.analyse.extract_tags(
            combined_text, 
            topK=max_keywords * 2,  # 提取更多关键词以过滤
            withWeight=True, 
            allowPOS=('n', 'nr', 'ns', 'nt', 'nz')  # 只提取名词相关词性
        )
        
        # 统计词频
        all_words = []
        for title in all_titles:
            words = self._segment_text(title)
            all_words.extend(words)
        word_freq = Counter(all_words)
        
        # 如果有学习引擎，获取当前最优权重
        weights = None
        if self.learning_engine:
            weights = self.learning_engine.optimal_weights
            logger.info(f"使用自适应学习权重: {weights}")
        
        keywords = []
        for word, tfidf_weight in keywords_with_weight:
            if word in self.stopwords or len(word) < 2:
                continue
            
            # 获取词频
            freq = word_freq.get(word, 0)
            if freq < 2:  # 过滤低频词
                continue
            
            trend_score = self._calculate_trend_score(word, news_items)
            sentiment_score = self._analyze_sentiment(word, news_items)
            
            keyword = Keyword(
                word=word,
                frequency=freq,
                trend_score=trend_score,
                sentiment_score=sentiment_score
            )
            keyword.calculate_importance(weights)
            keywords.append(keyword)
        
        # 按重要性排序
        keywords.sort(key=lambda x: x.importance, reverse=True)
        
        # 更新历史记录
        self._update_keyword_history(keywords)
        
        # 如果有学习引擎，从结果中学习
        if self.learning_engine:
            selected_keywords = keywords[:max_keywords]
            updated_weights = self.learning_engine.learn_from_keywords(selected_keywords, news_items)
            logger.info(f"学习引擎分析完成，更新权重: {updated_weights}")
        
        return keywords[:max_keywords]
    
    def _segment_text(self, text: str) -> List[str]:
        """使用jieba进行中文文本分词"""
        # 移除数字、符号等
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z]+', ' ', text)
        
        # 使用jieba分词
        words = jieba.cut(text)
        
        # 过滤停用词和短词
        filtered_words = [
            word for word in words 
            if word not in self.stopwords and len(word) >= 2
        ]
        
        return filtered_words
    
    def _calculate_trend_score(self, word: str, news_items: List[NewsItem]) -> float:
        """计算关键词趋势分数"""
        # 基于新闻排名和时间的趋势分析
        rank_scores = []
        for item in news_items:
            if word in item.title:
                # 排名越高分数越高
                rank_score = max(0, 20 - item.rank)
                rank_scores.append(rank_score)
        
        if not rank_scores:
            return 0.0
        
        # 计算平均排名分数
        avg_rank_score = sum(rank_scores) / len(rank_scores)
        
        # 归一化到0-1
        return min(1.0, avg_rank_score / 20.0)
    
    def _analyze_sentiment(self, word: str, news_items: List[NewsItem]) -> float:
        """简单的情感分析"""
        positive_indicators = ['成功', '突破', '增长', '上涨', '胜利', '好', '优', '赞', '棒']
        negative_indicators = ['失败', '下跌', '危机', '问题', '错误', '差', '坏', '批评']
        
        sentiment_score = 0.0
        count = 0
        
        for item in news_items:
            if word in item.title:
                title_lower = item.title.lower()
                for pos in positive_indicators:
                    if pos in title_lower:
                        sentiment_score += 1
                for neg in negative_indicators:
                    if neg in title_lower:
                        sentiment_score -= 1
                count += 1
        
        return sentiment_score / max(1, count)
    
    def _update_keyword_history(self, keywords: List[Keyword]):
        """更新关键词历史记录"""
        current_time = datetime.now()
        for keyword in keywords:
            self.keyword_history[keyword.word].append({
                'timestamp': current_time,
                'frequency': keyword.frequency,
                'importance': keyword.importance
            })
            
            # 只保留最近7天的记录
            self.keyword_history[keyword.word] = [
                record for record in self.keyword_history[keyword.word]
                if current_time - record['timestamp'] <= timedelta(days=7)
            ]

class SmartReportGenerator:
    """智能报告生成器"""
    
    def __init__(self, config: Dict):
        self.config = config
    
    def generate_html_report(self, keywords: List[Keyword], news_items: List[NewsItem]) -> str:
        """生成HTML报告"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>智能新闻雷达 - 自动发现的热点关键词</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        }}
        
        .header {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            font-weight: 300;
            margin-bottom: 10px;
        }}
        
        .header .subtitle {{
            font-size: 1.1rem;
            opacity: 0.9;
        }}
        
        .content {{
            padding: 40px 30px;
        }}
        
        .keywords-section {{
            margin-bottom: 50px;
        }}
        
        .section-title {{
            font-size: 1.8rem;
            font-weight: 600;
            margin-bottom: 30px;
            color: #1e3c72;
        }}
        
        .keywords-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .keyword-card {{
            background: #f8f9ff;
            padding: 20px;
            border-radius: 15px;
            border-left: 4px solid #2a5298;
            transition: transform 0.3s ease;
        }}
        
        .keyword-card:hover {{
            transform: translateY(-5px);
        }}
        
        .keyword-title {{
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 10px;
            color: #1e3c72;
        }}
        
        .keyword-stats {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 15px;
        }}
        
        .stat {{
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 1.1rem;
            font-weight: 600;
            color: #2a5298;
        }}
        
        .stat-label {{
            font-size: 0.8rem;
            color: #666;
            margin-top: 5px;
        }}
        
        .importance-bar {{
            height: 6px;
            background: #e0e0e0;
            border-radius: 3px;
            overflow: hidden;
        }}
        
        .importance-fill {{
            height: 100%;
            background: linear-gradient(90deg, #2a5298, #667eea);
            transition: width 0.5s ease;
        }}
        
        .related-news {{
            margin-top: 15px;
        }}
        
        .news-item {{
            background: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 10px;
            border: 1px solid #e0e0e0;
        }}
        
        .news-source {{
            font-size: 0.8rem;
            color: #666;
            margin-bottom: 5px;
        }}
        
        .news-title {{
            font-size: 0.95rem;
            line-height: 1.4;
        }}
        
        .timestamp {{
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            background: #f8f9ff;
            border-radius: 10px;
            color: #666;
        }}
        
        @media (max-width: 768px) {{
            .keywords-grid {{
                grid-template-columns: 1fr;
            }}
            
            .header h1 {{
                font-size: 2rem;
            }}
            
            .content {{
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 智能新闻雷达</h1>
            <div class="subtitle">AI驱动的热点关键词自动发现系统</div>
        </div>
        
        <div class="content">
            <div class="keywords-section">
                <h2 class="section-title">🔥 自动发现的热点关键词</h2>
                <div class="keywords-grid">
                    {self._generate_keyword_cards(keywords, news_items)}
                </div>
            </div>
            
            <div class="timestamp">
                <div>数据更新时间: {timestamp}</div>
                <div style="margin-top: 10px; font-size: 0.9rem;">
                    共分析了 {len(news_items)} 条新闻，自动发现 {len(keywords)} 个热点关键词
                </div>
            </div>
        </div>
    </div>
</body>
</html>
        """
        
        return html_content
    
    def _generate_keyword_cards(self, keywords: List[Keyword], news_items: List[NewsItem]) -> str:
        """生成关键词卡片HTML"""
        cards_html = ""
        
        for keyword in keywords:
            # 找到包含该关键词的相关新闻
            related_news = [
                item for item in news_items
                if keyword.word in item.title
            ][:3]  # 只显示前3条相关新闻
            
            related_news_html = ""
            for news in related_news:
                related_news_html += f"""
                <div class="news-item">
                    <div class="news-source">[{news.source}] 排名 #{news.rank}</div>
                    <div class="news-title">{news.title}</div>
                </div>
                """
            
            cards_html += f"""
            <div class="keyword-card">
                <div class="keyword-title">{keyword.word}</div>
                <div class="keyword-stats">
                    <div class="stat">
                        <div class="stat-value">{keyword.frequency}</div>
                        <div class="stat-label">出现次数</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">{keyword.trend_score:.2f}</div>
                        <div class="stat-label">趋势指数</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">{keyword.importance:.1f}</div>
                        <div class="stat-label">重要性</div>
                    </div>
                </div>
                <div class="importance-bar">
                    <div class="importance-fill" style="width: {min(100, keyword.importance * 10)}%"></div>
                </div>
                <div class="related-news">
                    {related_news_html}
                </div>
            </div>
            """
        
        return cards_html
    
    def generate_json_report(self, keywords: List[Keyword], news_items: List[NewsItem]) -> Dict:
        """生成JSON格式报告"""
        return {
            'timestamp': datetime.now().isoformat(),
            'total_news': len(news_items),
            'total_keywords': len(keywords),
            'keywords': [
                {
                    'word': kw.word,
                    'frequency': kw.frequency,
                    'trend_score': kw.trend_score,
                    'sentiment_score': kw.sentiment_score,
                    'importance': kw.importance
                }
                for kw in keywords
            ],
            'news_summary': [
                {
                    'title': item.title,
                    'source': item.source,
                    'rank': item.rank
                }
                for item in news_items[:20]  # 只保存前20条新闻
            ]
        }

class SmartNewsRadar:
    """智能新闻雷达主类"""
    
    def __init__(self, config_file: str = 'smart_config.yaml'):
        self.config = self._load_config(config_file)
        
        # 初始化学习引擎
        self.learning_engine = AdaptiveLearningEngine(self.config)
        
        # 初始化组件 - 使用增强版数据获取器
        from enhanced_data_fetcher import EnhancedDataFetcher as RealEnhancedDataFetcher
        self.fetcher = RealEnhancedDataFetcher(self.config)
        self.analyzer = SmartKeywordAnalyzer(self.learning_engine)
        self.reporter = SmartReportGenerator(self.config)
        self.notifier = SmartNotifier(self.config)
        
        # 确保输出目录存在
        Path('output').mkdir(exist_ok=True)
    
    def _load_config(self, config_file: str) -> Dict:
        """加载配置文件"""
        if not Path(config_file).exists():
            # 如果配置文件不存在，使用默认配置
            return self._create_default_config()
        
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _create_default_config(self) -> Dict:
        """创建默认配置"""
        return {
            'data_sources': {
                'enhanced_mode': True,
                'timeout': 30,
                'concurrent_limit': 20,
                'newsnow_api': {
                    'enabled': True,
                    'sources': [
                        {'id': 'toutiao', 'name': '今日头条'},
                        {'id': 'baidu', 'name': '百度热搜'},
                        {'id': 'weibo', 'name': '微博热搜'},
                        {'id': 'zhihu', 'name': '知乎热榜'},
                        {'id': 'douyin', 'name': '抖音热搜'},
                        {'id': 'bilibili-hot-search', 'name': 'B站热搜'}
                    ]
                },
                'rss_feeds': {
                    'enabled': True,
                    'sources': []
                },
                'web_scraping': {
                    'enabled': False,
                    'sources': []
                }
            },
            'ai_analysis': {
                'max_keywords': 50,
                'weights': {
                    'frequency_weight': 0.4,
                    'trend_weight': 0.4,
                    'sentiment_weight': 0.2
                }
            },
            'notification': {
                'enabled': False,
                'webhooks': {}
            }
        }
    
    def run(self):
        """运行主程序"""
        logger.info(f"SmartNewsRadar v{VERSION} 启动")
        
        try:
            # 获取新闻数据
            logger.info("开始获取新闻数据...")
            
            # 使用异步方法获取所有数据源
            news_data = asyncio.run(self.fetcher.fetch_all_news_async())
            
            # 转换为NewsItem对象
            news_items = []
            for item in news_data:
                news_item = NewsItem(
                    title=item['title'],
                    source=item['source'],
                    rank=item['rank'],
                    url=item.get('url', ''),
                    timestamp=datetime.fromisoformat(item['timestamp'])
                )
                news_items.append(news_item)
            
            logger.info(f"共获取到 {len(news_items)} 条新闻")
            
            if not news_items:
                logger.warning("没有获取到任何新闻数据")
                return
            
            # 分析关键词
            logger.info("开始分析关键词...")
            max_keywords = self.config.get('ai_analysis', {}).get('max_keywords', 50)
            keywords = self.analyzer.extract_keywords(news_items, max_keywords)
            
            logger.info(f"自动发现 {len(keywords)} 个关键词")
            
            # 生成报告
            logger.info("生成报告...")
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 生成HTML报告
            html_report = self.reporter.generate_html_report(keywords, news_items)
            html_file = f"output/smart_radar_{timestamp}.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_report)
            
            # 生成JSON报告
            json_report = self.reporter.generate_json_report(keywords, news_items)
            json_file = f"output/smart_radar_{timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(json_report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"报告已生成: {html_file}, {json_file}")
            
            # 发送通知
            if self.config.get('notification', {}).get('enabled', False):
                self.notifier.send_notification(keywords[:10])  # 只发送前10个关键词
            else:
                logger.info("通知功能未启用")
            
            # 显示结果到控制台
            self._display_results(keywords)
            
        except Exception as e:
            logger.error(f"程序运行出错: {e}", exc_info=True)
    
    def _display_results(self, keywords: List[Keyword]):
        """在控制台显示结果"""
        print("\n🎯 自动发现的热点关键词:")
        print("============================================================")
        
        # 显示前10个关键词
        for i, keyword in enumerate(keywords[:10], 1):
            print(f"{i:2d}. {keyword.word:<10} | 重要性: {keyword.importance:5.2f} | 出现: {keyword.frequency:2d}次 | 趋势: {keyword.trend_score:.2f}")
        
        print("\n🤖 AI学习统计:")
        print(f"  • 学习关键词数: {len(keywords)}")
        
        if hasattr(self.analyzer, 'learning_engine') and self.analyzer.learning_engine:
            # 使用weight_history的长度作为权重调整次数
            print(f"  • 权重调整次数: {len(self.analyzer.learning_engine.weight_history)}")
            print(f"  • 当前最优权重:")
            for key, value in self.analyzer.learning_engine.optimal_weights.items():
                print(f"    - {key}: {value:.3f}")

if __name__ == "__main__":
    radar = SmartNewsRadar()
    radar.run()