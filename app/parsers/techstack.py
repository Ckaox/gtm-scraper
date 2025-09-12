from bs4 import BeautifulSoup
from typing import List
from ..schemas import TechFingerprint
import re

PATTERNS = {
    "CMS": [
        ("WordPress", "wp-content|wp-includes"),
        ("Webflow", "webflow.css|wf-"),
        ("Squarespace", "squarespace.com|sqs-"),
        ("Wix", "wixstatic|wixsite"),
        ("Ghost", "ghost-(sdk|content)"),
        ("Drupal", "drupal-settings-json|/sites/default/"),
        ("Joomla", "(/media/jui/|com_content)"),
    ],
    "Ecommerce": [
        ("Shopify", "cdn.shopify.com|/cart.js"),
        ("WooCommerce", "woocommerce"),
        ("BigCommerce", "cdn.bigcommerce.com"),
        ("Magento", "mage/cookies|Magento_Cookie|var/view_preprocessed"),
        ("PrestaShop", "prestashop"),
    ],
    "Analytics": [
        ("GTM", "GTM-"),
        ("GA4", "gtag\\('config','G-|dataLayer"),
        ("UA", "UA-\\d+-\\d+"),
        ("Segment", "cdn.segment.com/analytics.js"),
        ("Mixpanel", "cdn.mxpnl.com"),
        ("Amplitude", "amplitude.com|cdn.amplitude.com"),
        ("Heap", "cdn.heapanalytics.com"),
        ("FullStory", "fullstory.com|fs\\.js"),
        ("Hotjar", "static.hotjar.com"),
    ],
    "Marketing": [
        ("HubSpot", "js.hs-analytics.net|js.hs-scripts.com|hs-forms"),
        ("Marketo", "munchkin.js|marketo"),
        ("Intercom", "widget.intercom.io"),
        ("Drift", "js.driftt.com"),
        ("Clearbit Forms", "clearbitforms|clearbit.com"),
    ],
    "CRM": [
        ("Salesforce", "force.com|embeddedservice/"),
        ("Pardot", "pi.pardot.com"),
        ("Zoho", "zohoforms|zohocrm"),
        ("Freshsales", "freshsales.io"),
    ],
    "ABTest": [
        ("Optimizely", "optimizely"),
        ("VWO", "visualwebsiteoptimizer.com|dev.visualwebsiteoptimizer.com"),
    ],
    "Ads": [
        ("Meta Pixel", "fbevents.js"),
        ("LinkedIn Insight", "snap.licdn.com/li.lms-analytics|linkedininsight"),
        ("TikTok Pixel", "analytics.tiktok.com"),
        ("Twitter Pixel", "static.ads-twitter.com"),
    ],
    "Chat": [
        ("Crisp", "client.crisp.chat"),
        ("Zendesk", "static.zdassets.com|zendesk"),
        ("Tawk.to", "tawk.to"),
    ],
}

def detect_tech(url: str, html: str) -> List[TechFingerprint]:
    out: List[TechFingerprint] = []
    if not html: return out
    hay = html if len(html) < 2_000_000 else html[:2_000_000]
    for cat, pairs in PATTERNS.items():
        for tool, pattern in pairs:
            if re.search(pattern, hay, re.I):
                out.append(TechFingerprint(category=cat, tool=tool, evidence=pattern))
    return out
