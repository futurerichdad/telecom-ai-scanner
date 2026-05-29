from bs4 import BeautifulSoup
import requests
import re
import json
import os
from datetime.datetime import now

def handler(request):
    # ===== TELECOM/AI SOURCES (YOUR FOCUS) =====
    KEY_SOURCES = [
        {"name": "LightReading", "url": "https://www.lightreading.com/", "selector": ".article-title a"},
        {"name": "FierceWireless", "url": "https://www.fiercewireless.com/wireless", "selector": ".headline a"},
        {"name": "TelecomTV", "url": "https://www.telecomtv.com/content/", "selector": ".teaser-title a"},
        {"name": "Ars Technica Telecom", "url": "https://arstechnica.com/tag/telecom/", "selector": ".article-header a"},
        {"name": "IEEE ComSoc", "url": "https://comsoc.org/news", "selector": ".news-item h3 a"}
    ]
    
    all_headlines = []
    for source in KEY_SOURCES:
        try:
            # Critical: Add timeout and user-agent to avoid Vercel blocks
            response = requests.get(
                source["url"], 
                headers={"User-Agent": "TelecomAIScanner/1.0 (+https://vercel.com)"}, 
                timeout=15
            )
            soup = BeautifulSoup(response.content, 'html.parser')
            for tag in soup.select(source["selector"])[:3]:  # Reduced to 3 for speed
                text = tag.get_text(strip=True)
                link = tag.get('href', '')
                if not link.startswith('http'):
                    link = source["url"] + link
                all_headlines.append({"text": text, "link": link, "source": source["name"]})
        except Exception as e:
            print(f"⚠️  Skipping {source['name']}: {str(e)}")
            continue

    # Process headlines (optimized for speed)
    results = []
    for hl in all_headlines[:10]:  # Max 10 results to avoid timeout
        signals = extract_signals_fast(hl["text"])
        if signals["telecom_score"] >= 2 and signals["ai_score"] >= 1:
            results.append({
                "Headline": hl["text"][:200],
                "Source": hl["source"],
                "Published": now().isoformat(),
                "Telecom Relevance": "High" if signals["telecom_score"] >= 3 else "Medium",
                "AI Relevance": "High" if signals["ai_score"] >= 2 else "Low",
                "Action Signal": "🚨 PRIORITIZE" if (signals["telecom_score"] >= 3 and signals["ai_score"] >= 2) else "📡 MONITOR" if signals["telecom_score"] >= 3 else "📉 IGNORE",
                "Vendor Tags": detect_vendors_fast(hl["text"]),
                "Cost/Savings Signal": signals["cost_signal"],
                "Time Horizon": signals["time_horizon"]
            })
    
    # Push to Notion (if configured)
    push_to_notion_safe(results)
    
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(results)
    }

# ===== OPTIMIZED HELPERS (NO EXTERNAL DEPS BEYOND REQUIREMENTS.TXT) =====
def extract_signals_fast(text):
    text_lower = text.lower()
    
    # Telecom keywords (prioritizing YOUR WiFi expertise)
    telecom_keywords = {
        "wifi": 3, "5g": 3, "openran": 3, "ran": 2, "core network": 2, 
        "ont": 4, "olt": 4, "fixed wireless": 2, "small cell": 2, 
        "beamforming": 2, "massive mimo": 2, "network slicing": 3,
        "wifi 6": 3, "wifi 6e": 4, "wifi 7": 4  # YOUR SPECIALTY
    }
    telecom_score = sum(weight for kw, weight in telecom_keywords.items() if kw in text_lower)
    
    # AI keywords (practical focus)
    ai_keywords = {
        "llm": 3, "ml": 2, "inference": 3, "edge ai": 3, "tinyML": 2,
        "anomaly detection": 2, "predictive maintenance": 2, "computer vision": 2,
        "nlp": 2, "reinforcement learning": 1
    }
    ai_score = sum(weight for kw, weight in ai_keywords.items() if kw in text_lower)
    
    # Cost/savings signals (from your $5M+ budget work)
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
    
    # Time horizon (your 3-5yr roadmap lens)
    time_horizon = "Near-Term"
    if any(term in text_lower for term in ["2025", "2026", "long-term", "roadmap", "3-5 year"]):
        time_horizon = "Long-Term"
    elif any(term in text_lower for term in ["2024", "Q1", "Q2", "H1", "H2", "pilot", "trial", "launch"]):
        time_horizon = "Near-Term"
    else:
        time_horizon = "Mid-Term"
    
    return {
        "telecom_score": telecom_score,
        "ai_score": ai_score,
        "cost_signal": cost_signal,
        "time_horizon": time_horizon
    }

def detect_vendors_fast(text):
    vendors = {
        # YOUR CORE WIFI VENDORS (TIER 1)
        "airties": "Airties", "sagemcom": "Sagemcom", "commscope": "CommScope",
        "cisco": "Cisco", "nokia": "Nokia", "ericsson": "Ericsson",
        "qualcomm": "Qualcomm", "intel": "Intel", "samsung": "Samsung",
        "huawei": "Huawei", "zte": "ZTE",
        
        # INFRASTRUCTURE (TIER 2)
        "ciena": "Ciena", "american tower": "American Tower", 
        "crown castle": "Crown Castle", "sba communications": "SBA Communications",
        "echostar": "EchoStar", "globalstar": "Globalstar", "iridium": "Iridium",
        
        # COMPETITORS (TIER 3 - LABELED FOR CLARITY)
        "verizon": "Verizon (Competitor)", "at&t": "AT&T (Competitor)",
        "t-mobile": "T-Mobile US (Competitor)", "deutsche telekom": "Deutsche Telekom (Competitor)",
        "china mobile": "China Mobile (Competitor)", "orange": "Orange (Competitor)",
        "vodafone": "Vodafone (Competitor)", "telefonica": "Telefónica (Competitor)",
        "bt group": "BT Group (Competitor)", "kpn": "KPN (Competitor)",
        "telus": "Telus (Competitor)", "telstra": "Telstra (Competitor)",
        "softbank": "SoftBank Corp (Competitor)",  # Telecom arm
        
        # YOUR ORIGINALS
        "open source": "Open-Source", "vmware": "VMware", 
        "red hat": "Red Hat", "arcturus": "Arcturus"
    }
    found = []
    text_lower = text.lower()
    for key, vendor in vendors.items():
        if key in text_lower:
            found.append(vendor)
    return list(set(found))[:3]  # Max 3 vendors

def push_to_notion_safe(results):
    NOTION_TOKEN = os.getenv("NOTION_TOKEN")
    NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
    if not NOTION_TOKEN or not NOTION_DATABASE_ID:
        return  # Silently fail if not configured (avoids crashing)
    
    try:
        from notion_client import Client
        notion = Client(auth=NOTION_TOKEN)
        for item in results[:5]:  # Max 5 items to avoid timeout
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
        print(f"⚠️  Notion push failed (non-fatal): {str(e)}")
