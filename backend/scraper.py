from bs4 import BeautifulSoup
import requests
import re
import json
from notion_client import Client
import os
from datetime import datetime

def handler(request):
    # ===== CONFIGURE YOUR SOURCES HERE (TELECOM/AI FOCUS) =====
    KEY_SOURCES = [
        {"name": "LightReading", "url": "https://www.lightreading.com/", "selector": ".article-title a"},
        {"name": "FierceWireless", "url": "https://www.fiercewireless.com/wireless", "selector": ".headline a"},
        {"name": "TelecomTV", "url": "https://www.telecomtv.com/content/", "selector": ".teaser-title a"},
        {"name": "Ars Technica Telecom", "url": "https://arstechnica.com/tag/telecom/", "selector": ".article-header a"},
        {"name": "IEEE ComSoc", "url": "https://comsoc.org/news", "selector": ".news-item h3 a"}
    ]
    # ===== END CONFIG =====

    all_headlines = []
    for source in KEY_SOURCES:
        try:
            response = requests.get(source["url"], headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            for tag in soup.select(source["selector"])[:5]:  # Top 5 per source
                text = tag.get_text(strip=True)
                link = tag.get('href', '')
                if not link.startswith('http'):
                    link = source["url"] + link
                all_headlines.append({"text": text, "link": link, "source": source["name"]})
        except Exception as e:
            print(f"Error scraping {source['name']}: {str(e)}")
            continue

    # Process headlines for signals
    results = []
    for hl in all_headlines:
        signals = extract_signals(hl["text"])
        # Only keep items with meaningful telecom/AI signal (your filter)
        if signals["telecom_score"] >= 2 and signals["ai_score"] >= 1:
            item = {
                "Headline": hl["text"][:200],
                "Source": hl["source"],
                "Published": datetime.now().isoformat(),
                "Telecom Relevance": "High" if signals["telecom_score"] >= 3 else "Medium",
                "AI Relevance": "High" if signals["ai_score"] >= 2 else "Low",
                "Action Signal": "🚨 PRIORITIZE" if (signals["telecom_score"] >= 3 and signals["ai_score"] >= 2) else "📡 MONITOR" if signals["telecom_score"] >= 3 else "📉 IGNORE",
                "Vendor Tags": detect_vendors(hl["text"]),
                "Cost/Savings Signal": signals["cost_signal"],
                "Time Horizon": signals["time_horizon"]
            }
            results.append(item)

    # Push to Notion if credentials exist (optional but recommended)
    push_to_notion(results)
    
    return {
        "statusCode": 200,
        "body": json.dumps(results)
    }

def extract_signals(text):
    text_lower = text.lower()
    
    # Telecom keywords (weighted by your AT&T expertise)
    telecom_keywords = {
        "wifi": 3, "5g": 3, "openran": 3, "ran": 2, "core network": 2, 
        "ont": 2, "olt": 2, "fixed wireless": 2, "small cell": 2, 
        "beamforming": 2, "massive mimo": 2, "network slicing": 3,
        "wifi 6": 3, "wifi 6e": 4, "wifi 7": 4  # Boosted for your specialty
    }
    telecom_score = sum(weight for kw, weight in telecom_keywords.items() if kw in text_lower)
    
    # AI keywords (practical AI focus)
    ai_keywords = {
        "llm": 3, "ml": 2, "inference": 3, "edge ai": 3, "tinyML": 2,
        "anomaly detection": 2, "predictive maintenance": 2, "computer vision": 2,
        "nlp": 2, "reinforcement learning": 1, "ai": 1
    }
    ai_score = sum(weight for kw, weight in ai_keywords.items() if kw in text_lower)
    
    # Cost/savings signals (from your $5M+ budget experience)
    cost_patterns = [
        r'(saved?|reduced?|cut)\s*\$?\d+[\d,.]*(?:\s*(?:million|billion|m|b))?',
        r'(cost\s*(?:savings|reduction|avoidance))\s*\$?\d+[\d,.]*',
        r'(roi|return\s*on\s*investment)\s*\d+%',
        r'(capEx|opex)\s*(?:reduced?|lowered?)\s*\d+%',
        r'(truck\s*rolls?|dispatch)\s*(?:reduced?|lowered?|cut)\s*\d+%'
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

def detect_vendors(text):
    vendors = {
        # ===== TIER 1: WIFI/HOME NETWORKING VENDORS (YOUR CORE AT&T FOCUS - WEIGHT 4) =====
        "airties": "Airties",                    # Home WiFi mesh (critical for your strategy)
        "sagemcom": "Sagemcom",                  # Gateway/AP manufacturer
        "commscope": "CommScope",                # Antennas/cabling for WiFi deployments
        "cisco": "Cisco",                        # Meraki/Enterprise WiFi
        "nokia": "Nokia",                        # WiFi Beacon/Radio Dot
        "ericsson": "Ericsson",                  # Radio Dot System
        "qualcomm": "Qualcomm",                  # WiFi chipsets (QCA9377 etc.)
        "intel": "Intel",                        # WiFi 6E/7 chipsets (AX210)
        "samsung": "Samsung",                    # Networking gear
        "huawei": "Huawei",                      # WiFi APs (despite restrictions)
        "zte": "ZTE",                            # WiFi solutions
        
        # ===== TIER 2: INFRASTRUCTURE/BACKHAUL VENDORS (WEIGHT 3) =====
        "ciena": "Ciena",                        # Optical backhaul (fiber to AP)
        "american tower": "American Tower",      # Tower partner (outdoor WiFi/small cell)
        "crown castle": "Crown Castle",          # Tower partner
        "sba communications": "SBA Communications", # Tower partner
        "echostar": "EchoStar",                  # Satellite backhaul (rural WiFi)
        "globalstar": "Globalstar",              # Satellite (IoT/WiFi hybrid)
        "iridium": "Iridium",                    # Satellite (global WiFi fallback)
        "interdigital": "InterDigital",          # Wireless tech patents (WiFi innovation)
        "lumen technologies": "Lumen Technologies", # Fiber/network services
        "softbank": "SoftBank Corp",             # Telecom arm (5G/WiFi R&D)
        "zte": "ZTE",                            # Already in Tier 1 but kept for coverage
        
        # ===== TIER 3: TELECOM OPERATORS (COMPETITIVE INTELLIGENCE - WEIGHT 2) =====
        # (Formatted as "Vendor Name (Competitor)" for instant recognition in Vendor Tags)
        "softbank group": "SoftBank Group (Competitor)",   # Conglomerate (telecom arm relevant)
        "china mobile": "China Mobile (Competitor)",       # #2 in your list
        "t-mobile us": "T-Mobile US (Competitor)",         # #3
        "verizon": "Verizon (Competitor)",                 # #4
        "at&t": "AT&T (Competitor)",                       # #5 (self-reference for competitive intel)
        "deutsche telekom": "Deutsche Telekom (Competitor)", # #6
        "bharti airtel": "Bharti Airtel (Competitor)",     # #7
        "comcast": "Comcast (Competitor)",                 # #8 (broadband/WiFi competitor)
        "america movil": "América Móvil (Competitor)",     # #12
        "kddi": "KDDI (Competitor)",                       # #13
        "china telecom": "China Telecom (Competitor)",     # #14
        "saudi telecom company": "Saudi Telecom Company (Competitor)", # #15
        "singtel": "Singtel (Competitor)",                 # #16
        "orange": "Orange (Competitor)",                   # #17
        "swisscom": "Swisscom (Competitor)",               # #18
        "emirates telecom": "Emirates Telecom (Etisalat Group) (Competitor)", # #20
        "telstra": "Telstra (Competitor)",                 # #21
        "bt group": "BT Group (Competitor)",               # #29
        "telefonica": "Telefónica (Competitor)",           # #31
        "sk group": "SK Group (Competitor)",               # #32 (Note: Includes SK Telecom)
        "mtn group": "MTN Group (Competitor)",             # #33
        "bce inc": "BCE Inc. (Competitor)",                # #34
        "telenor": "Telenor (Competitor)",                 # #36
        "telia company": "Telia Company (Competitor)",     # #40
        "rogers communications": "Rogers Communications (Competitor)", # #141
        "charter communications": "Charter Communications (Competitor)", # #142
        "kpn": "KPN (Competitor)",                         # #43
        "telus": "Telus (Competitor)",                     # #144
        "telecom italia": "Telecom Italia (Competitor)",   # #47
        "airtel africa": "Airtel Africa (Competitor)",     # #48
        "telkom indonesia": "Telkom Indonesia (Competitor)", # #49
        "vodafone idea": "Vodafone Idea (Competitor)",     # #50
        "true corporation": "True Corporation (Competitor)", # #51
        "sk telecom": "SK Telecom (Competitor)",           # #252
        "millicom": "Millicom (Competitor)",               # #153
        "emirates integrated telecom": "Emirates Integrated Telecommunications Company (Competitor)", # #154
        "etihad etisalat": "Etihad Etisalat (Mobily) (Competitor)", # #155
        "tele2": "Tele2 (Competitor)",                     # #156
        "indus towers": "Indus Towers (Competitor)",       # #57
        "ooredoo qatar": "Ooredoo Qatar (Competitor)",     # #58
        "hong kong telecom": "Hong Kong Telecom (Competitor)", # #159
        "ooredoo": "Ooredoo (Competitor)",                 # #160
        "quebecor": "Quebecor (Competitor)",               # #163
        "far eastone": "Far EasTone (Competitor)",         # #164
        "taiwan mobile": "Taiwan Mobile (Competitor)",     # #66
        "tim s.a.": "TIM S.A. (Competitor)",               # #67
        "sirius xm": "Sirius XM (Competitor)",             # #68 (satellite audio - relevant for in-car WiFi)
        "celcomdigi": "Celcomdigi (Competitor)",           # #69
        "ote group": "OTE Group (Competitor)",             # #70
        "elisa": "Elisa (Competitor)",                     # #76
        "a1 telekom austria": "A1 Telekom Austria (Competitor)", # #77
        "maxis berhad": "Maxis Berhad (Competitor)",       # #278
        "telekom malaysia": "Telekom Malaysia (Competitor)", # #179
        "inwit": "INWIT (Competitor)",                     # #180
        "mobile telesystems": "Mobile TeleSystems (Competitor)", # #82
        "telecom argentina": "Telecom Argentina (Competitor)", # #83
        "tata communications": "Tata Communications (Competitor)", # #284
        "orange polska": "Orange Polska (Competitor)",     # #85
        "zegona communications": "Zegona Communications (Competitor)", # #286
        "pccw": "PCCW (Competitor)",                       # #87
        "tpg telecom": "TPG Telecom (Competitor)",         # #188
        "united internet": "United Internet (Competitor)", # #92
        "turkcell": "Turkcell (Competitor)",               # #93
        "liberty global": "Liberty Global (Competitor)",   # #94
        "turk telekom": "Türk Telekom (Competitor)",       # #295
        "1&1": "1&1 (Competitor)",                         # #96
        "axiata group": "Axiata Group (Competitor)",       # #98
        "telephone and data systems": "Telephone and Data Systems (Competitor)", # #99
        "sunrise communications": "Sunrise Communications AG (Competitor)", # #1100
        "zayo group": "Zayo Group Holdings (Competitor)",  # Bandwidth infra (alternative carriers)
        "8x8": "8x8 Inc. (Competitor)",                    # Cloud comms (alternative carriers)
        "vonage": "Vonage Holdings Corp. (Competitor)",    # Cloud comms (alternative carriers)
        "magicjack": "MagicJack VocalTec Ltd. (Competitor)", # Micro-cap carrier
        "one horizon": "One Horizon Group Inc. (Competitor)", # Micro-cap carrier
        "ooma": "Ooma Inc. (Competitor)",                  # Micro-cap carrier
        
        # ===== YOUR ORIGINAL VENDORS (PRESERVED FOR BACKWARD COMPATIBILITY) =====
        "open source": "Open-Source",
        "vmware": "VMware",
        "red hat": "Red Hat",
        "arcturus": "Arcturus"
    }
    found = []
    text_lower = text.lower()
    for key, vendor in vendors.items():
        if key in text_lower:
            found.append(vendor)
    # Return UNIQUE entries (max 3) – prioritizes Tier 1/2 via natural scoring
    return list(set(found))[:3]


def push_to_notion(results):
    NOTION_TOKEN = os.getenv("NOTION_TOKEN")
    NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
    if not NOTION_TOKEN or not NOTION_DATABASE_ID:
        print("⚠️ Notion credentials not set - skipping Notion push")
        return
    
    try:
        notion = Client(auth=NOTION_TOKEN)
        for item in results:
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
        print(f"✅ Pushed {len(results)} items to Notion")
    except Exception as e:
        print(f"❌ Notion push failed: {str(e)}")
