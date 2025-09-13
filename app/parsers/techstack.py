from bs4 import BeautifulSoup
from typing import List
from ..schemas import TechFingerprint
import re

PATTERNS = {
    "CMS": [
        ("WordPress", "wp-content|wp-includes|/wp-json/"),
        ("Webflow", "webflow.css|wf-|webflow.com"),
        ("Squarespace", "squarespace.com|sqs-"),
        ("Wix", "wixstatic|wixsite"),
        ("Ghost", "ghost-(sdk|content)"),
        ("Drupal", "drupal-settings-json|/sites/default/|drupal.js"),
        ("Joomla", "(/media/jui/|com_content)"),
        ("Contentful", "contentful.com|cdn.contentful.com"),
        ("Strapi", "strapi.io"),
        ("Webflow", "assets.website-files.com"),
    ],
    "Ecommerce": [
        ("Shopify", "cdn.shopify.com|/cart.js|shop_money"),
        ("WooCommerce", "woocommerce|wc-ajax"),
        ("BigCommerce", "cdn.bigcommerce.com"),
        ("Magento", "mage/cookies|Magento_Cookie|var/view_preprocessed"),
        ("PrestaShop", "prestashop"),
        ("Vtex", "vtex.com.br|vtexcommercestable"),
        ("Mercado Shops", "mercadoshops.com.ar"),
        ("TiendaNube", "mitiendanube.com|tiendanube.com"),
    ],
    "Analytics": [
        ("Google Tag Manager", "GTM-|googletagmanager.com"),
        ("Google Analytics 4", "gtag\\('config','G-|G-[A-Z0-9]{10}"),
        ("Universal Analytics", "UA-\\d+-\\d+"),
        ("Segment", "cdn.segment.com/analytics.js|segment.com"),
        ("Mixpanel", "cdn.mxpnl.com|mixpanel.com"),
        ("Amplitude", "amplitude.com|cdn.amplitude.com"),
        ("Heap", "cdn.heapanalytics.com"),
        ("FullStory", "fullstory.com|fs\\.js"),
        ("Hotjar", "static.hotjar.com|hotjar"),
        ("Adobe Analytics", "omtrdc.net|adobe.com/analytics"),
        ("Clarity", "clarity.ms"),
    ],
    "Marketing Automation": [
        ("HubSpot", "js.hs-analytics.net|js.hs-scripts.com|hs-forms"),
        ("Marketo", "munchkin.js|marketo"),
        ("Pardot", "pi.pardot.com"),
        ("ActiveCampaign", "activecampaign.com"),
        ("Mailchimp", "mailchimp.com|list-manage.com"),
        ("ConvertKit", "convertkit.com"),
        ("Klaviyo", "klaviyo.com"),
    ],
    "Live Chat": [
        ("Intercom", "widget.intercom.io"),
        ("Drift", "js.driftt.com"),
        ("Crisp", "client.crisp.chat"),
        ("Zendesk", "static.zdassets.com|zendesk"),
        ("Tawk.to", "tawk.to"),
        ("LiveChat", "livechatinc.com"),
        ("Freshchat", "freshchat.com"),
    ],
    "CRM": [
        ("Salesforce", "force.com|embeddedservice/"),
        ("Zoho", "zohoforms|zohocrm"),
        ("Freshsales", "freshsales.io"),
        ("Pipedrive", "pipedrive.com"),
        ("Monday.com", "monday.com"),
    ],
    "A/B Testing": [
        ("Optimizely", "optimizely"),
        ("VWO", "visualwebsiteoptimizer.com"),
        ("Google Optimize", "googleoptimize.com"),
        ("Unbounce", "unbounce.com"),
    ],
    "Advertising": [
        ("Meta Pixel", "fbevents.js|facebook.com/tr"),
        ("LinkedIn Insight", "snap.licdn.com/li.lms-analytics"),
        ("TikTok Pixel", "analytics.tiktok.com"),
        ("Twitter Pixel", "static.ads-twitter.com"),
        ("Google Ads", "googleadservices.com|google.com/ads"),
        ("Microsoft Advertising", "clarity.ms|bing.com/ads"),
    ],
    "CDN": [
        ("Cloudflare", "cloudflare"),
        ("Amazon CloudFront", "cloudfront.net"),
        ("JSDelivr", "jsdelivr.net"),
        ("UNPKG", "unpkg.com"),
        ("KeyCDN", "keycdn.com"),
    ],
    "JavaScript Frameworks": [
        ("React", "react|_react|React"),
        ("Vue.js", "vue.js|Vue|__VUE__"),
        ("Angular", "angular.js|ng-|Angular"),
        ("jQuery", "jquery|jQuery"),
        ("Next.js", "_next/static|__NEXT_"),
        ("Gatsby", "gatsby|__gatsby"),
        ("Nuxt.js", "__nuxt"),
    ],
    "CSS Frameworks": [
        ("Bootstrap", "bootstrap|Bootstrap"),
        ("Tailwind CSS", "tailwindcss|tailwind"),
        ("Bulma", "bulma"),
        ("Foundation", "foundation"),
    ],
    "Security": [
        ("reCAPTCHA", "recaptcha|google.com/recaptcha"),
        ("hCaptcha", "hcaptcha.com"),
        ("Cloudflare Turnstile", "cloudflare.com/turnstile"),
    ],
    "Performance": [
        ("Lazy Loading", "loading=\"lazy\"|lazyload"),
        ("Service Worker", "sw.js|service-worker"),
        ("Web Vitals", "web-vitals"),
    ],
    "Maps": [
        ("Google Maps", "maps.googleapis.com|google.com/maps"),
        ("Mapbox", "mapbox.com"),
        ("OpenStreetMap", "openstreetmap.org"),
    ],
    "Forms": [
        ("Typeform", "typeform.com"),
        ("JotForm", "jotform.com"),
        ("Gravity Forms", "gravityforms"),
        ("Contact Form 7", "contact-form-7"),
        ("Formspree", "formspree.io"),
    ],
    "Payment": [
        ("Stripe", "stripe.com|js.stripe.com"),
        ("PayPal", "paypal.com|paypalobjects.com"),
        ("Square", "squareup.com"),
        ("MercadoPago", "mercadopago.com"),
        ("Checkout.com", "checkout.com"),
    ],
}

def detect_tech(url: str, html: str) -> List[TechFingerprint]:
    """
    Detect technologies and group them by category.
    Returns list of TechFingerprint with category and list of tools.
    """
    if not html: 
        return []
    
    # Limitar HTML para performance (máximo 1MB)
    hay = html if len(html) < 1_000_000 else html[:1_000_000]
    
    # Group findings by category
    found_by_category = {}
    
    for cat, pairs in PATTERNS.items():
        for tool, pattern in pairs:
            if re.search(pattern, hay, re.I):
                if cat not in found_by_category:
                    found_by_category[cat] = {
                        "tools": [],
                        "evidence": []
                    }
                found_by_category[cat]["tools"].append(tool)
                found_by_category[cat]["evidence"].append(pattern)
    
    # Convert to list of TechFingerprint
    result = []
    for category, data in found_by_category.items():
        # Remove duplicates from tools
        unique_tools = list(dict.fromkeys(data["tools"]))
        evidence = " | ".join(data["evidence"][:3])  # Limit evidence for readability
        
        result.append(TechFingerprint(
            category=category,
            tools=unique_tools,
            evidence=evidence
        ))
    
    return result
