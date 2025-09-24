#  智能新闻雷达

热点新闻与关键词分析系统

`python smart_radar.py`

<img width="1417" height="1253" alt="屏幕截图 2025-09-24 100658" src="https://github.com/user-attachments/assets/d35c0827-3d07-4f39-9e23-87b65d6461da" />

<img width="2560" height="1368" alt="屏幕截图 2025-09-24 100315" src="https://github.com/user-attachments/assets/a643ab89-bb99-4b55-bb02-cb5915e24076" />

<img width="2560" height="1368" alt="屏幕截图 2025-09-24 100326" src="https://github.com/user-attachments/assets/413ba3de-79ee-4b4b-9f93-00acb57df05a" />

<img width="2560" height="1368" alt="屏幕截图 2025-09-24 100351" src="https://github.com/user-attachments/assets/9a5ae7bc-12e9-4dc8-bb24-9c37ac6358a4" />

## 📊 核心功能详解

### 🔍 关键词发现机制

系统使用基于jieba的中文分词算法，结合以下步骤发现热点关键词：

1. 从多源数据中提取所有新闻标题
2. 使用正则表达式提取中文词汇和英文单词
3. 使用jieba进行中文分词处理
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
- 保留14天学习数据，越用越智能

## 🔧 news_sources.json 配置详解

`news_sources.json`是系统最重要的配置文件之一，它决定了系统从哪些平台获取新闻数据。为了获得最佳效果，建议您根据自己的需求仔细配置此文件。

### 文件结构

```json
{
  "description": "新闻源配置",
  "type_defaults": {
    "newsnow_api": true,  // 全局启用/禁用API源
    "rss": false,         // 全局启用/禁用RSS源
    "web_scraper": false  // 全局启用/禁用网页抓取源
  },
  "news_sources": {
    "newsnow_api": [      // API数据源配置列表
      {
        "id": "weibo",    // 唯一标识符
        "name": "微博热搜", // 显示名称
        "url": "https://newsnow.busiyi.world/api/s?id=weibo&latest" // API URL
      },
      // 更多API源...
    ],
    "rss": [              // RSS数据源配置列表
      // RSS源配置...
    ],
    "web_scraper": [      // 网页抓取数据源配置列表
      // 网页抓取源配置...
    ]
  }
}
```

### 配置建议

1. **逐步启用数据源**：首次使用时，建议先启用少量优质数据源，待系统稳定运行后再逐步增加
2. **平衡数据源类型**：混合使用API、RSS和网页抓取源，以提高数据多样性和系统稳定性
3. **根据兴趣定制**：专注于您感兴趣的领域，启用相关平台的数据源
4. **定期检查更新**：定期检查数据源是否有效，及时替换失效的数据源

### 添加自定义数据源

您可以根据以下格式添加自定义数据源：

```json
// API源格式
{
  "id": "自定义ID",
  "name": "显示名称",
  "url": "API接口URL"
}

// RSS源格式
{
  "id": "自定义ID",
  "name": "显示名称",
  "url": "RSS订阅URL"
}

// 网页抓取源格式
{
  "id": "自定义ID",
  "name": "显示名称",
  "url": "目标网站URL",
  "selector": "CSS选择器，用于提取新闻标题"
}
```

## 🚧 注意事项

1. **网页抓取注意**：网页抓取功能默认关闭，如需启用请修改news_sources.json并注意反爬策略
2. **RSS源注意**：RSS源功能默认关闭，如需启用请修改news_sources.json并仔细验证每个源是否正确
3. **API调用限制**：避免过于频繁的请求，可能导致API限流
4. **系统资源**：并发数设置过高可能占用较多系统资源
5. **数据存储**：每次运行都会自动清理output目录，然后再生成新的HTML报告和JSON报告
6. **数据源维护**：由于第三方平台的变化，部分数据源可能会失效，建议定期检查和更新news_sources.json

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
