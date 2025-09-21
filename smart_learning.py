#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SmartLearning - 自适应学习系统
让AI系统根据新闻热度变化自动调整和优化

Author: Inspired by Jobs' philosophy of continuous innovation
"""

import json
import pickle
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, deque
import math

logger = logging.getLogger(__name__)

class AdaptiveLearningEngine:
    """自适应学习引擎"""
    
    def __init__(self, config: Dict):
        self.config = config.get('learning', {})
        self.enabled = self.config.get('enabled', True)
        self.history_days = self.config.get('history_days', 7)
        self.auto_adjust = self.config.get('auto_adjust_weights', True)
        
        # 学习数据存储
        self.data_dir = Path('learning_data')
        self.data_dir.mkdir(exist_ok=True)
        
        # 历史数据
        self.keyword_performance = defaultdict(list)
        self.weight_history = deque(maxlen=50)  # 保留最近50次的权重调整
        self.trend_patterns = defaultdict(list)
        
        # 当前最优权重
        self.optimal_weights = {
            'frequency_weight': 0.4,
            'trend_weight': 0.4,
            'sentiment_weight': 0.2
        }
        
        # 加载历史学习数据
        self._load_learning_data()
    
    def _load_learning_data(self):
        """加载历史学习数据"""
        try:
            data_file = self.data_dir / 'learning_data.pkl'
            if data_file.exists():
                with open(data_file, 'rb') as f:
                    data = pickle.load(f)
                    self.keyword_performance = data.get('keyword_performance', defaultdict(list))
                    self.weight_history = deque(data.get('weight_history', []), maxlen=50)
                    self.trend_patterns = data.get('trend_patterns', defaultdict(list))
                    self.optimal_weights = data.get('optimal_weights', self.optimal_weights)
                logger.info("历史学习数据加载成功")
        except Exception as e:
            logger.warning(f"加载学习数据失败: {e}")
    
    def _save_learning_data(self):
        """保存学习数据"""
        try:
            data = {
                'keyword_performance': dict(self.keyword_performance),
                'weight_history': list(self.weight_history),
                'trend_patterns': dict(self.trend_patterns),
                'optimal_weights': self.optimal_weights,
                'last_update': datetime.now().isoformat()
            }
            
            data_file = self.data_dir / 'learning_data.pkl'
            with open(data_file, 'wb') as f:
                pickle.dump(data, f)
            
            # 同时保存JSON格式便于查看
            json_file = self.data_dir / 'learning_summary.json'
            with open(json_file, 'w', encoding='utf-8') as f:
                json_data = {
                    'optimal_weights': self.optimal_weights,
                    'total_keywords_learned': len(self.keyword_performance),
                    'weight_adjustments': len(self.weight_history),
                    'last_update': data['last_update']
                }
                json.dump(json_data, f, ensure_ascii=False, indent=2)
                
            logger.info("学习数据保存成功")
        except Exception as e:
            logger.error(f"保存学习数据失败: {e}")
    
    def learn_from_keywords(self, keywords: List, news_items: List) -> Dict:
        """从关键词结果中学习"""
        if not self.enabled:
            return self.optimal_weights
        
        current_time = datetime.now()
        
        # 记录每个关键词的表现
        for keyword in keywords:
            performance_data = {
                'timestamp': current_time,
                'importance': keyword.importance,
                'frequency': keyword.frequency,
                'trend_score': keyword.trend_score,
                'sentiment_score': keyword.sentiment_score,
                'real_impact': self._calculate_real_impact(keyword, news_items)
            }
            # 确保关键词在字典中存在
            if keyword.word not in self.keyword_performance:
                self.keyword_performance[keyword.word] = []
            self.keyword_performance[keyword.word].append(performance_data)
        
        # 清理过期数据
        self._cleanup_old_data()
        
        # 分析趋势模式
        self._analyze_trend_patterns(keywords)
        
        # 如果启用自动调整，优化权重
        if self.auto_adjust:
            new_weights = self._optimize_weights()
            if new_weights != self.optimal_weights:
                logger.info(f"权重调整: {self.optimal_weights} -> {new_weights}")
                self.optimal_weights = new_weights
                self.weight_history.append({
                    'timestamp': current_time,
                    'weights': new_weights.copy(),
                    'reason': 'auto_optimization'
                })
        
        # 保存学习数据
        self._save_learning_data()
        
        return self.optimal_weights
    
    def _calculate_real_impact(self, keyword, news_items: List) -> float:
        """计算关键词的真实影响力"""
        # 基于新闻排名和数量计算真实影响
        related_news = [item for item in news_items if keyword.word in item.title]
        
        if not related_news:
            return 0.0
        
        # 计算加权影响分数
        impact_score = 0.0
        for news in related_news:
            # 排名越靠前影响越大
            rank_score = max(0, 21 - news.rank) / 20.0
            impact_score += rank_score
        
        # 考虑出现频次的影响
        frequency_bonus = min(1.0, len(related_news) / 10.0)
        
        return impact_score * (1 + frequency_bonus)
    
    def _cleanup_old_data(self):
        """清理过期的学习数据"""
        cutoff_time = datetime.now() - timedelta(days=self.history_days)
        
        for keyword in list(self.keyword_performance.keys()):
            # 过滤掉过期的记录
            self.keyword_performance[keyword] = [
                record for record in self.keyword_performance[keyword]
                if record['timestamp'] > cutoff_time
            ]
            
            # 如果没有有效记录，删除该关键词
            if not self.keyword_performance[keyword]:
                del self.keyword_performance[keyword]
    
    def _analyze_trend_patterns(self, keywords: List):
        """分析趋势模式"""
        current_time = datetime.now()
        
        # 按时间段分析关键词出现模式
        for keyword in keywords:
            pattern_data = {
                'timestamp': current_time,
                'hour': current_time.hour,
                'weekday': current_time.weekday(),
                'importance': keyword.importance,
                'trend_score': keyword.trend_score
            }
            # 确保关键词在字典中存在
            if keyword.word not in self.trend_patterns:
                self.trend_patterns[keyword.word] = []
            self.trend_patterns[keyword.word].append(pattern_data)
            
            # 只保留最近的模式数据
            if len(self.trend_patterns[keyword.word]) > 100:
                self.trend_patterns[keyword.word] = self.trend_patterns[keyword.word][-50:]
    
    def _optimize_weights(self) -> Dict:
        """基于学习数据优化权重"""
        if len(self.keyword_performance) < 10:  # 数据不足，不调整
            return self.optimal_weights
        
        # 分析各个因子的效果
        performance_analysis = self._analyze_factor_performance()
        
        # 基于分析结果调整权重
        new_weights = self._calculate_optimal_weights(performance_analysis)
        
        return new_weights
    
    def _analyze_factor_performance(self) -> Dict:
        """分析各因子的表现"""
        frequency_effectiveness = []
        trend_effectiveness = []
        sentiment_effectiveness = []
        
        for keyword, records in self.keyword_performance.items():
            if len(records) >= 3:  # 至少需要3次记录
                # 计算各因子与真实影响的相关性
                for record in records[-10:]:  # 分析最近10次记录
                    real_impact = record['real_impact']
                    
                    if real_impact > 0:  # 只分析有真实影响的记录
                        freq_score = record['frequency'] / max(1, record['frequency'])
                        trend_score = record['trend_score']
                        sentiment_score = abs(record['sentiment_score'])
                        
                        frequency_effectiveness.append((freq_score, real_impact))
                        trend_effectiveness.append((trend_score, real_impact))
                        sentiment_effectiveness.append((sentiment_score, real_impact))
        
        # 计算相关性得分
        freq_correlation = self._calculate_correlation(frequency_effectiveness)
        trend_correlation = self._calculate_correlation(trend_effectiveness)
        sentiment_correlation = self._calculate_correlation(sentiment_effectiveness)
        
        return {
            'frequency': freq_correlation,
            'trend': trend_correlation,
            'sentiment': sentiment_correlation
        }
    
    def _calculate_correlation(self, data_pairs: List[Tuple[float, float]]) -> float:
        """计算简单的相关性系数"""
        if len(data_pairs) < 5:
            return 0.5  # 数据不足，返回中性值
        
        # 简化的皮尔逊相关系数
        x_values = [pair[0] for pair in data_pairs]
        y_values = [pair[1] for pair in data_pairs]
        
        if not x_values or not y_values:
            return 0.5
        
        x_mean = sum(x_values) / len(x_values)
        y_mean = sum(y_values) / len(y_values)
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
        x_variance = sum((x - x_mean) ** 2 for x in x_values)
        y_variance = sum((y - y_mean) ** 2 for y in y_values)
        
        if x_variance == 0 or y_variance == 0:
            return 0.5
        
        correlation = numerator / math.sqrt(x_variance * y_variance)
        
        # 归一化到0-1范围
        return (correlation + 1) / 2
    
    def _calculate_optimal_weights(self, performance: Dict) -> Dict:
        """根据性能分析计算最优权重"""
        current_weights = self.optimal_weights.copy()
        
        # 基于相关性调整权重
        freq_perf = performance['frequency']
        trend_perf = performance['trend']
        sentiment_perf = performance['sentiment']
        
        # 总权重必须为1
        total_performance = freq_perf + trend_perf + sentiment_perf
        
        if total_performance > 0:
            # 基于性能按比例分配权重，但限制变化幅度
            target_freq_weight = freq_perf / total_performance
            target_trend_weight = trend_perf / total_performance
            target_sentiment_weight = sentiment_perf / total_performance
            
            # 平滑调整，避免剧烈变化
            adjustment_rate = 0.1  # 调整速度
            
            new_freq_weight = current_weights['frequency_weight'] + \
                            (target_freq_weight - current_weights['frequency_weight']) * adjustment_rate
            new_trend_weight = current_weights['trend_weight'] + \
                             (target_trend_weight - current_weights['trend_weight']) * adjustment_rate
            new_sentiment_weight = current_weights['sentiment_weight'] + \
                                 (target_sentiment_weight - current_weights['sentiment_weight']) * adjustment_rate
            
            # 确保权重在合理范围内
            new_freq_weight = max(0.1, min(0.7, new_freq_weight))
            new_trend_weight = max(0.1, min(0.7, new_trend_weight))
            new_sentiment_weight = max(0.05, min(0.4, new_sentiment_weight))
            
            # 重新归一化
            total = new_freq_weight + new_trend_weight + new_sentiment_weight
            new_freq_weight /= total
            new_trend_weight /= total
            new_sentiment_weight /= total
            
            return {
                'frequency_weight': round(new_freq_weight, 3),
                'trend_weight': round(new_trend_weight, 3),
                'sentiment_weight': round(new_sentiment_weight, 3)
            }
        
        return current_weights
    
    def get_keyword_insights(self, keyword: str) -> Dict:
        """获取特定关键词的洞察"""
        if keyword not in self.keyword_performance:
            return {}
        
        records = self.keyword_performance[keyword]
        if not records:
            return {}
        
        # 计算统计信息
        importance_scores = [r['importance'] for r in records]
        trend_scores = [r['trend_score'] for r in records]
        
        insights = {
            'total_appearances': len(records),
            'avg_importance': sum(importance_scores) / len(importance_scores),
            'max_importance': max(importance_scores),
            'avg_trend_score': sum(trend_scores) / len(trend_scores),
            'first_seen': min(r['timestamp'] for r in records).isoformat(),
            'last_seen': max(r['timestamp'] for r in records).isoformat(),
            'trend_direction': self._analyze_trend_direction(records)
        }
        
        return insights
    
    def _analyze_trend_direction(self, records: List[Dict]) -> str:
        """分析关键词的趋势方向"""
        if len(records) < 3:
            return 'insufficient_data'
        
        recent_records = sorted(records, key=lambda x: x['timestamp'])[-5:]
        importance_trend = [r['importance'] for r in recent_records]
        
        # 简单的趋势分析
        if len(importance_trend) >= 3:
            early_avg = sum(importance_trend[:2]) / 2
            late_avg = sum(importance_trend[-2:]) / 2
            
            if late_avg > early_avg * 1.1:
                return 'rising'
            elif late_avg < early_avg * 0.9:
                return 'falling'
            else:
                return 'stable'
        
        return 'unknown'
    
    def generate_learning_report(self) -> Dict:
        """生成学习报告"""
        report = {
            'learning_status': {
                'enabled': self.enabled,
                'total_keywords_learned': len(self.keyword_performance),
                'weight_adjustments': len(self.weight_history),
                'current_weights': self.optimal_weights
            },
            'top_keywords': [],
            'weight_evolution': list(self.weight_history)[-10:],  # 最近10次调整
            'insights': {
                'most_stable_keywords': [],
                'trending_up_keywords': [],
                'trending_down_keywords': []
            }
        }
        
        # 分析表现最佳的关键词
        keyword_scores = []
        for keyword, records in self.keyword_performance.items():
            if records:
                avg_importance = sum(r['importance'] for r in records) / len(records)
                keyword_scores.append((keyword, avg_importance, len(records)))
        
        keyword_scores.sort(key=lambda x: x[1], reverse=True)
        report['top_keywords'] = [
            {'keyword': k[0], 'avg_importance': k[1], 'appearances': k[2]}
            for k in keyword_scores[:10]
        ]
        
        # 分析趋势
        for keyword in list(self.keyword_performance.keys())[:20]:
            trend = self._analyze_trend_direction(self.keyword_performance[keyword])
            if trend == 'rising':
                report['insights']['trending_up_keywords'].append(keyword)
            elif trend == 'falling':
                report['insights']['trending_down_keywords'].append(keyword)
            elif trend == 'stable':
                report['insights']['most_stable_keywords'].append(keyword)
        
        return report