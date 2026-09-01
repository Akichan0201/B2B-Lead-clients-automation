#!/usr/bin/env python3
"""
STAGE 1A: Multi-Platform Lead Discovery CLI Trigger
--------------------------------------------------
Flow:
1. Python Collector runs public post search (/api/v1/collect)
2. Receives candidate posts across platforms (LinkedIn, Facebook, Threads)
3. Forwards exact payload to n8n Webhook
4. n8n normalizes items and appends to Google Sheets (lead_posts_raw)
"""

import os
import sys
import requests

# Base Service Configuration
PYTHON_SERVICE_URL = os.getenv("PYTHON_SERVICE_URL", "http://localhost:8000")

# n8n Webhook Endpoints
N8N_WEBHOOK_URL = os.getenv(
    "N8N_WEBHOOK_URL",
    "https://adzkiaalma.app.n8n.cloud/webhook/trigger-lead-scan"
)
N8N_TEST_WEBHOOK_URL = os.getenv(
    "N8N_TEST_WEBHOOK_URL",
    "https://adzkiaalma.app.n8n.cloud/webhook-test/trigger-lead-scan"
)

KEYWORDS = {
    "website": [
        "butuh website",
        "butuh jasa website",
        "mau bikin website",
        "cari web developer",
        "butuh web developer",
        "ada yang bisa bantu buat website",
        "need a website",
        "need a web developer",
        "looking for web developer",
        "looking for website developer",
        "looking for someone to build a website",
    ],
    "software": [
        "butuh aplikasi",
        "butuh developer",
        "butuh software",
        "butuh sistem informasi",
        "cari developer",
        "cari programmer",
        "cari vendor IT",
        "butuh jasa IT",
        "looking for software developer",
        "looking for software agency",
        "need software developer",
        "need software agency",
    ],
    "agency_outsource": [
        "butuh agency",
        "cari agency",
        "butuh vendor",
        "cari vendor",
        "butuh bantuan IT",
        "mencari partner IT",
        "mencari agency IT",
        "need an agency",
        "looking for an agency",
        "looking for IT company",
        "looking for IT agency",
        "looking for development agency",
    ],
    "problem_intent": [
        "website saya error",
        "website bermasalah",
        "butuh redesign website",
        "ingin redesign website",
        "website tidak bisa",
        "butuh dibuatkan sistem",
        "ingin membuat aplikasi",
        "ingin membuat website",
        "need help with website",
        "website needs improvement",
        "need website redesign",
    ],
    "hiring_intent": [
        "butuh orang untuk",
        "butuh bantuan untuk",
        "cari orang untuk",
        "ada yang bisa bantu",
        "siapa yang bisa bantu",
        "recommend web developer",
        "recommend website developer",
        "looking for someone",
        "need someone to",
        "can someone help",
    ]
}

def get_all_keywords():
    """Combine all keyword groups into a deduplicated list."""
    keywords = []
    for group_keywords in KEYWORDS.values():
        for keyword in group_keywords:
            if keyword not in keywords:
                keywords.append(keyword)
    return keywords

def check_python_service():
    """Check if Python microservice is online."""
    print("\n🔎 Checking Python Collector status...")
    try:
        response = requests.get(f"{PYTHON_SERVICE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Python Collector Microservice is ONLINE (Port 8000)")
            return True
        print(f"❌ Python service returned HTTP {response.status_code}")
        return False
    except Exception as e:
        print("❌ Python Collector is OFFLINE!")
        print(f"   Error details: {e}")
        return False

def collect_candidate_posts(keywords, platform):
    """Query search API via Python Microservice for a specific platform."""
    print("\n" + "=" * 70)
    print(f"🔍 Searching {platform.upper()}")
    print("=" * 70)

    queries = []
    for keyword in keywords:
        if platform == "linkedin":
            queries.append(f'"{keyword}" site:linkedin.com/posts')
        elif platform == "facebook":
            queries.append(f'"{keyword}" site:facebook.com')
        elif platform == "threads":
            queries.append(f'"{keyword}" site:threads.net')

    payload = {
        "platform": platform,
        "keywords": keywords,
        "queries": queries,
        "max_results": 20
    }

    try:
        response = requests.post(
            f"{PYTHON_SERVICE_URL}/api/v1/collect",
            json=payload,
            timeout=60
        )

        if response.status_code != 200:
            print(f"❌ Collector error: HTTP {response.status_code}")
            print(response.text)
            return []

        data = response.json()
        candidates = data.get("candidates", [])
        print(f"✅ {platform.upper()}: {len(candidates)} candidate post(s) found")
        return candidates

    except Exception as e:
        print(f"❌ Error searching {platform}: {e}")
        return []

def send_to_n8n_webhook(candidates, use_test_webhook=False):
    """Relay candidate posts to n8n Webhook."""
    if not candidates:
        print("\n⚠️ No candidates to send to n8n.")
        return False

    target_url = N8N_TEST_WEBHOOK_URL if use_test_webhook else N8N_WEBHOOK_URL

    print("\n" + "=" * 70)
    print("🚀 Sending candidate posts to n8n Webhook...")
    print("=" * 70)
    print(f"Target URL: {target_url}")
    print(f"Total candidates: {len(candidates)}")

    platform_count = {}
    for candidate in candidates:
        platform = candidate.get("platform", "unknown")
        platform_count[platform] = platform_count.get(platform, 0) + 1

    print("\n📊 Platform Summary:")
    for platform, count in platform_count.items():
        print(f"   - {platform.upper()}: {count} post(s)")

    webhook_payload = {
        "source": "python_collector",
        "total_candidates": len(candidates),
        "keyword_groups": list(KEYWORDS.keys()),
        "candidates": candidates
    }

    try:
        response = requests.post(target_url, json=webhook_payload, timeout=30)
        if response.status_code in [200, 201]:
            print("\n✅ Successfully delivered to n8n!")
            print(f"HTTP {response.status_code}")
            print(f"n8n Response: {response.text}")
            return True

        print(f"\n❌ n8n returned HTTP {response.status_code}")
        print(response.text)
        return False

    except Exception as e:
        print("\n❌ Failed to connect to n8n:")
        print(e)
        return False

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print(" STAGE 1A: MULTI-PLATFORM LEAD DISCOVERY ")
    print(" Python Collector → n8n → Google Sheets ")
    print("=" * 70)

    if not check_python_service():
        sys.exit(1)

    all_keywords = get_all_keywords()
    print(f"\n🔑 Total keywords: {len(all_keywords)}")
    print(f"📚 Keyword groups: {len(KEYWORDS)}")

    platforms = ["linkedin", "facebook", "threads"]
    all_candidates = []

    for platform in platforms:
        candidates = collect_candidate_posts(all_keywords, platform)
        all_candidates.extend(candidates)

    print("\n" + "=" * 70)
    print("📊 FINAL COLLECTION RESULT")
    print("=" * 70)
    print(f"Total candidate posts collected: {len(all_candidates)}")

    if all_candidates:
        send_to_n8n_webhook(all_candidates, use_test_webhook=False)
    else:
        print("\n⚠️ No candidate posts found.")
        print("Check keywords, search API key, or collector configuration.")