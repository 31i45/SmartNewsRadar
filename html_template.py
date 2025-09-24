"""
HTML模板生成器
遵循乔布斯设计哲学的简洁、优雅、直观的HTML报告模板
"""
import datetime
from typing import Dict, List, Any, Optional
import os


def generate_html_content(data: Dict, chart_paths: List[str]) -> str:
    """生成HTML格式报告内容"""
    timestamp = data.get('timestamp', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    total_news = data.get('total_news', 0)
    keywords = data.get('keywords', [])
    news_summary = data.get('news_summary', [])
    
    # 生成关键词卡片HTML
    keyword_cards = []
    for keyword in keywords[:15]:  # 前15个关键词（简化数量）
        importance_percent = min(100, int(keyword['importance'] * 5))
        trend_class = "positive" if keyword['trend_score'] > 0.5 else "neutral" if keyword['trend_score'] > 0.3 else "negative"
        
        keyword_cards.append(f"""
        <div class="keyword-card">
            <div class="keyword-title">{keyword['word']}</div>
            <div class="keyword-stats">
                <div class="stat">
                    <div class="stat-value">{keyword['frequency']}</div>
                    <div class="stat-label">出现频率</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{keyword['importance']:.1f}</div>
                    <div class="stat-label">重要性</div>
                </div>
            </div>
            <div class="importance-bar">
                <div class="importance-fill" style="width: {importance_percent}%" data-value="{importance_percent}"></div>
            </div>
        </div>
        """)
    
    # 生成图表HTML
    charts_html = []
    for chart_path in chart_paths:
        if chart_path:
            chart_type = "关键词" if "keyword" in chart_path.lower() else "趋势"
            # 获取安全的文件名
            safe_filename = os.path.basename(chart_path).replace('"', '&quot;').replace("'", '&#39;')
            
            charts_html.append(f"""
            <div class="chart-container">
                <div class="chart-title">{chart_type}分析图表</div>
                <img src=".cache/{safe_filename}" alt="{chart_type}图表" class="chart-image" loading="lazy">
            </div>
            """)
    
    # 生成新闻摘要HTML
    news_items_html = []
    for i, news in enumerate(news_summary[:8]):  # 前8条新闻（简化数量）
        news_items_html.append(f"""
        <div class="news-item">
            <div class="news-rank">{i+1}</div>
            <div class="news-content">
                <div class="news-title">{news['title']}</div>
                <div class="news-source">{news['source']}</div>
            </div>
        </div>
        """)
    
    # 完整HTML模板 - 极简主义设计
    html_template = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>智能新闻雷达 - 热点分析报告</title>
    <style>
        /* 全局样式重置和基础设置 */
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        /* 明亮模式变量 */
        :root {{
            --bg-primary: #f5f5f7;
            --bg-secondary: #ffffff;
            --text-primary: #1d1d1f;
            --text-secondary: #86868b;
            --accent-color: #0071e3;
            --border-color: #e3e3e3;
            --shadow-light: rgba(0, 0, 0, 0.05);
        }}
        
        /* 暗黑模式支持 */
        @media (prefers-color-scheme: dark) {{
            :root {{
                --bg-primary: #121212;
                --bg-secondary: #1e1e1e;
                --text-primary: #f5f5f7;
                --text-secondary: #a1a1a6;
                --accent-color: #0a84ff;
                --border-color: #333333;
            }}
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            transition: background-color 0.3s ease, color 0.3s ease;
            padding-bottom: 40px;
        }}
        
        .container {{
            max-width: 1100px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding: 30px 0;
            background: var(--bg-secondary);
            border-radius: 12px;
            box-shadow: 0 2px 8px var(--shadow-light);
        }}
        
        .header h1 {{
            font-size: 2.2rem;
            font-weight: 300;
            margin-bottom: 8px;
            color: var(--text-primary);
            letter-spacing: -0.02em;
        }}
        
        .header .subtitle {{
            font-size: 1rem;
            color: var(--text-secondary);
            letter-spacing: 0.01em;
        }}
        
        .section {{
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 2px 8px var(--shadow-light);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        
        .section:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 12px var(--shadow-light);
        }}
        
        .section-title {{
            font-size: 1.4rem;
            font-weight: 600;
            margin-bottom: 20px;
            color: var(--text-primary);
            padding-bottom: 8px;
            border-bottom: 1px solid var(--border-color);
            letter-spacing: -0.01em;
        }}
        
        /* 关键词卡片 */
        .keywords-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
            gap: 15px;
        }}
        
        .keyword-card {{
            background: var(--bg-secondary);
            padding: 16px;
            border-radius: 10px;
            border-left: 3px solid var(--accent-color);
            box-shadow: 0 1px 3px var(--shadow-light);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        
        .keyword-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 4px 8px var(--shadow-light);
        }}
        
        .keyword-title {{
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 12px;
            color: var(--text-primary);
        }}
        
        .keyword-stats {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 12px;
        }}
        
        .stat {{
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--accent-color);
        }}
        
        .stat-label {{
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-top: 4px;
        }}
        
        .importance-bar {{
            height: 4px;
            background: var(--border-color);
            border-radius: 2px;
            overflow: hidden;
        }}
        
        .importance-fill {{
            height: 100%;
            background: linear-gradient(90deg, var(--accent-color) 0%, #5ac8fa 100%);
            border-radius: 2px;
            transition: width 1s ease-out;
        }}
        
        /* 图表样式 */
        .chart-container {{
            background: var(--bg-secondary);
            border-radius: 10px;
            padding: 16px;
            box-shadow: 0 2px 6px var(--shadow-light);
            margin-bottom: 20px;
        }}
        
        .chart-title {{
            font-size: 1rem;
            font-weight: 500;
            color: var(--text-secondary);
            margin-bottom: 12px;
            text-align: center;
        }}
        
        .chart-image {{
            width: 100%;
            border-radius: 8px;
            transition: transform 0.2s ease;
        }}
        
        .chart-image:hover {{
            transform: scale(1.01);
        }}
        
        /* 新闻样式 */
        .news-item {{
            display: flex;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid var(--border-color);
            transition: transform 0.2s ease;
        }}
        
        .news-item:hover {{
            transform: translateX(4px);
        }}
        
        .news-item:last-child {{
            border-bottom: none;
        }}
        
        .news-rank {{
            font-size: 1.3rem;
            font-weight: 700;
            color: var(--accent-color);
            margin-right: 16px;
            min-width: 25px;
            text-align: center;
        }}
        
        .news-content {{
            flex: 1;
        }}
        
        .news-title {{
            font-size: 0.95rem;
            font-weight: 500;
            color: var(--text-primary);
            margin-bottom: 4px;
            transition: color 0.2s ease;
        }}
        
        .news-item:hover .news-title {{
            color: var(--accent-color);
        }}
        
        .news-source {{
            font-size: 0.8rem;
            color: var(--text-secondary);
        }}
        
        .timestamp {{
            text-align: center;
            margin-top: 30px;
            color: var(--text-secondary);
            font-size: 0.85rem;
        }}
        
        /* 响应式设计 */
        @media (max-width: 768px) {{
            .container {{
                padding: 10px;
            }}
            
            .header h1 {{
                font-size: 1.8rem;
            }}
            
            .keywords-grid {{
                grid-template-columns: 1fr;
            }}
            
            .section {{
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>智能新闻雷达</h1>
            <div class="subtitle">热点新闻与关键词分析</div>
        </div>
        
        <div class="section">
            <div class="section-title">关键词分析</div>
            <div class="keywords-grid">
                {''.join(keyword_cards)}
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">热门新闻</div>
            <div class="news-section">
                {''.join(news_items_html)}
            </div>
        </div>
        
        {''.join(charts_html) if charts_html else ''}
        
        <div class="timestamp">
            <div>更新时间: {timestamp}</div>
            <div style="margin-top: 8px;">
                分析了 {total_news} 条新闻，发现 {len(keywords)} 个热点关键词
            </div>
        </div>
    </div>
    
    <script>
        // 页面加载动画和交互增强
        document.addEventListener('DOMContentLoaded', function() {{
            // 为重要性条添加动画效果
            const bars = document.querySelectorAll('.importance-fill');
            bars.forEach(bar => {{
                const width = bar.getAttribute('data-value') + '%';
                bar.style.width = '0';
                setTimeout(() => {{
                    bar.style.width = width;
                }}, 300 + Math.random() * 300); // 随机延迟，创造错落有致的效果
            }});
            
            // 添加页面滚动平滑效果
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
                anchor.addEventListener('click', function (e) {{
                    e.preventDefault();
                    document.querySelector(this.getAttribute('href')).scrollIntoView({{
                        behavior: 'smooth'
                    }});
                }});
            }});
            
            // 为图表和卡片添加渐进式加载动画
            const fadeElements = document.querySelectorAll('.keyword-card, .chart-container, .news-item');
            fadeElements.forEach((element, index) => {{
                element.style.opacity = '0';
                element.style.transform = 'translateY(10px)';
                element.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                
                setTimeout(() => {{
                    element.style.opacity = '1';
                    element.style.transform = 'translateY(0)';
                }}, 100 + index * 30);
            }});
        }});
    </script>
</body>
</html>
"""
    
    return html_template