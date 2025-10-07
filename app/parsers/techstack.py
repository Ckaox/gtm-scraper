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
        ("Sanity", "sanity.io|cdn.sanity.io"),
        ("Prismic", "prismic.io|cdn.prismic.io"),
        ("DatoCMS", "datocms.com"),
        ("Craft CMS", "craft.js|craftcms"),
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
        ("Shopware", "shopware.com"),
        ("Spree Commerce", "spreecommerce.org"),
        ("nopCommerce", "nopcommerce.com"),
        ("OpenCart", "opencart.com"),
        ("osCommerce", "oscommerce.com"),
    ],
    "Payment Processors": [
        ("Stripe", "js.stripe.com|stripe.com/v3"),
        ("PayPal", "paypal.com/sdk|paypalobjects.com"),
        ("Square", "squareup.com|js.squareup.com"),
        ("Klarna", "klarna.com|js.klarna.com"),
        ("Adyen", "adyen.com|js.adyen.com"),
        ("Braintree", "js.braintreegateway.com"),
        ("Razorpay", "razorpay.com"),
        ("Mollie", "mollie.com"),
        ("2Checkout", "2checkout.com"),
        ("Authorize.Net", "authorize.net"),
        ("Worldpay", "worldpay.com"),
        ("Redsys", "redsys.es"),
        ("Mercado Pago", "mercadopago.com"),
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
        ("Plausible", "plausible.io"),
        ("Fathom", "cdn.usefathom.com"),
        ("Simple Analytics", "scripts.simpleanalyticscdn.com"),
        ("Matomo", "matomo.org|piwik.org"),
        ("Yandex Metrica", "mc.yandex.ru"),
    ],
    "Marketing Automation": [
        ("HubSpot", "js.hs-analytics.net|js.hs-scripts.com|hs-forms"),
        ("Marketo", "munchkin.js|marketo"),
        ("Pardot", "pi.pardot.com"),
        ("ActiveCampaign", "activecampaign.com"),
        ("Mailchimp", "mailchimp.com|list-manage.com"),
        ("ConvertKit", "convertkit.com"),
        ("Klaviyo", "klaviyo.com"),
        ("GetResponse", "getresponse.com"),
        ("AWeber", "aweber.com"),
        ("Campaign Monitor", "campaignmonitor.com"),
        ("Constant Contact", "constantcontact.com"),
        ("MailerLite", "mailerlite.com"),
        ("Sendinblue", "sendinblue.com"),
        ("Drip", "d2z7bzwflv7old.cloudfront.net"),
    ],
    "Live Chat & Support": [
        ("Intercom", "widget.intercom.io"),
        ("Drift", "js.driftt.com"),
        ("Crisp", "client.crisp.chat"),
        ("Zendesk", "static.zdassets.com|zendesk"),
        ("Tawk.to", "tawk.to"),
        ("LiveChat", "livechatinc.com"),
        ("Freshchat", "freshchat.com"),
        ("Olark", "olark.com"),
        ("Tidio", "tidio.co"),
        ("Smartsupp", "smartsupp.com"),
        ("Chaport", "chaport.com"),
        ("Help Scout", "helpscout.net"),
    ],
    "CRM": [
        ("Salesforce", "force.com|embeddedservice/"),
        ("Zoho", "zohoforms|zohocrm"),
        ("Freshsales", "freshsales.io"),
        ("Pipedrive", "pipedrive.com"),
        ("Monday.com", "monday.com"),
        ("Airtable", "airtable.com"),
        ("Notion", "notion.so"),
        ("ClickUp", "clickup.com"),
        ("Asana", "asana.com"),
        # GoHighLevel y CRMs populares para marketing/outbound
        ("GoHighLevel", "gohighlevel\\.com|app\\.ghl\\.com|msgsndr\\.com|[a-z0-9-]+\\.msgsndr\\.com|/widget/booking/|form_embed\\.js"),
        ("HubSpot", "hubspot.com|hs-scripts.com|hsstatic.com|hubapi.com"),
        ("ActiveCampaign", "activecampaign.com"),
        ("ConvertKit", "convertkit.com"),
        ("Mailchimp", "mailchimp.com"),
        ("GetResponse", "getresponse.com"),
        ("Keap", "keap.com|infusionsoft.com"),
        ("Ontraport", "ontraport.com"),
        ("HighLevel", "highlevel.com"),
        ("Leadpages", "leadpages.net"),
        ("ClickFunnels", "clickfunnels.com"),
    ],
    "Marketing Automation": [
        ("Smartlead", "smartlead.ai"),
        ("Apollo.io", "apollo.io"),
        ("Outreach", "outreach.io"),
        ("SalesLoft", "salesloft.com"),
        ("Lemlist", "lemlist.com"),
        ("Reply.io", "reply.io"),
        ("Close.com", "close.com"),
        ("Instantly", "instantly.ai"),
        ("Sales Navigator", "linkedin.com/sales"),
        ("ZoomInfo", "zoominfo.com"),
        ("Calendly", "calendly.com"),
        ("Acuity Scheduling", "acuityscheduling.com"),
        ("Cal.com", "cal.com"),
        ("Typeform", "typeform.com"),
        ("Jotform", "jotform.com"),
        ("Gravity Forms", "gravityforms.com"),
    ],
    "A/B Testing": [
        ("Optimizely", "optimizely"),
        ("VWO", "visualwebsiteoptimizer.com"),
        ("Google Optimize", "googleoptimize.com"),
        ("Unbounce", "unbounce.com"),
        ("Kameleoon", "kameleoon.com"),
        ("Split.io", "split.io"),
        ("LaunchDarkly", "launchdarkly.com"),
    ],
    "Advertising": [
        ("Meta Pixel", "fbevents.js|facebook.com/tr"),
        ("LinkedIn Insight", "snap.licdn.com/li.lms-analytics"),
        ("TikTok Pixel", "analytics.tiktok.com"),
        ("Twitter Pixel", "static.ads-twitter.com"),
        ("Google Ads", "googleadservices.com|google.com/ads"),
        ("Microsoft Advertising", "clarity.ms|bing.com/ads"),
        ("Pinterest Pixel", "s.pinimg.com"),
        ("Snapchat Pixel", "sc-static.net"),
        ("Amazon DSP", "amazon-adsystem.com"),
        ("Taboola", "taboola.com"),
        ("Outbrain", "outbrain.com"),
        ("Criteo", "criteo.com"),
    ],
    "CDN & Hosting": [
        ("Cloudflare", "cloudflare"),
        ("Amazon CloudFront", "cloudfront.net"),
        ("JSDelivr", "jsdelivr.net"),
        ("UNPKG", "unpkg.com"),
        ("KeyCDN", "keycdn.com"),
        ("MaxCDN", "maxcdn.com"),
        ("Fastly", "fastly.com"),
        ("BunnyCDN", "bunnycdn.com"),
        ("AWS", "amazonaws.com"),
        ("Google Cloud", "gstatic.com|googleapis.com"),
        ("Azure", "azureedge.net|azure.com"),
        ("DigitalOcean", "digitaloceanspaces.com"),
        ("Netlify", "netlify.com|netlify.app"),
        ("Vercel", "vercel.app|vercel.com"),
        ("Heroku", "herokuapp.com"),
    ],
    "JavaScript Frameworks": [
        ("React", "react|_react|React"),
        ("Vue.js", "vue.js|Vue|__VUE__"),
        ("Angular", "angular.js|ng-|Angular"),
        ("jQuery", "jquery|jQuery"),
        ("Next.js", "_next/static|__NEXT_"),
        ("Gatsby", "gatsby|__gatsby"),
        ("Nuxt.js", "__nuxt"),
        ("Svelte", "svelte"),
        ("Alpine.js", "alpinejs"),
        ("Stimulus", "stimulus"),
        ("Ember.js", "ember"),
        ("Backbone.js", "backbone"),
        ("Lit", "lit-element|lit-html"),
    ],
    "CSS Frameworks": [
        ("Bootstrap", "bootstrap|Bootstrap"),
        ("Tailwind CSS", "tailwindcss|tailwind"),
        ("Bulma", "bulma"),
        ("Foundation", "foundation"),
        ("Materialize", "materialize"),
        ("Semantic UI", "semantic-ui"),
        ("UIkit", "uikit"),
        ("Ant Design", "antd"),
        ("Chakra UI", "chakra-ui"),
        ("Material-UI", "material-ui"),
    ],
    "Security": [
        ("reCAPTCHA", "recaptcha|google.com/recaptcha"),
        ("hCaptcha", "hcaptcha.com"),
        ("Cloudflare Turnstile", "cloudflare.com/turnstile"),
        ("Auth0", "auth0.com"),
        ("Okta", "okta.com"),
        ("Firebase Auth", "firebase.google.com/auth"),
        ("Supabase Auth", "supabase.co"),
    ],
    "Performance": [
        ("Lazy Loading", "loading=\"lazy\"|lazyload"),
        ("Service Worker", "sw.js|service-worker"),
        ("Web Vitals", "web-vitals"),
        ("Intersection Observer", "IntersectionObserver"),
        ("Critical CSS", "critical.css"),
        ("Resource Hints", "dns-prefetch|preconnect|prefetch"),
    ],
    "Maps": [
        ("Google Maps", "maps.googleapis.com|google.com/maps"),
        ("Mapbox", "mapbox.com"),
        ("OpenStreetMap", "openstreetmap.org"),
        ("Here Maps", "here.com"),
        ("Bing Maps", "bing.com/maps"),
        ("MapQuest", "mapquest.com"),
    ],
    "Forms": [
        ("Typeform", "typeform.com"),
        ("JotForm", "jotform.com"),
        ("Google Forms", "docs.google.com/forms"),
        ("Formstack", "formstack.com"),
        ("Wufoo", "wufoo.com"),
        ("Gravity Forms", "gravityforms.com"),
        ("Formidable Forms", "formidableforms.com"),
        ("Ninja Forms", "ninjaforms.com"),
    ],
    "Video & Media": [
        ("YouTube", "youtube.com|ytimg.com"),
        ("Vimeo", "vimeo.com"),
        ("Wistia", "wistia.com"),
        ("JW Player", "jwplayer.com"),
        ("Video.js", "videojs.com"),
        ("Brightcove", "brightcove.com"),
        ("Kaltura", "kaltura.com"),
        ("Cloudinary", "cloudinary.com"),
        ("ImageKit", "imagekit.io"),
    ],
    "Email Services": [
        ("SendGrid", "sendgrid.com"),
        ("Mailgun", "mailgun.com"),
        ("Amazon SES", "amazonses.com"),
        ("Postmark", "postmarkapp.com"),
        ("SparkPost", "sparkpost.com"),
        ("Mandrill", "mandrill.com"),
    ],
    "Social Media": [
        ("Facebook SDK", "connect.facebook.net"),
        ("Twitter Widgets", "platform.twitter.com"),
        ("LinkedIn SDK", "platform.linkedin.com"),
        ("Instagram", "instagram.com"),
        ("Pinterest", "assets.pinterest.com"),
        ("ShareThis", "sharethis.com"),
        ("AddThis", "addthis.com"),
    ],
}

def detect_tech(domain: str, html: str) -> List[dict]:
    """
    Detect technologies and group them by category.
    Returns list of dict with category and tech data.
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
    
    # Convert to list of dicts with category info
    result = []
    for category, data in found_by_category.items():
        # Remove duplicates from tools
        unique_tools = list(dict.fromkeys(data["tools"]))
        evidence = " | ".join(data["evidence"][:3])  # Limit evidence for readability
        
        result.append({
            "category": category,
            "tools": unique_tools,
            "evidence": evidence
        })
    
    return result
