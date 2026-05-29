from http.server import BaseHTTPRequestHandler
from bs4 import BeautifulSoup
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import re
import json
import os

KEY_SOURCES = [
    {"name": "LightReading", "url": "https://www.lightreading.com/", "selector": ".article-title a"},
    {"name": "FierceWireless", "url": "https://www.fiercewireless.com/wireless", "selector": ".headline a"},
    {"name": "TelecomTV", "url": "https://www.telecomtv.com/content/", "selector": ".teaser-title a"},
    {"name": "Ars Technica Telecom", "url": "https://arstechnica.com/tag/telecom/", "selector": ".article-header a"},
    {"name": "IEEE ComSoc", "url": "https://comsoc.org/news", "selector": ".news-item h3 a"}
]


def fetch_source(source):
    try:
        response = requests.get(
            source["url"],
            headers={"User-Agent": "TelecomAIScanner/1.0 (+https://vercel.com)"},
            timeout=5
        )
        soup = BeautifulSoup(response.content, 'lxml')
        headlines = []
        for tag in soup.select(source["selector"])[:3]:
            text = tag.get_text(strip=True)
            link = tag.get('href', '')
            if not link.startswith('http'):
                link = source["url"] + link
            headlines.append({"text": text, "link": link, "source": source["name"]})
        return headlines
    except Exception as e:
        print(f"Skipping {source['name']}: {str(e)}")
        return []


def extract_signals_fast(text):
    text_lower = text.lower()
    telecom_keywords = {
        "wifi": 3, "5g": 3, "openran": 3, "ran": 2, "core network": 2,
        "ont": 4, "olt": 4, "fixed wireless": 2, "small cell": 2,
        "beamforming": 2, "massive mimo": 2, "network slicing": 3,
        "wifi 6": 3, "wifi 6e": 4, "wifi 7": 4
    }
    telecom_score = sum(weight for kw, weight in telecom_keywords.items() if kw in text_lower)

    ai_keywords = {
        "llm": 3, "ml": 2, "inference": 3, "edge ai": 3, "tinyml": 2,
        "anomaly detection": 2, "predictive maintenance": 2, "computer vision": 2,
        "nlp": 2, "reinforcement learning": 1
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
        "red hat": "Red Hat"
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
        all_headlines = []

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(fetch_source, source): source for source in KEY_SOURCES}
            for future in as_completed(futures):
                all_headlines.extend(future.result())

        results = []
        for hl in all_headlines[:10]:
            signals = extract_signals_fast(hl["text"])
            if signals["telecom_score"] >= 2 and signals["ai_score"] >= 1:
                results.append({
                    "Headline": hl["text"][:200],
                    "Source": hl["source"],
                    "Published": datetime.now().isoformat(),
                    "Telecom Relevance": "High" if signals["telecom_score"] >= 3 else "Medium",
                    "AI Relevance": "High" if signals["ai_score"] >= 2 else "Low",
                    "Action Signal": "PRIORITIZE" if (signals["telecom_score"] >= 3 and signals["ai_score"] >= 2) else "MONITOR" if signals["telecom_score"] >= 3 else "IGNORE",
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