# -*- coding: utf-8 -*-
"""
智能新闻雷达 - 展示层模块
遵循乔布斯设计哲学：简洁、优雅、直观
"""
import os
import json
import datetime
import logging
from typing import Dict, List, Any, Optional
import matplotlib.pyplot as plt
import matplotlib

# 设置matplotlib后端为非交互式
matplotlib.use('Agg')
# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'WenQuanYi Micro Hei', 'Heiti TC']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

logger = logging.getLogger(__name__)

class SmartPresenter:
    """智能展示层，负责以多种形式呈现分析结果"""
    
    def __init__(self, output_dir: str = "output", config: Optional[Dict] = None):
        """初始化展示层"""
        self.output_dir = os.path.join(os.path.dirname(__file__), output_dir)
        self._cache_dir = os.path.join(self.output_dir, '.cache')
        self.config = config or {}
        
        # 创建必要的目录，但不在这里清空
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self._cache_dir, exist_ok=True)
        
        # 分隔线定义
        self.SEPARATOR = "—" * 60  # 使用em dash，更优雅
    
    def _clear_output_dir(self) -> None:
        """清空output目录"""
        try:
            if os.path.exists(self.output_dir):
                for filename in os.listdir(self.output_dir):
                    filepath = os.path.join(self.output_dir, filename)
                    if os.path.isfile(filepath):
                        os.remove(filepath)
                    elif os.path.isdir(filepath) and filename == '.cache':
                        # 清空.cache目录但保留目录本身
                        for cache_file in os.listdir(filepath):
                            os.remove(os.path.join(filepath, cache_file))
            logger.info("已清空output目录")
        except Exception as e:
            logger.error(f"清空output目录时出错: {e}")
    
    def present(self, data: Dict, format_type: str = "console") -> str:
        """以指定格式呈现分析结果"""
        logger.info(f"以{format_type}格式呈现分析结果")
        
        try:
            if format_type == "html":
                return self._generate_html_report(data)
            elif format_type == "json":
                return self._generate_json_report(data)
            elif format_type == "console":
                return self._generate_console_output(data)
            else:
                raise ValueError(f"不支持的输出格式: {format_type}")
        except Exception as e:
            error_msg = f"呈现分析结果时出错: {str(e)[:100]}"
            logger.error(error_msg)
            
            # 降级到控制台输出
            print(f"\n⚠️ {error_msg}\n已自动降级到控制台输出模式")
            return self._generate_console_output(data)
            
    def _generate_console_output(self, data: Dict) -> str:
        """生成控制台输出格式的分析结果"""
        output = [
            "\n🎯 智能新闻雷达分析结果 🎯",
            self.SEPARATOR,
            f"分析时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"新闻总数: {data.get('total_news', 0)}",
            f"发现关键词: {len(data.get('keywords', []))}"
        ]
        
        # 输出热点关键词
        output.extend([
            "\n🎯 自动发现的热点关键词:",
            self.SEPARATOR
        ])
        
        # 输出前10个关键词
        for i, keyword in enumerate(data.get('keywords', [])[:10]):
            output.append(f"{i+1:2d}. {keyword['word']:<8} | 重要性: {keyword['importance']:.2f} | 出现: {keyword['frequency']}次")
        
        # 输出热门新闻摘要
        output.extend([
            self.SEPARATOR,
            "\n📰 热门新闻摘要:"
        ])
        
        # 输出前5条热门新闻
        for i, news in enumerate(data.get('news_summary', [])[:5]):
            output.append(f"{i+1}. {news['title']} ({news['source']})")
            
        # 添加AI学习统计部分
        if 'learning_stats' in data:
            learning_stats = data['learning_stats']
            output.extend([
                self.SEPARATOR,
                "\n🤖 AI学习统计:"
            ])
            output.append(f"  • 学习关键词数: {learning_stats.get('keywords_count', 0)}")
            output.append(f"  • 权重调整次数: {learning_stats.get('weights_adjusted', 0)}")
            output.append(f"  • 当前最优权重:")
            
            # 格式化权重输出
            weights = learning_stats.get('current_weights', {})
            for name, value in weights.items():
                output.append(f"    - {name}: {value:.3f}")
            
        output.append(self.SEPARATOR)
        
        result = "\n".join(output)
        print(result)  # 打印到控制台
        return result
    
    def _generate_json_report(self, data: Dict) -> str:
        """生成JSON格式报告"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"smart_radar_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        # 确保数据包含必要的字段
        report_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "total_news": data.get("total_news", 0),
            "total_keywords": len(data.get("keywords", [])),
            "keywords": data.get("keywords", []),
            "news_summary": data.get("news_summary", [])
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            logger.info(f"JSON报告已保存至: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"生成JSON报告失败: {e}")
            raise
            
    def _generate_html_report(self, data: Dict) -> str:
        """生成HTML格式报告"""
        # 导入HTML模板
        from html_template import generate_html_content
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"smart_radar_{timestamp}.html"
        filepath = os.path.join(self.output_dir, filename)
        
        # 创建图表
        chart_paths = []
        try:
            chart_paths = self._generate_charts(data)
        except Exception as e:
            logger.warning(f"生成图表失败: {e}")
            
        # 生成HTML内容
        html_content = generate_html_content(data, chart_paths)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"HTML报告已保存至: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"生成HTML报告失败: {e}")
            raise
            
    def _generate_charts(self, data: Dict) -> List[str]:
        """生成数据可视化图表"""
        chart_paths = []
        
        # 关键词重要性条形图
        keyword_chart = self._generate_keyword_chart(data)
        if keyword_chart:
            chart_paths.append(keyword_chart)
        
        # 趋势分析图
        trend_chart = self._generate_trend_chart(data)
        if trend_chart:
            chart_paths.append(trend_chart)
        
        return chart_paths
        
    def _generate_keyword_chart(self, data: Dict) -> str:
        """生成关键词重要性图表 - 极简主义风格"""
        keywords = data.get('keywords', [])[:10]  # 取前10个关键词
        
        if not keywords:
            return ""
            
        # 排序关键词，从高到低
        keywords_sorted = sorted(keywords, key=lambda x: x['importance'], reverse=True)
        words = [kw['word'] for kw in keywords_sorted]
        importances = [kw['importance'] for kw in keywords_sorted]
        
        # 使用乔布斯风格的极简设计
        plt.figure(figsize=(10, 6), facecolor='none')
        
        # 创建水平条形图，使用优雅的蓝色渐变效果
        bars = plt.barh(words, importances, height=0.6, color='#0071e3', alpha=0.8)
        
        # 添加轻微的阴影效果
        for bar in bars:
            bar.set_edgecolor('white')
            bar.set_linewidth(1)
        
        # 设置坐标轴，隐藏顶部和右侧边框
        ax = plt.gca()
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#e3e3e3')
        ax.spines['bottom'].set_color('#e3e3e3')
        
        # 设置坐标轴字体和刻度
        plt.xticks(fontsize=12, color='#86868b')
        plt.yticks(fontsize=13, color='#1d1d1f')
        
        # 隐藏Y轴刻度线
        ax.tick_params(axis='y', length=0)
        
        # 优化X轴范围，留出适当空间
        max_importance = max(importances) if importances else 1
        plt.xlim(0, max_importance * 1.1)
        
        # 添加极简风格的标题
        plt.title('热门关键词重要性分析', fontsize=16, color='#1d1d1f', fontweight='300', pad=20)
        
        # 美化布局
        plt.tight_layout(pad=2)
        
        chart_path = os.path.join(self._cache_dir, f"keyword_chart_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        # 保存为高质量图片，设置透明背景
        plt.savefig(chart_path, dpi=300, bbox_inches='tight', transparent=True)
        plt.close()
        
        return chart_path

    def _generate_trend_chart(self, data: Dict) -> str:
        """生成趋势分析图表 - 极简主义风格"""
        keywords = data.get('keywords', [])[:5]  # 取前5个关键词
        
        if not keywords:
            return ""
            
        # 使用乔布斯风格的极简设计
        plt.figure(figsize=(10, 6), facecolor='none')
        
        # 使用优雅的颜色方案
        colors = ['#0071e3', '#5856d6', '#af52de', '#ff2d55', '#ff9500']
        
        # 绘制趋势线
        for i, kw in enumerate(keywords):
            # 基于当前趋势分数创建模拟数据
            x = [1, 2, 3, 4, 5]
            base_importance = kw['importance'] * 0.8
            y = [base_importance + (kw['trend_score'] * i) for i in range(5)]
            
            # 绘制平滑的曲线
            plt.plot(x, y, marker='o', markersize=6, linewidth=2.5, color=colors[i], alpha=0.9, label=kw['word'])
            
            # 美化数据点
            plt.scatter(x, y, s=40, color=colors[i], alpha=0.8, edgecolors='white', linewidths=1)
        
        # 设置坐标轴，隐藏顶部和右侧边框
        ax = plt.gca()
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#e3e3e3')
        ax.spines['bottom'].set_color('#e3e3e3')
        
        # 设置坐标轴字体和刻度
        plt.xticks(fontsize=12, color='#86868b')
        plt.yticks(fontsize=12, color='#86868b')
        
        # 设置X轴标签，增加视觉直观性
        plt.xticks([1, 2, 3, 4, 5], ['第1日', '第2日', '第3日', '第4日', '第5日'])
        
        # 添加极简风格的标题
        plt.title('关键词趋势分析', fontsize=16, color='#1d1d1f', fontweight='300', pad=20)
        
        # 优化图例
        plt.legend(frameon=False, loc='upper left', fontsize=11)
        
        # 美化布局
        plt.tight_layout(pad=2)
        
        chart_path = os.path.join(self._cache_dir, f"trend_chart_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        # 保存为高质量图片，设置透明背景
        plt.savefig(chart_path, dpi=300, bbox_inches='tight', transparent=True)
        plt.close()
        
        return chart_path

# 工厂方法，用于快速创建和使用展示层
def create_presenter(output_dir: str = "output", config: Optional[Dict] = None) -> SmartPresenter:
    """创建展示层实例"""
    return SmartPresenter(output_dir, config)

# 全局变量，用于跟踪是否已清空目录
_output_dir_cleared = False

# 便捷函数：直接展示数据
def present_results(data: Dict, format_type: str = "console", config: Optional[Dict] = None, clear_dir: bool = True) -> str:
    """便捷函数：使用SmartPresenter呈现分析结果"""
    global _output_dir_cleared
    
    # 创建展示器
    presenter = create_presenter(config=config)
    
    # 只在需要且未清空过时清空目录
    if clear_dir and not _output_dir_cleared:
        presenter._clear_output_dir()
        _output_dir_cleared = True
    
    # 呈现结果
    return presenter.present(data, format_type)