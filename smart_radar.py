# -*- coding: utf-8 -*-
"""SmartNewsRadar - 智能新闻关键词发现系统
基于AI驱动的真实世界热点关键词自动发现
"""

import asyncio
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set, Optional

import jieba
import jieba.analyse
import yaml
from dataclasses import dataclass, field

# 导入自定义模块
from enhanced_data_fetcher import NewsFetcher
from smart_learning import SmartLearningEngine  
from smart_presentation import present_results

# 配置日志 - 极简高效
import logging
# 确保这是程序中第一个配置日志的地方
# 添加force=True参数确保覆盖其他模块的配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('smart_radar.log', encoding='utf-8'),
        logging.StreamHandler()
    ],
    force=True  # 强制覆盖其他配置
) 
logger = logging.getLogger(__name__)
VERSION = "5.1.0"

@dataclass
class Keyword:
    """关键词数据类 - 只保留最核心的属性"""
    word: str
    frequency: int
    trend_score: float
    importance: float = 0.0
    insights: Dict = field(default_factory=dict)
    
    def calculate_importance(self, weights: Optional[Dict] = None) -> None:
        """计算关键词重要性 - 简洁高效的算法"""
        if weights is None:
            weights = {'frequency_weight': 0.4, 'trend_weight': 0.6}
        
        self.importance = (
            self.frequency * weights['frequency_weight'] +
            self.trend_score * weights['trend_weight']
        )

class SystemState:
    """系统状态管理器 - 统一管理系统状态"""
    IDLE = 'idle'
    FETCHING = 'fetching'
    ANALYZING = 'analyzing'
    LEARNING = 'learning'
    PRESENTING = 'presenting'  # 添加展示状态
    COMPLETED = 'completed'    # 添加完成状态
    ERROR = 'error'
    
    def __init__(self):
        self.state = self.IDLE
        self.last_error = None
        self.start_time = datetime.now()
        self.metrics = {}
        
    def set_state(self, state: str, error: Optional[Exception] = None) -> None:
        self.state = state
        self.last_error = error
        
        # 添加状态变更详情
        details = {
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': (datetime.now() - self.start_time).total_seconds()
        }
        
        if error:
            error_type = type(error).__name__
            error_msg = str(error)[:100]  # 限制错误信息长度
            details['error'] = f"{error_type}: {error_msg}"
            logger.error(f"系统状态变更为: {state}, 错误: {details['error']}")
        else:
            logger.info(f"系统状态变更为: {state}")
    
    def update_metrics(self, metrics: Dict) -> None:
        """更新系统运行指标"""
        self.metrics.update(metrics)
        
    def get_status_summary(self) -> Dict:
        """获取系统状态摘要"""
        return {
            'state': self.state,
            'running_time': (datetime.now() - self.start_time).total_seconds(),
            'metrics': self.metrics,
            'last_error': self.last_error is not None
        }

