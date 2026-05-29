from http.server import BaseHTTPRequestHandler
from datetime import datetime
import requests
import re
import json
import os

BLOCKED_SOURCES = {
    "Pypi.org", "Slickdeals.net", "Dealnews.com", "Bringatrailer.com",
    "Rlsbb.to", "Adventurouskate.com", "Bossip"
}

KEY_SOURCES = []


def fetch_headlines():
    API_KEY = os.getenv("NEWS_API_KEY")
    if not API_KEY:
        return []

    query = (
        "5G OR OpenRAN OR WiFi OR \"network slicing\" OR \"fixed wireless\" "
        "OR \"small cell\" OR \"massive MIMO\" OR \"edge AI\" OR \"WiFi 7\" "
        "OR \"WiFi 6\" OR ONT OR OLT"
    )

    try:
        response = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": query,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": 50,
                "apiKey": API_KEY
            },
            timeout=10
        )
        data = response.json()
        articles = data.get("articles", [])
        headlines = []
        for article in articles:
            title = article.get("title", "")
            url = article.get("url", "")
            source = article.get("source", {}).get("name", "Unknown")
            if title and url and source not in BLOCKED_SOURCES:
                headlines.append({"text": title, "link": url, "source": source})
        return headlines
    except Exception as e:
        print(f"NewsAPI fetch failed: {str(e)}")
        return []


def extract_signals_fast(text):
    text_lower = text.lower()
    telecom_keywords = {
        "wifi": 3, "5g": 3, "openran": 3, "ran": 2, "core network": 2,
        "ont": 4, "olt": 4, "fixed wireless": 2, "small cell": 2,
        "beamforming": 2, "massive mimo": 2, "network slicing": 3,
        "wifi 6": 3, "wifi 6e": 4, "wifi 7": 4, "telecom": 2,
        "broadband": 2, "spectrum": 2, "fiber": 2, "lte": 2,
        # Next-gen WiFi (beyond WiFi 7)
        "wifi 8": 4, "ieee 802.11bn": 4, "eht": 3, "ultra high reliability": 3, "next generation":4,

        # 6G (active standards work now, commercial ~2030)
        "6g": 4, "imt-2030": 4, "terahertz": 3, "thz": 3, "sub-thz": 3,

        # Open networking evolution
        "o-ran": 4, "open ran": 4, "disaggregated ran": 3, "vran": 3, "cloud ran": 3,

        # Private networks (big enterprise trend)
        "private 5g": 4, "private lte": 3, "cbrs": 3, "neutral host": 3,

        # Satellite/NTN (your Viasat context)
        "ntn": 4, "non-terrestrial": 4, "leo": 3, "meo": 2, "starlink": 3,
        "satellite broadband": 3, "direct to device": 4, "d2d": 2,

        # Next-gen core
        "service based architecture": 3, "sba": 2, "cloud native": 2,
        "network as a service": 3, "naas": 3, "intent based networking": 3,

        # 3GPP release milestones (journalists reference these constantly)
        "release 18": 4, "rel-18": 4, "release 19": 4, "rel-19": 4,
        "3gpp": 3,

        # 5G Advanced (Release 18+ branding)
        "5g advanced": 4, "5g-advanced": 4,

        # Key Release 18/19 features getting press
        "redcap": 4, "reduced capability": 3,  # IoT/wearables
        "sidelink": 3,                          # device-to-device
        "positioning": 2,                       # precise location
        "xr": 3, "extended reality": 3,        # AR/VR over 5G
        "ambient iot": 4,                       # battery-free devices
        "integrated sensing": 3, "isac": 4,    # sensing + comms combined
    }
    telecom_score = sum(weight for kw, weight in telecom_keywords.items() if kw in text_lower)

    ai_keywords = {
        "llm": 3, "ml": 2, "inference": 3, "edge ai": 3, "tinyml": 2,
        "anomaly detection": 2, "predictive maintenance": 2, "computer vision": 2,
        "nlp": 2, "reinforcement learning": 1, "ai": 1, "artificial intelligence": 2,
        "machine learning": 2, "generative": 1, "automation": 1
    }
    ai_score = sum(weight for kw, weight in ai_keywords.items() if kw in text_lower)

    cost_patterns = [
        r'(saved?|reduced?|cut)\s*\$?\d+[\d,.]*(?:\s*(?:million|billion|m|b))?',
        r'(cost\s*(?:savings|reduction|avoidance))\s*\$?\d+[\d,.]*',
        r'(truck\s*rolls?|dispatch)\s*(?:reduced?|lowered?|cut)\s*\d+%',
        r'(roi|return\s*on\s*investment)\s*\d+%'
    ]
    cost_signal = ""
    for pattern in cost_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            cost_signal = match.group(0).strip()
            break

    time_horizon = "Mid-Term"
    if any(term in text_lower for term in ["2025", "2026", "long-term", "roadmap", "3-5 year"]):
        time_horizon = "Long-Term"
    elif any(term in text_lower for term in ["2024", "q1", "q2", "h1", "h2", "pilot", "trial", "launch"]):
        time_horizon = "Near-Term"

    return {
        "telecom_score": telecom_score,
        "ai_score": ai_score,
        "cost_signal": cost_signal,
        "time_horizon": time_horizon
    }


