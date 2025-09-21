#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SmartNotifier - 智能通知系统
支持多平台推送，具有简洁美观的消息格式

Author: Inspired by Jobs' philosophy of simplicity
"""

import json
import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SmartNotifier:
    """智能通知系统"""
    
    def __init__(self, config: Dict):
        self.config = config.get('notification', {})
        self.enabled = self.config.get('enabled', False)
    
    def send_keyword_report(self, keywords: List, total_news: int) -> bool:
        """发送关键词报告到所有启用的平台"""
        if not self.enabled:
            logger.info("通知功能未启用")
            return True
        
        success_count = 0
        total_platforms = 0
        
        for platform_name, platform_config in self.config.get('platforms', {}).items():
            if platform_config.get('enabled', False):
                total_platforms += 1
                if self._send_to_platform(platform_name, platform_config, keywords, total_news):
                    success_count += 1
        
        logger.info(f"通知发送完成: {success_count}/{total_platforms} 个平台成功")
        return success_count == total_platforms
    
    def _send_to_platform(self, platform: str, config: Dict, keywords: List, total_news: int) -> bool:
        """发送到指定平台"""
        try:
            if platform == 'feishu':
                return self._send_feishu(config, keywords, total_news)
            elif platform == 'wework':
                return self._send_wework(config, keywords, total_news)
            elif platform == 'dingtalk':
                return self._send_dingtalk(config, keywords, total_news)
            elif platform == 'telegram':
                return self._send_telegram(config, keywords, total_news)
            else:
                logger.warning(f"不支持的平台: {platform}")
                return False
        except Exception as e:
            logger.error(f"发送到 {platform} 失败: {e}")
            return False
    
    def _create_message_content(self, keywords: List, total_news: int) -> str:
        """创建消息内容"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 消息标题
        content = f"🎯 智能新闻雷达 - 自动发现的热点关键词\\n"
        content += f"📊 数据时间: {timestamp}\\n"
        content += f"📈 分析了 {total_news} 条新闻，发现 {len(keywords)} 个关键词\\n\\n"
        
        # 关键词列表
        content += "🔥 热点关键词排行:\\n"
        content += "━━━━━━━━━━━━━━━━━━━\\n"
        
        for i, keyword in enumerate(keywords[:10], 1):
            # 根据重要性添加不同的emoji
            if keyword.importance >= 8:
                emoji = "🌟"
            elif keyword.importance >= 6:
                emoji = "⭐"
            elif keyword.importance >= 4:
                emoji = "🔸"
            else:
                emoji = "▫️"
            
            content += f"{emoji} {i:2d}. {keyword.word}\\n"
            content += f"     重要性: {keyword.importance:.1f} | 出现: {keyword.frequency}次\\n\\n"
        
        content += "━━━━━━━━━━━━━━━━━━━\\n"
        content += "🤖 由AI自动分析生成，无需人工预设关键词"
        
        return content
    
    def _send_feishu(self, config: Dict, keywords: List, total_news: int) -> bool:
        """发送到飞书"""
        webhook_url = config.get('webhook_url', '')
        if not webhook_url:
            logger.warning("飞书webhook_url未配置")
            return False
        
        content = self._create_message_content(keywords, total_news)
        
        # 飞书消息格式
        data = {
            "msg_type": "text",
            "content": {
                "text": content
            }
        }
        
        response = requests.post(webhook_url, json=data, timeout=10)
        response.raise_for_status()
        
        logger.info("飞书通知发送成功")
        return True
    
    def _send_wework(self, config: Dict, keywords: List, total_news: int) -> bool:
        """发送到企业微信"""
        webhook_url = config.get('webhook_url', '')
        if not webhook_url:
            logger.warning("企业微信webhook_url未配置")
            return False
        
        content = self._create_message_content(keywords, total_news)
        
        # 企业微信消息格式
        data = {
            "msgtype": "text",
            "text": {
                "content": content
            }
        }
        
        response = requests.post(webhook_url, json=data, timeout=10)
        response.raise_for_status()
        
        logger.info("企业微信通知发送成功")
        return True
    
    def _send_dingtalk(self, config: Dict, keywords: List, total_news: int) -> bool:
        """发送到钉钉"""
        webhook_url = config.get('webhook_url', '')
        if not webhook_url:
            logger.warning("钉钉webhook_url未配置")
            return False
        
        content = self._create_message_content(keywords, total_news)
        
        # 钉钉消息格式
        data = {
            "msgtype": "text",
            "text": {
                "content": content
            }
        }
        
        response = requests.post(webhook_url, json=data, timeout=10)
        response.raise_for_status()
        
        logger.info("钉钉通知发送成功")
        return True
    
    def _send_telegram(self, config: Dict, keywords: List, total_news: int) -> bool:
        """发送到Telegram"""
        bot_token = config.get('bot_token', '')
        chat_id = config.get('chat_id', '')
        
        if not bot_token or not chat_id:
            logger.warning("Telegram bot_token或chat_id未配置")
            return False
        
        content = self._create_message_content(keywords, total_news)
        
        # Telegram API
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": content,
            "parse_mode": "HTML"
        }
        
        response = requests.post(url, data=data, timeout=10)
        response.raise_for_status()
        
        logger.info("Telegram通知发送成功")
        return True

class SmartReportSender:
    """智能报告发送器 - 支持富文本格式"""
    
    def __init__(self, config: Dict):
        self.config = config.get('notification', {})
        self.enabled = self.config.get('enabled', False)
    
    def send_rich_report(self, keywords: List, news_items: List, html_path: str) -> bool:
        """发送富文本格式的报告"""
        if not self.enabled:
            return True
        
        # 创建富文本卡片消息（适用于飞书等支持富文本的平台）
        card_content = self._create_rich_card(keywords, news_items, html_path)
        
        # 这里可以扩展为发送到支持富文本的平台
        logger.info("富文本报告准备就绪")
        return True
    
    def _create_rich_card(self, keywords: List, news_items: List, html_path: str) -> Dict:
        """创建富文本卡片"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 飞书卡片格式示例
        card = {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "🎯 智能新闻雷达报告"
                },
                "subtitle": {
                    "tag": "plain_text",
                    "content": f"AI自动发现 · {timestamp}"
                }
            },
            "elements": []
        }
        
        # 添加统计信息
        stats_element = {
            "tag": "div",
            "fields": [
                {
                    "is_short": True,
                    "text": {
                        "tag": "lark_md",
                        "content": f"**📊 分析新闻**\\n{len(news_items)} 条"
                    }
                },
                {
                    "is_short": True,
                    "text": {
                        "tag": "lark_md", 
                        "content": f"**🔥 发现关键词**\\n{len(keywords)} 个"
                    }
                }
            ]
        }
        card["elements"].append(stats_element)
        
        # 添加分隔线
        card["elements"].append({"tag": "hr"})
        
        # 添加关键词列表
        keywords_text = ""
        for i, keyword in enumerate(keywords[:8], 1):
            importance_stars = "⭐" * min(5, int(keyword.importance / 2))
            keywords_text += f"{i}. **{keyword.word}** {importance_stars}\\n"
            keywords_text += f"   重要性: {keyword.importance:.1f} | 出现: {keyword.frequency}次\\n\\n"
        
        keywords_element = {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": keywords_text
            }
        }
        card["elements"].append(keywords_element)
        
        return card