class KeywordAnalyzer:
    """智能关键词分析器 - 专注于高质量关键词提取"""
    
    def __init__(self):
        self.stopwords = self._load_stopwords()
        self._setup_jieba()
        
    def _setup_jieba(self) -> None:
        """配置jieba分词器以获得最佳性能"""
        import platform
        if platform.system() != 'Windows':
            try:
                jieba.enable_parallel(4)  # 只在非Windows系统上开启并行分词
            except Exception as e:
                logger.warning(f"启用并行分词失败: {e}")
    
    def _load_stopwords(self) -> Set[str]:
        """加载优化后的停用词表 - 专注于中文新闻文本"""
        return {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
            '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
            '自己', '这', '那', '为', '与', '或', '以及', '因为', '所以', '但是', '然而',
            '网友', '用户', '表示', '认为', '称', '据', '显示', '报道', '消息', '记者',
            '今日', '昨日', '明日', '今天', '昨天', '明天', '上午', '下午', '晚上',
            '最新', '热门', '热搜', '排行', '榜单', '第一', '第二', '第三'
        }
    
    async def extract_keywords(self, news_items: List, max_keywords: int = 20) -> List[Keyword]:
        """异步从新闻中提取高质量关键词"""
        if not news_items:
            return []
        
        # 提取所有标题文本
        all_titles = [item.title for item in news_items]
        
        # 使用jieba的TF-IDF提取关键词
        combined_text = ' '.join(all_titles)
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
        
        # 处理关键词计算
        keywords = []
        for word, tfidf_weight in keywords_with_weight:
            if word in self.stopwords or len(word) < 2:
                continue
            
            freq = word_freq.get(word, 0)
            if freq < 2:  # 过滤低频词
                continue
            
            trend_score = self._calculate_trend_score(word, news_items)
            
            keyword = Keyword(
                word=word,
                frequency=freq,
                trend_score=trend_score
            )
            keyword.calculate_importance()
            keywords.append(keyword)
        
        # 按重要性排序
        keywords.sort(key=lambda x: x.importance, reverse=True)
        
        return keywords[:max_keywords]
    
    def _segment_text(self, text: str) -> List[str]:
        """使用jieba进行中文文本分词 - 精简高效"""
        # 移除数字、符号等
        text = re.sub(r'[^一-龥a-zA-Z]+', ' ', text)
        
        # 使用jieba分词
        words = jieba.cut(text)
        
        # 过滤停用词和短词
        return [word for word in words if word not in self.stopwords and len(word) >= 2]
    
    def _calculate_trend_score(self, word: str, news_items: List) -> float:
        """计算关键词趋势分数 - 基于新闻排名的简洁算法"""
        matching_items = [item for item in news_items if word in item.title]
        if not matching_items:
            return 0.0
        
        avg_rank = sum(max(0, 20 - item.rank) for item in matching_items) / len(matching_items)
        return min(1.0, avg_rank / 20.0)

