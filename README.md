# SmartNewsRadar - 智能新闻关键词发现系统

> "简洁就是终极的复杂" - 基于极简主义哲学的AI驱动新闻分析系统

## 📋 项目概述

SmartNewsRadar是一个强大的智能新闻关键词发现系统，能够自动从海量新闻数据中识别热点关键词，无需预设任何关键词。系统通过AI驱动的分析算法，结合多源数据获取，实现了真正的智能趋势分析和热点发现。
受到`https://github.com/sansan0/TrendRadar`的启发，专注真实新闻世界的关键词的智能发现而非新闻消息推荐。

## ✨ 核心特性

### 🤖 真正的AI驱动
- **自动关键词发现**：无需预设任何关键词，系统自动从新闻中发现热点
- **智能趋势分析**：基于新闻排名、出现频次、时间分布进行深度分析
- **情感理解**：简单但有效的情感分析，识别正面/负面趋势
- **自适应学习**：系统会根据历史数据自动优化分析权重

### 🌐 多平台覆盖
- **NewNow API源**：38个主流平台（微博、抖音、知乎、B站等）
- **RSS订阅源**：27个权威媒体（新浪、网易、财新、36氪等）
- **网页抓取源**：18个备用数据源（人民日报、新华网、央视新闻等）
- **支持轻松扩展更多平台**

### 🔄 多源备份机制
- 支持同时从API、RSS和网页抓取三种方式获取数据
- 单平台失败不影响整体分析
- 自适应选择最优数据源

### 📱 智能通知
- **多平台支持**：飞书、企业微信、钉钉、Telegram
- 优雅的消息格式设计
- 基于重要性的智能推送
- 支持批量发送和错误恢复

### 📊 精美报告
- **响应式HTML报告**：完美适配PC和移动端
- **JSON数据格式**：便于二次开发和数据分析
- **学习报告**：展示AI学习进度和权重优化过程

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements_enhanced.txt
```

### 2. 配置系统

系统默认使用`smart_config.yaml`作为配置文件，已包含完整的38个NewNow API数据源、27个RSS订阅源和18个网页抓取源。

### 3. 运行主程序

```bash
python smart_radar.py
```

### 4. 查看实时结果

```bash
# 控制台直接显示TOP10热点关键词
🎯 自动发现的热点关键词:
 1. 始祖鸟          | 重要性:  7.48 | 出现: 19次 | 趋势: 0.29
 2. 烟花           | 重要性:  5.59 | 出现: 14次 | 趋势: 0.45
 3. 蔡国强          | 重要性:  4.50 | 出现: 11次 | 趋势: 0.63
```

### 5. 查看详细报告

程序会在`output`目录下自动生成以下报告文件：
- `output/smart_radar_YYYYMMDD_HHMMSS.html`：可视化报告
- `output/smart_radar_YYYYMMDD_HHMMSS.json`：数据报告
- `output/learning_report_YYYYMMDD_HHMMSS.json`：AI学习报告

## 🔧 配置说明

### 主要配置项

`smart_config.yaml`包含以下主要配置部分：

```yaml
# 数据获取配置
data_sources:
  # 启用增强模式（多源获取）
  enhanced_mode: true
  
  # 数据源超时设置（秒）
  timeout: 30
  
  # 并发请求数限制
  concurrent_limit: 20
  
  # NewNow API源配置
  newsnow_api:
    enabled: true
    sources: # 包含38个数据源
    # ...
  
  # RSS订阅源配置
  rss_feeds:
    enabled: true
    sources: # 包含27个数据源
    # ...
  
  # 网页抓取源配置
  web_scraping:
    enabled: false  # 默认关闭，避免反爬
    sources: # 包含18个数据源
    # ...

# AI分析参数
ai_analysis:
  # 关键词数量限制
  max_keywords: 50
  
  # 分析权重配置
  weights:
    frequency_weight: 0.4
    trend_weight: 0.4
    sentiment_weight: 0.2
  
  # 其他AI分析参数
  # ...
```

### 自定义配置

你可以根据需要修改以下配置：

1. **启用/禁用特定数据源**：在相应的`sources`列表中设置`enabled: true/false`
2. **调整并发数**：修改`concurrent_limit`参数（默认20）
3. **调整分析权重**：在`ai_analysis.weights`中修改各项权重值
4. **调整关键词数量**：修改`ai_analysis.max_keywords`参数（默认50）

## 📁 项目结构

```
SmartNewsRadar/
├── smart_radar.py         # 主程序入口
├── enhanced_data_fetcher.py  # 增强版数据获取器
├── smart_config.yaml      # 配置文件
├── smart_learning.py      # 自适应学习引擎
├── smart_notifier.py      # 智能通知系统
├── requirements.txt       # 依赖列表
├── output/                # 报告输出目录
└── README.md              # 项目说明文档
```

## 📊 核心功能详解

### 🔍 关键词发现机制

系统使用创新的中文n-gram分词算法，结合以下步骤发现热点关键词：

1. 从多源数据中提取所有新闻标题
2. 使用正则表达式提取中文词汇和英文单词
3. 对中文进行2-4字n-gram分词
4. 统计词频并过滤停用词和低频词
5. 计算关键词重要性（综合词频、趋势和情感得分）

### 📈 趋势分析算法

系统通过以下方式计算关键词趋势得分：

- 基于新闻排名的趋势分析
- 时间分布分析
- 多平台覆盖度评估
- 自适应权重调整

### 🧠 自适应学习系统

系统会不断学习优化分析结果：

- 记录关键词历史表现数据
- 根据实际热度调整分析权重
- 学习不同时间段的热点规律
- 保留7天学习数据，越用越智能

## 🚧 注意事项

1. **网页抓取注意**：默认关闭网页抓取功能，如需启用请修改配置并注意反爬策略
2. **API调用限制**：避免过于频繁的请求，可能导致API限流
3. **系统资源**：并发数设置过高可能占用较多系统资源
4. **数据存储**：长期运行会产生大量历史数据，请定期清理output目录

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进SmartNewsRadar。主要贡献方向包括：

- 添加更多数据源
- 改进关键词提取算法
- 优化AI学习模型
- 增强可视化报告

## 📜 许可证

本项目采用MIT许可证 - 查看LICENSE文件了解详情

## 📧 联系我们

如有问题或建议，请联系项目维护者。

---

SmartNewsRadar - 让热点发现更智能 🌟
        