def detect_vendors_fast(text):
    vendors = {
        "airties": "Airties", "sagemcom": "Sagemcom", "commscope": "CommScope",
        "cisco": "Cisco", "nokia": "Nokia", "ericsson": "Ericsson",
        "qualcomm": "Qualcomm", "intel": "Intel", "samsung": "Samsung",
        "huawei": "Huawei", "zte": "ZTE", "ciena": "Ciena",
        "american tower": "American Tower", "crown castle": "Crown Castle",
        "verizon": "Verizon (Competitor)", "at&t": "AT&T (Competitor)",
        "t-mobile": "T-Mobile US (Competitor)", "vmware": "VMware",
        "red hat": "Red Hat", "boldyn": "Boldyn Networks",
        "jio": "Reliance Jio", "airtel": "Bharti Airtel"
    }
    text_lower = text.lower()
    found = [vendor for key, vendor in vendors.items() if key in text_lower]
    return list(set(found))[:3]


def push_to_notion_safe(results):
    NOTION_TOKEN = os.getenv("NOTION_TOKEN")
    NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
    if not NOTION_TOKEN or not NOTION_DATABASE_ID:
        return
    try:
        from notion_client import Client
        notion = Client(auth=NOTION_TOKEN)
        for item in results[:5]:
            notion.pages.create(
                parent={"database_id": NOTION_DATABASE_ID},
                properties={
                    "Headline": {"title": [{"text": {"content": item["Headline"]}}]},
                    "Source": {"select": {"name": item["Source"]}},
                    "Published": {"date": {"start": item["Published"]}},
                    "Telecom Relevance": {"select": {"name": item["Telecom Relevance"]}},
                    "AI Relevance": {"select": {"name": item["AI Relevance"]}},
                    "Action Signal": {"select": {"name": item["Action Signal"]}},
                    "Vendor Tags": {"multi-select": [{"name": v} for v in item["Vendor Tags"]]},
                    "Cost/Savings Signal": {"rich_text": [{"text": {"content": item["Cost/Savings Signal"]}}] if item["Cost/Savings Signal"] else []},
                    "Time Horizon": {"select": {"name": item["Time Horizon"]}}
                }
            )
    except Exception as e:
        print(f"Notion push failed (non-fatal): {str(e)}")


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        all_headlines = fetch_headlines()

        results = []
        for hl in all_headlines:
            signals = extract_signals_fast(hl["text"])
            if signals["telecom_score"] >= 2 or (signals["telecom_score"] >= 1 and signals["ai_score"] >= 1):
                results.append({
                    "Headline": hl["text"][:200],
                    "Source": hl["source"],
                    "Link": hl["link"],
                    "Published": datetime.now().isoformat(),
                    "Telecom Relevance": "High" if signals["telecom_score"] >= 3 else "Medium",
                    "AI Relevance": "High" if signals["ai_score"] >= 2 else "Low",
                    "Action Signal": "PRIORITIZE" if (signals["telecom_score"] >= 3 and signals["ai_score"] >= 2) else "MONITOR" if signals["telecom_score"] >= 2 else "IGNORE",
                    "Vendor Tags": detect_vendors_fast(hl["text"]),
                    "Cost/Savings Signal": signals["cost_signal"],
                    "Time Horizon": signals["time_horizon"]
                })

        push_to_notion_safe(results)

        body = json.dumps(results).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(body)