class SmartNewsRadar:
    """智能新闻雷达主类 - 简洁优雅的协调者"""
    
    def __init__(self, config_file: str = 'smart_config.yaml'):
        self.config = self._load_config(config_file)
        
        # 初始化核心组件
        self.news_fetcher = NewsFetcher("news_sources.json")
        self.analyzer = KeywordAnalyzer()
        self.learning_engine = SmartLearningEngine(self.config.get('learning', {}))
        self.state_manager = SystemState()
    
    def _load_config(self, config_file: str) -> Dict:
        """加载配置文件"""
        if not Path(config_file).exists():
            # 如果配置文件不存在，使用默认配置
            return {'core': {'max_keywords': 50}}
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {'core': {'max_keywords': 50}}
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"加载配置文件失败: {error_type}")
            return {'core': {'max_keywords': 50}}
    
    async def run(self):
        """异步运行主程序 - 优雅高效的流程控制"""
        logger.info(f"SmartNewsRadar v{VERSION} 启动")
        
        try:
            # 获取新闻数据
            logger.info("开始获取新闻数据...")
            self.state_manager.set_state(SystemState.FETCHING)
            news_items = await self._safe_fetch_news()
            
            logger.info(f"共获取到 {len(news_items)} 条新闻")
            self.state_manager.update_metrics({'news_count': len(news_items)})
            
            if not news_items:
                logger.warning("没有获取到任何新闻数据")
                return
            
            # 分析关键词
            logger.info("开始分析关键词...")
            self.state_manager.set_state(SystemState.ANALYZING)
            max_keywords = self.config.get('core', {}).get('max_keywords', 50)
            keywords = await self.analyzer.extract_keywords(news_items, max_keywords)
            
            logger.info(f"自动发现 {len(keywords)} 个关键词")
            self.state_manager.update_metrics({'keywords_count': len(keywords)})
            
            # 调用学习引擎
            logger.info("开始自适应学习...")
            self.state_manager.set_state(SystemState.LEARNING)
            self.learning_engine.learn_from_keywords(keywords, news_items)
            
            # 更新关键词洞察
            self._enrich_keywords_with_insights(keywords)
            
            # 构建新闻摘要
            news_summary = []
            for item in news_items[:10]:  # 前10条新闻
                news_summary.append({
                    'title': item.title,
                    'source': item.source,
                    'rank': item.rank if hasattr(item, 'rank') else 0
                })
            
            # 获取学习统计数据
            learning_stats = {
                'keywords_count': len(self.learning_engine._learning_data.get('keywords', {})),
                'weights_adjusted': len(self.learning_engine._learning_data.get('weight_history', [])),
                'current_weights': self.learning_engine.optimal_weights
            }
            
            # 构建完整的分析结果数据
            analysis_result = {
                'timestamp': datetime.now().isoformat(),
                'total_news': len(news_items),
                'keywords': [kw.__dict__ for kw in keywords],  # 转换为字典格式
                'news_summary': news_summary,
                'learning_stats': learning_stats  # 添加学习统计数据
            }
            
            # 使用新的展示层呈现结果
            logger.info("开始生成分析报告...")
            self.state_manager.set_state(SystemState.PRESENTING)
            
            # 首先生成HTML报告
            report_path = present_results(analysis_result, "html", self.config)
            # 移除下面这行重复的日志
            # logger.info(f"HTML分析报告已生成: {report_path}")
            
            # 检查配置是否需要生成JSON报告
            if self.config.get('presentation', {}).get('generate_json', True):
                json_path = present_results(analysis_result, "json", self.config)
                # 同样移除这行重复的日志
                # logger.info(f"JSON分析报告已生成: {json_path}")
            
            # 然后使用控制台格式输出，确保用户能在命令行看到结果
            console_output = present_results(analysis_result, "console", self.config)
            
            self.state_manager.set_state(SystemState.COMPLETED)
            
            # 添加HTML报告地址显示和自动打开浏览器功能
            if report_path:
                print(f"\n✨ 分析已完成！HTML报告已生成:\n📁 {report_path}")
                # 询问用户是否要打开浏览器查看报告
                try:
                    import webbrowser
                    import os
                    # 获取绝对路径并转换为URL格式
                    abs_path = os.path.abspath(report_path)
                    # 对于Windows系统，需要特别处理路径格式
                    if os.name == 'nt':  # Windows系统
                        url = f"file:///{abs_path.replace('\\', '/')}"
                    else:  # 其他系统
                        url = f"file://{abs_path}"
                    
                    # 自动打开浏览器
                    webbrowser.open(url)
                    print(f"🌐 已尝试自动打开浏览器查看报告")
                except Exception as e:
                    print(f"⚠️ 无法自动打开浏览器: {str(e)}")
                    print(f"📌 请手动打开文件: {report_path}")
            
            return keywords
            
        except Exception as e:
            self.state_manager.set_state(SystemState.ERROR, e)
            logger.error(f"程序运行出错: {e}", exc_info=True)
            return []
    
    async def _safe_fetch_news(self):
        """安全获取新闻数据，带重试机制"""
        max_retries = 2
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, self.news_fetcher.fetch)
            except Exception as e:
                retry_count += 1
                if retry_count > max_retries:
                    raise
                error_type = type(e).__name__
                logger.warning(f"获取新闻数据失败({error_type})，正在重试 ({retry_count}/{max_retries})...")
                await asyncio.sleep(2)  # 等待2秒后重试
    
    def _enrich_keywords_with_insights(self, keywords: List[Keyword]) -> None:
        """为关键词添加学习引擎提供的洞察"""
        for keyword in keywords[:10]:  # 取排名靠前的关键词
            insights = self.learning_engine.get_keyword_insights(keyword.word)
            if insights:
                keyword.insights = {
                    'trend': insights.get('trend_direction', 'unknown'),
                    'appearances': insights.get('appearances', 0),
                    'first_seen': insights.get('first_seen', 'unknown')
                }
    
    def start(self):
        """启动程序入口"""
        try:
            asyncio.run(self.run())
        except RuntimeError:
            # 处理事件循环已存在的情况
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.run())
            finally:
                loop.close()

    # 修复process_news方法
    async def process_news(self) -> List[Dict]:
        """处理新闻数据，提取关键词并进行分析"""
        try:
            # 直接调用run方法获取关键词
            keywords = await self.run()
            return [kw.__dict__ for kw in keywords] if keywords else []
        except Exception as e:
            logger.error(f"处理新闻数据出错: {e}")
            return []

if __name__ == "__main__":
    radar = SmartNewsRadar()
    radar.start()