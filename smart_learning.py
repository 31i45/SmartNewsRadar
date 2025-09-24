"""
SmartLearning - 自适应学习系统
让AI系统根据新闻热度变化自动调整和优化
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import deque
import statistics

logger = logging.getLogger(__name__)


class SmartLearningEngine:
    """极简设计的自适应学习引擎"""
    
    # 统一配置模型 - 所有配置集中在一处
    CONFIG = {
        'enabled': True,
        'history_days': 7,
        'auto_adjust': True,
        'weights': {'frequency': 0.4, 'trend': 0.4, 'sentiment': 0.2},
        # 内部配置常量
        'min_records': 3,
        'max_records': 10,
        'trend_thresholds': {'up': 1.15, 'down': 0.85},
        'keyword_history_limit': 50,
        'max_status_updates': 10
    }
    
    # 状态机 - 统一状态管理
    class State:
        INITIALIZED = 'initialized'  # 初始状态
        READY = 'ready'              # 数据加载完成，准备就绪
        ERROR = 'error'              # 出错状态
    
    def __init__(self, config: Dict[str, Any] = None):
        # 配置初始化 - 智能合并默认配置与用户配置
        self._config = self._merge_configs(config or {})
        
        # 核心数据结构 - 统一的数据模型
        self._data_dir = Path('learning_data')
        self._learning_data = {
            'keywords': {},  # 关键词历史记录（整合KeywordAnalyzer的keyword_history）
            'weight_history': deque(maxlen=50),  # 权重调整历史
            'weights': self._config['weights'].copy()  # 当前权重
        }
        
        # 状态管理 - 使用状态机模式
        self._state = self.State.INITIALIZED
        
        # 用户体验: 添加状态更新系统
        self._status_updates = []
        self._add_status_update("引擎已初始化")
        
        # 延迟初始化
        self._lazy_initialize()
    
    def _lazy_initialize(self) -> None:
        """延迟初始化 - 确保必要的目录存在"""
        if self._state != self.State.INITIALIZED or not self._config['enabled']:
            return
        
        try:
            self._data_dir.mkdir(exist_ok=True)
            self._state = self.State.INITIALIZED
            self._add_status_update("数据目录已准备就绪")
        except OSError as e:
            logger.error(f"无法创建数据目录: {e}")
            self._config['enabled'] = False
            self._state = self.State.ERROR
            self._add_status_update(f"初始化失败: 无法创建数据目录")
    
    def _add_status_update(self, message: str) -> None:
        """添加状态更新 - 用于用户体验反馈"""
        self._status_updates.append({
            'timestamp': datetime.now().isoformat(),
            'message': message
        })
        # 保持最近状态更新数量
        if len(self._status_updates) > self._config['max_status_updates']:
            self._status_updates.pop(0)
    
    def _merge_configs(self, user_config: Dict[str, Any]) -> Dict[str, Any]:
        """智能合并默认配置和用户配置"""
        merged = self.CONFIG.copy()
        
        # 合并用户提供的配置
        if 'weights' in user_config:
            merged['weights'].update(user_config['weights'])
            user_config.pop('weights')
        
        merged.update(user_config)
        return merged
    
    @property
    def optimal_weights(self) -> Dict[str, float]:
        """获取最优权重 - 直观的属性访问"""
        self._lazy_load_data()
        # 转换键名格式以匹配calculate_importance方法的期望
        return {
            'frequency_weight': self._learning_data['weights']['frequency'],
            'trend_weight': self._learning_data['weights']['trend'],
            'sentiment_weight': self._learning_data['weights']['sentiment']
        }
    
    def _lazy_load_data(self) -> None:
        """延迟加载数据 - 只在需要时执行"""
        if self._state == self.State.READY or not self._config['enabled']:
            return
            
        try:
            data_file = self._data_dir / 'learning_data.json'
            if data_file.exists():
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._restore_data(data)
                self._add_status_update(f"成功加载历史数据: {len(self._learning_data['keywords'])} 个关键词")
            else:
                self._add_status_update("未发现历史数据，从零开始")
            self._state = self.State.READY
        except Exception as e:
            error_type = type(e).__name__
            logger.warning(f"加载数据时发生{error_type}: {e}")
            self._add_status_update(f"加载历史数据时发生{error_type}，使用默认配置")
            self._state = self.State.READY  # 即使出错，也尝试继续运行
    
    def _restore_data(self, data: Dict) -> None:
        """统一恢复所有数据 - 整合之前分散的恢复逻辑"""
        # 恢复关键词数据
        for word, records in data.get('keywords', {}).items():
            try:
                # 转换时间戳并限制历史记录数量
                deque_records = deque(maxlen=self._config['keyword_history_limit'])
                for record in records:
                    if 'ts' in record:
                        record['ts'] = datetime.fromisoformat(record['ts'])
                    deque_records.append(record)
                self._learning_data['keywords'][word] = deque_records
            except Exception:
                # 忽略单个关键词的错误，继续处理其他关键词
                continue
        
        # 恢复权重数据
        if 'weights' in data:
            self._learning_data['weights'].update(data['weights'])
    
    def _save_data(self) -> None:
        """保存数据 - 精简存储格式"""
        if not self._config['enabled'] or self._state == self.State.ERROR:
            return
            
        try:
            # 准备数据 - 只保存必要信息
            data = {
                'keywords': {},
                'weights': self._learning_data['weights'],
                'updated_at': datetime.now().isoformat()
            }
            
            # 转换每个关键词的记录
            for word, records in self._learning_data['keywords'].items():
                data['keywords'][word] = self._serialize_records(records)
            
            # 保存主数据文件
            with open(self._data_dir / 'learning_data.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 保存摘要信息便于监控
            self._save_summary(data)
        except IOError as e:
            logger.error(f"保存数据文件失败: {e}")
    
    def _serialize_records(self, records: deque) -> List[Dict]:
        """序列化记录，确保datetime对象被正确处理"""
        serializable_records = []
        for record in records:
            # 创建记录副本以避免修改原始数据
            serializable_record = record.copy()
            # 将datetime对象转换为ISO格式字符串
            if 'ts' in serializable_record and isinstance(serializable_record['ts'], datetime):
                serializable_record['ts'] = serializable_record['ts'].isoformat()
            serializable_records.append(serializable_record)
        return serializable_records
    
    def _save_summary(self, data: Dict) -> None:
        """保存摘要信息"""
        try:
            summary = {
                'keywords_count': len(self._learning_data['keywords']),
                'weights_adjusted': len(self._learning_data['weight_history']),
                'current_weights': self._learning_data['weights'],
                'updated_at': data['updated_at']
            }
            with open(self._data_dir / 'learning_summary.json', 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
        except Exception:
            # 摘要信息不是关键数据，忽略错误
            pass
    
    def learn(self, keywords: List[Any], news_items: List[Any]) -> Dict[str, float]:
        """核心学习方法 - 专注于学习和适应"""
        if not self._config['enabled']:
            return self._learning_data['weights'].copy()
        
        if not keywords:
            self._add_status_update("没有收到关键词数据，跳过学习")
            return self._learning_data['weights'].copy()
            
        # 确保数据已加载
        self._lazy_load_data()
        
        current_time = datetime.now()
        
        # 用户体验: 添加学习开始反馈
        self._add_status_update(f"开始学习 {len(keywords)} 个关键词")
        
        # 处理每个关键词
        processed_count = 0
        for keyword in keywords:
            if self._process_keyword(keyword, news_items, current_time):
                processed_count += 1
        
        # 用户体验: 添加学习进度反馈
        self._add_status_update(f"成功处理 {processed_count}/{len(keywords)} 个关键词")
        
        # 清理过期数据
        self._cleanup_old_data()
        
        # 智能优化权重
        if self._config['auto_adjust'] and len(self._learning_data['keywords']) >= 10:
            self._optimize_weights_if_needed(current_time)
        
        # 保存学习结果
        self._save_data()
        
        return self._learning_data['weights'].copy()
    
    def _process_keyword(self, keyword: Any, news_items: List[Any], timestamp: datetime) -> bool:
        """处理单个关键词 - 提取并存储关键信息"""
        try:
            if not (word := getattr(keyword, 'word', '')):
                return False
                
            # 计算真实影响力
            impact = self._calculate_impact(word, news_items)
            
            # 存储核心数据
            if word not in self._learning_data['keywords']:
                self._learning_data['keywords'][word] = deque(maxlen=self._config['keyword_history_limit'])
                self._add_status_update(f"发现新关键词: {word}")
                
            self._learning_data['keywords'][word].append({
                'ts': timestamp,
                'importance': keyword.importance,
                'frequency': keyword.frequency,
                'trend': keyword.trend_score,
                'sentiment': getattr(keyword, 'sentiment_score', 0.0),
                'impact': impact
            })
            return True
        except Exception as e:
            logger.debug(f"处理关键词时发生轻微错误: {e}")
            return False
    
    def _calculate_impact(self, word: str, news_items: List[Any]) -> float:
        """计算关键词真实影响力 - 高效算法"""
        impact = 0.0
        count = 0
        
        for news in news_items:
            if word in getattr(news, 'title', ''):
                count += 1
                # 使用简洁的计算方式
                impact += max(0, 21 - getattr(news, 'rank', 20)) / 20.0
        
        # 频率奖励因子
        bonus = min(1.0, count / 10.0)
        return impact * (1 + bonus) if count > 0 else 0.0
    
    def _cleanup_old_data(self) -> None:
        """清理过期数据 - 保持轻量"""
        cutoff = datetime.now() - timedelta(days=self._config['history_days'])
        
        # 使用列表复制避免迭代时修改
        for word in list(self._learning_data['keywords'].keys()):
            # 移除过期记录
            while self._learning_data['keywords'][word] and self._learning_data['keywords'][word][0].get('ts', datetime.min) <= cutoff:
                self._learning_data['keywords'][word].popleft()
            
            # 移除空关键词
            if not self._learning_data['keywords'][word]:
                del self._learning_data['keywords'][word]
    
    def _optimize_weights_if_needed(self, timestamp: datetime) -> None:
        """优化权重 - 在必要时进行调整"""
        new_weights = self._calculate_optimal_weights()
        
        if new_weights and self._should_update_weights(new_weights):
            old_weights = self._learning_data['weights'].copy()
            self._learning_data['weights'] = new_weights
            self._learning_data['weight_history'].append({
                'time': timestamp,
                'weights': new_weights.copy()
            })
            # 用户体验: 添加权重调整反馈
            self._add_status_update(f"智能优化权重: 频率={old_weights['frequency']:.2f}→{new_weights['frequency']:.2f}, 趋势={old_weights['trend']:.2f}→{new_weights['trend']:.2f}")
    
    def _calculate_optimal_weights(self) -> Optional[Dict[str, float]]:
        """计算最优权重 - 既智能又不过于复杂"""
        # 收集特征数据并计算性能得分
        performance = self._evaluate_factors()
        
        # 基于性能分配权重
        total = sum(performance.values())
        if total <= 0:
            return None
            
        new_weights = {k: v / total for k, v in performance.items()}
        
        # 边界检查和归一化
        return self._normalize_weights(new_weights)
    
    def _evaluate_factors(self) -> Dict[str, float]:
        """整合特征数据收集和性能评估 - 简化调用链"""
        factors = {'frequency': [], 'trend': [], 'sentiment': []}
        
        # 收集特征数据
        for records in self._learning_data['keywords'].values():
            if len(records) < self._config['min_records']:
                continue
                
            # 获取最近记录
            recent = list(records)[-self._config['max_records']:]
            for record in recent:
                if record.get('impact', 0) <= 0:
                    continue
                    
                # 收集特征数据
                factors['frequency'].append((record['frequency'], record['impact']))
                factors['trend'].append((record['trend'], record['impact']))
                factors['sentiment'].append((abs(record['sentiment']), record['impact']))
        
        # 计算性能得分
        performance = {}
        for name, data in factors.items():
            if len(data) < 5:
                performance[name] = 0.5
                continue
                
            try:
                # 使用简单但有效的相关性计算
                corr = self._simple_correlation(data)
                performance[name] = (corr + 1) / 2
            except Exception:
                performance[name] = 0.5
        
        return performance
    
    @staticmethod
    def _simple_correlation(data):
        """简单相关系数计算，避免引入复杂依赖"""
        x_values, y_values = zip(*data)
        n = len(x_values)
        
        # 计算均值
        mean_x = sum(x_values) / n
        mean_y = sum(y_values) / n
        
        # 计算协方差和标准差
        covariance = sum((x - mean_x) * (y - mean_y) for x, y in data) / n
        std_x = (sum((x - mean_x) ** 2 for x in x_values) / n) ** 0.5
        std_y = (sum((y - mean_y) ** 2 for y in y_values) / n) ** 0.5
        
        # 避免除以零
        if std_x * std_y == 0:
            return 0
            
        return covariance / (std_x * std_y)
    
    def _should_update_weights(self, new_weights: Dict[str, float]) -> bool:
        """判断是否应该更新权重"""
        # 只有当权重变化超过阈值时才更新
        return any(abs(new_weights[k] - self._learning_data['weights'][k]) >= 0.01 for k in self._learning_data['weights'])
    
    def _normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """归一化权重并应用边界限制"""
        # 应用边界限制
        normalized = {
            'frequency': max(0.1, min(0.7, weights['frequency'])),
            'trend': max(0.1, min(0.7, weights['trend'])),
            'sentiment': max(0.05, min(0.4, weights['sentiment']))
        }
        
        # 确保权重和为1
        total_weight = sum(normalized.values())
        if total_weight > 0:
            normalized = {k: round(v / total_weight, 3) for k, v in normalized.items()}
            
        return normalized
    
    def get_keyword_insights(self, keyword: str) -> Dict[str, Any]:
        """获取关键词洞察 - 保持核心功能"""
        self._lazy_load_data()
        
        if keyword not in self._learning_data['keywords'] or not self._learning_data['keywords'][keyword]:
            return {}
            
        records = list(self._learning_data['keywords'][keyword])
        try:
            return self._extract_keyword_insights(records)
        except Exception as e:
            logger.debug(f"计算关键词洞察失败: {e}")
            return {}
    
    def _extract_keyword_insights(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """提取关键词洞察"""
        # 提取关键指标
        importance_values = [r['importance'] for r in records]
        trend_values = [r['trend'] for r in records]
        timestamps = [r['ts'] for r in records]
        
        insights = {
            'appearances': len(records),
            'avg_importance': statistics.mean(importance_values),
            'max_importance': max(importance_values),
            'min_importance': min(importance_values),
            'avg_trend': statistics.mean(trend_values),
            'trend_direction': self._analyze_trend(records),
            'first_seen': min(timestamps).isoformat(),
            'last_seen': max(timestamps).isoformat()
        }
        
        # 仅在数据足够时添加额外统计
        if len(importance_values) > 1:
            insights.update({
                'importance_std': statistics.stdev(importance_values),
                'trend_std': statistics.stdev(trend_values)
            })
            
        return insights
    
    def _analyze_trend(self, records: List[Dict[str, Any]]) -> str:
        """分析趋势方向 - 简化算法"""
        if len(records) < self._config['min_records']:
            return 'insufficient'
            
        # 获取最近记录的重要性趋势
        recent = sorted(records, key=lambda x: x['ts'])[-5:]
        importance = [r['importance'] for r in recent]
        
        if len(importance) >= 3:
            # 计算简单移动平均变化率
            early_avg = sum(importance[:2]) / 2
            late_avg = sum(importance[-2:]) / 2
            
            # 避免除以零
            if early_avg <= 0:
                return 'unknown'
                
            ratio = late_avg / early_avg
            thresholds = self._config['trend_thresholds']
            if ratio > thresholds['up']:
                return 'rising'
            elif ratio < thresholds['down']:
                return 'falling'
            else:
                return 'stable'
        
        return 'unknown'
    
    def generate_report(self) -> Dict[str, Any]:
        """生成学习报告 - 保留核心洞察"""
        self._lazy_load_data()
        
        report = {
            'status': {
                'enabled': self._config['enabled'],
                'state': self._state,
                'keywords_count': len(self._learning_data['keywords']),
                'weights_adjusted': len(self._learning_data['weight_history']),
                'current_weights': self._learning_data['weights'],
                'recent_status': self._status_updates  # 用户体验: 添加最近状态更新
            },
            'top_keywords': [],
            'insights': {
                'trending_up': [],
                'trending_down': [],
                'stable': [],
                'efficiency': 'high' if len(self._learning_data['weight_history']) > 0 else 'initial'
            }
        }
        
        # 分析表现最佳的关键词
        report['top_keywords'] = self._get_top_keywords()
        
        # 分析趋势分类
        self._categorize_keywords_by_trend(report['insights'])
        
        # 评估学习效率
        if len(self._learning_data['weight_history']) > 3:
            efficiency = self._evaluate_learning_efficiency()
            report['insights']['efficiency'] = efficiency
            # 用户体验: 根据效率等级添加建议
            if efficiency == 'stable':
                report['insights']['recommendation'] = "当前配置已稳定，建议保持监控"
            elif efficiency == 'converging':
                report['insights']['recommendation'] = "学习系统正在收敛，即将达到最优状态"
            else:
                report['insights']['recommendation'] = "系统正在积极适应新数据，请继续观察"
            
        return report
    
    def _get_top_keywords(self) -> List[Dict[str, Any]]:
        """获取表现最佳的关键词"""
        keyword_scores = []
        for word, records in self._learning_data['keywords'].items():
            if records:
                avg_importance = statistics.mean([r['importance'] for r in records])
                keyword_scores.append((word, avg_importance, len(records)))
        
        # 排序并取前10
        return [
            {'keyword': k[0], 'avg_importance': k[1], 'appearances': k[2]}
            for k in sorted(keyword_scores, key=lambda x: x[1], reverse=True)[:10]
        ]
    
    def _categorize_keywords_by_trend(self, insights: Dict) -> None:
        """按趋势分类关键词"""
        for word, records in self._learning_data['keywords'].items():
            trend = self._analyze_trend(list(records))
            if trend == 'rising':
                insights['trending_up'].append(word)
            elif trend == 'falling':
                insights['trending_down'].append(word)
            elif trend == 'stable':
                insights['stable'].append(word)
    
    def _evaluate_learning_efficiency(self) -> str:
        """评估学习效率"""
        # 计算权重稳定性指标
        recent_weights = list(self._learning_data['weight_history'])[-3:]
        stability = 0
        for i in range(len(recent_weights) - 1):
            w1, w2 = recent_weights[i]['weights'], recent_weights[i+1]['weights']
            stability += abs(w1['frequency'] - w2['frequency']) + \
                        abs(w1['trend'] - w2['trend']) + \
                        abs(w1['sentiment'] - w2['sentiment'])
        stability /= (len(recent_weights) - 1)
        
        # 评估效率等级
        if stability < 0.02:
            return 'stable'
        elif stability < 0.05:
            return 'converging'
        else:
            return 'adapting'
    
    # 兼容性方法 - 为了向后兼容而保留
    def learn_from_keywords(self, keywords: List[Any], news_items: List[Any]) -> Dict[str, float]:
        """从关键词列表中学习 - 为SmartNewsRadar提供的便捷接口"""
        return self.learn(keywords, news_items)

    def learn_new(self, keywords, news_items):
        """学习新的关键词和新闻数据"""
        return self.learn(keywords, news_items)