#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规则数据定义
集中管理所有内置规则，便于维护
"""

# YouTube 相关域名后缀
YOUTUBE_DOMAIN_SUFFIXES = [
    'ggpht.cn', 'ggpht.com', 'googlevideo.com', 'gvt1.com', 'gvt2.com',
    'video.google.com', 'wide-youtube.l.google.com', 'withyoutube.com',
    'youtu.be', 'youtube', 'youtube-nocookie.com', 'youtube-ui.l.google.com',
    'youtube.ae', 'youtube.al', 'youtube.am', 'youtube.at', 'youtube.az',
    'youtube.ba', 'youtube.be', 'youtube.bg', 'youtube.bh', 'youtube.bo',
    'youtube.by', 'youtube.ca', 'youtube.cat', 'youtube.ch', 'youtube.cl',
    'youtube.co', 'youtube.co.ae', 'youtube.co.at', 'youtube.co.cr',
    'youtube.co.hu', 'youtube.co.id', 'youtube.co.il', 'youtube.co.in',
    'youtube.co.jp', 'youtube.co.ke', 'youtube.co.kr', 'youtube.co.ma',
    'youtube.co.nz', 'youtube.co.th', 'youtube.co.tz', 'youtube.co.ug',
    'youtube.co.uk', 'youtube.co.ve', 'youtube.co.za', 'youtube.co.zw',
    'youtube.com', 'youtube.com.ar', 'youtube.com.au', 'youtube.com.az',
    'youtube.com.bd', 'youtube.com.bh', 'youtube.com.bo', 'youtube.com.br',
    'youtube.com.by', 'youtube.com.co', 'youtube.com.do', 'youtube.com.ec',
    'youtube.com.ee', 'youtube.com.eg', 'youtube.com.es', 'youtube.com.gh',
    'youtube.com.gr', 'youtube.com.gt', 'youtube.com.hk', 'youtube.com.hn',
    'youtube.com.hr', 'youtube.com.jm', 'youtube.com.jo', 'youtube.com.kw',
    'youtube.com.lb', 'youtube.com.lv', 'youtube.com.ly', 'youtube.com.mk',
    'youtube.com.mt', 'youtube.com.mx', 'youtube.com.my', 'youtube.com.ng',
    'youtube.com.ni', 'youtube.com.om', 'youtube.com.pa', 'youtube.com.pe',
    'youtube.com.ph', 'youtube.com.pk', 'youtube.com.pt', 'youtube.com.py',
    'youtube.com.qa', 'youtube.com.ro', 'youtube.com.sa', 'youtube.com.sg',
    'youtube.com.sv', 'youtube.com.tn', 'youtube.com.tr', 'youtube.com.tw',
    'youtube.com.ua', 'youtube.com.uy', 'youtube.com.ve', 'youtube.cr',
    'youtube.cz', 'youtube.de', 'youtube.dk', 'youtube.ee', 'youtube.es',
    'youtube.fi', 'youtube.fr', 'youtube.ge', 'youtube.googleapis.com',
    'youtube.gr', 'youtube.gt', 'youtube.hk', 'youtube.hr', 'youtube.hu',
    'youtube.ie', 'youtube.in', 'youtube.iq', 'youtube.is', 'youtube.it',
    'youtube.jo', 'youtube.jp', 'youtube.kr', 'youtube.kz', 'youtube.la',
    'youtube.lk', 'youtube.lt', 'youtube.lu', 'youtube.lv', 'youtube.ly',
    'youtube.ma', 'youtube.md', 'youtube.me', 'youtube.mk', 'youtube.mn',
    'youtube.mx', 'youtube.my', 'youtube.ng', 'youtube.ni', 'youtube.nl',
    'youtube.no', 'youtube.pa', 'youtube.pe', 'youtube.ph', 'youtube.pk',
    'youtube.pl', 'youtube.pr', 'youtube.pt', 'youtube.qa', 'youtube.ro',
    'youtube.rs', 'youtube.ru', 'youtube.sa', 'youtube.se', 'youtube.sg',
    'youtube.si', 'youtube.sk', 'youtube.sn', 'youtube.soy', 'youtube.sv',
    'youtube.tn', 'youtube.tv', 'youtube.ua', 'youtube.ug', 'youtube.uy',
    'youtube.vn', 'youtubeeducation.com', 'youtubeembeddedplayer.googleapis.com',
    'youtubefanfest.com', 'youtubegaming.com', 'youtubego.co.id',
    'youtubego.co.in', 'youtubego.com', 'youtubego.com.br', 'youtubego.id',
    'youtubego.in', 'youtubei.googleapis.com', 'youtubekids.com',
    'youtubemobilesupport.com', 'yt.be', 'ytimg.com',
]

# X/Twitter 视频相关
X_VIDEO_DOMAINS = ['video.twimg.com', 'pscp.tv']

# YouTube 完整规则列表
def get_youtube_rules():
    """生成 YouTube 规则列表"""
    rules = [f"DOMAIN-SUFFIX,{d}" for d in YOUTUBE_DOMAIN_SUFFIXES]
    rules.append("DOMAIN-KEYWORD,youtube")
    # X.com 视频
    rules.extend([f"DOMAIN-SUFFIX,{d}" for d in X_VIDEO_DOMAINS])
    rules.append("DOMAIN-KEYWORD,video.twimg.com")
    # IP 段
    rules.extend([
        "IP-CIDR,172.110.32.0/21",
        "IP-CIDR,216.73.80.0/20",
        "IP-CIDR6,2620:120:e000::/40",
    ])
    return rules


# OpenAI / ChatGPT 规则
OPENAI_RULES = [
    "DOMAIN,browser-intake-datadoghq.com",
    "DOMAIN,chat.openai.com.cdn.cloudflare.net",
    "DOMAIN,openai-api.arkoselabs.com",
    "DOMAIN,openaicom-api-bdcpf8c6d2e9atf6.z01.azurefd.net",
    "DOMAIN,openaicomproductionae4b.blob.core.windows.net",
    "DOMAIN,production-openaicom-storage.azureedge.net",
    "DOMAIN,static.cloudflareinsights.com",
    "DOMAIN-SUFFIX,ai.com",
    "DOMAIN-SUFFIX,algolia.net",
    "DOMAIN-SUFFIX,api.statsig.com",
    "DOMAIN-SUFFIX,auth0.com",
    "DOMAIN-SUFFIX,chatgpt.com",
    "DOMAIN-SUFFIX,chatgpt.livekit.cloud",
    "DOMAIN-SUFFIX,client-api.arkoselabs.com",
    "DOMAIN-SUFFIX,events.statsigapi.net",
    "DOMAIN-SUFFIX,featuregates.org",
    "DOMAIN-SUFFIX,host.livekit.cloud",
    "DOMAIN-SUFFIX,identrust.com",
    "DOMAIN-SUFFIX,intercom.io",
    "DOMAIN-SUFFIX,intercomcdn.com",
    "DOMAIN-SUFFIX,launchdarkly.com",
    "DOMAIN-SUFFIX,oaistatic.com",
    "DOMAIN-SUFFIX,oaiusercontent.com",
    "DOMAIN-SUFFIX,observeit.net",
    "DOMAIN-SUFFIX,openai.com",
    "DOMAIN-SUFFIX,openaiapi-site.azureedge.net",
    "DOMAIN-SUFFIX,openaicom.imgix.net",
    "DOMAIN-SUFFIX,segment.io",
    "DOMAIN-SUFFIX,sentry.io",
    "DOMAIN-SUFFIX,stripe.com",
    "DOMAIN-SUFFIX,turn.livekit.cloud",
    "DOMAIN-KEYWORD,openai",
    "IP-CIDR,24.199.123.28/32",
    "IP-CIDR,64.23.132.171/32",
    "IP-ASN,20473",
]

# Claude 规则
CLAUDE_RULES = [
    "DOMAIN,cdn.usefathom.com",
    "DOMAIN-SUFFIX,anthropic.com",
    "DOMAIN-SUFFIX,claude.ai",
]

# Grok / X.AI 规则
GROK_RULES = [
    "DOMAIN-SUFFIX,x.ai",
    "DOMAIN-SUFFIX,grok.com",
    "DOMAIN-KEYWORD,grok",
]


def get_ai_rules():
    """生成 AI 服务规则列表（不含 Gemini）"""
    return OPENAI_RULES + CLAUDE_RULES + GROK_RULES


# 广告屏蔽规则
AD_BLOCK_RULES = [
    # X/Twitter 广告
    "DOMAIN-SUFFIX,ads.twitter.com",
    "DOMAIN-SUFFIX,ads-api.twitter.com",
    "DOMAIN-SUFFIX,analytics.twitter.com",
    "DOMAIN-SUFFIX,scribe.twitter.com",
    "DOMAIN-SUFFIX,syndication.twitter.com",
    "DOMAIN-SUFFIX,advertising.twitter.com",
    "DOMAIN-SUFFIX,ads.x.com",
    "DOMAIN-SUFFIX,analytics.x.com",
    "DOMAIN-KEYWORD,ads-twitter",
    "DOMAIN-KEYWORD,twitterads",
]


# 香港节点识别关键词
HK_KEYWORDS = ["HK", "Hong Kong", "香港", "HongKong", "HONG KONG"]
