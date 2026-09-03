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
        # Indonesian
        "butuh website",
        "butuh jasa website",
        "mau bikin website",
        "ingin membuat website",
        "cari web developer",
        "butuh web developer",
        "ada yang bisa bantu buat website",
        "website saya error",
        "website bermasalah",
        "butuh redesign website",
        "ingin redesign website",

        # English
        "need a website",
        "need a web developer",
        "looking for a web developer",
        "looking for a website developer",
        "looking for someone to build a website",
        "need help with my website",
        "need help with website",
        "website not working",
        "website is broken",
        "website needs improvement",
        "need website redesign",
        "need an ecommerce website",
        "need a landing page",
    ],

    "software_app": [
        # Indonesian
        "butuh aplikasi",
        "ingin membuat aplikasi",
        "butuh software",
        "butuh sistem",
        "butuh sistem informasi",
        "butuh aplikasi web",
        "cari developer",
        "cari programmer",
        "cari vendor IT",
        "butuh jasa IT",
        "mencari partner IT",
        "mencari vendor IT",

        # English
        "need an app",
        "need a mobile app",
        "looking for an app developer",
        "looking for a software developer",
        "looking for software development",
        "need software development",
        "need software developed",
        "need custom software",
        "need a web application",
        "need a SaaS developer",
        "looking for a development company",
    ],

    "agency_outsource": [
        # Indonesian
        "butuh agency",
        "cari agency",
        "butuh vendor",
        "cari vendor",
        "butuh bantuan IT",
        "mencari partner IT",
        "mencari agency IT",
        "butuh outsourcing IT",
        "cari partner untuk project",
        "butuh partner development",

        # English
        "need an agency",
        "looking for an agency",
        "looking for an IT company",
        "looking for an IT agency",
        "looking for a development agency",
        "looking for a technology partner",
        "looking for a development partner",
        "looking for an outsourcing partner",
        "need an outsourcing company",
        "looking for a software company",
    ],

    "automation_ai_data": [
        # Indonesian
        "butuh automation",
        "butuh otomatisasi",
        "butuh sistem otomatis",
        "butuh chatbot",
        "butuh AI",
        "butuh solusi AI",
        "butuh dashboard",
        "butuh data dashboard",
        "butuh integrasi API",
        "butuh data integration",
        "ingin otomatisasi bisnis",
        "ingin membuat chatbot",

        # English
        "need automation",
        "need workflow automation",
        "looking for automation developer",
        "need business automation",
        "need AI automation",
        "looking for an AI solution",
        "need an AI solution",
        "need a chatbot",
        "need a business chatbot",
        "need a dashboard",
        "need a data dashboard",
        "need data automation",
        "need data integration",
        "need API integration",
        "looking for an automation developer",
    ],

    "infrastructure_maintenance": [
        # Indonesian
        "butuh hosting",
        "cari hosting",
        "butuh VPS",
        "cari VPS",
        "butuh server",
        "butuh cloud",
        "butuh cloud hosting",
        "butuh bantuan hosting",
        "website tidak bisa",
        "website error",
        "website rusak",
        "butuh maintenance website",
        "butuh perbaikan website",
        "butuh migrasi website",
        "butuh migrasi server",
        "butuh backup data",
        "butuh database",
        "database bermasalah",

        # English
        "need hosting",
        "looking for hosting",
        "need a VPS",
        "looking for a VPS",
        "need cloud hosting",
        "need server setup",
        "need cloud deployment",
        "need help with hosting",
        "website not working",
        "website broken",
        "need website maintenance",
        "need website fixed",
        "need website migration",
        "need server migration",
        "need database help",
        "database problem",
        "need backup",
        "need technical support",
    ]
}

BLOCKED_KEYWORDS = [
    "india",
    "indian",
    "pakistan",
    "pakistani"
]

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
        elif platform == "x":
            queries.append(f'"{keyword}" site:x.com')

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

    # Filter blocked keywords once
    filtered_keywords = [
        keyword
        for keyword in all_keywords
        if not any(
            blocked.lower() in keyword.lower()
            for blocked in BLOCKED_KEYWORDS
        )
    ]

    print(f"\n🔑 Total keywords: {len(all_keywords)}")
    print(f"🚫 Blocked keywords: {len(all_keywords) - len(filtered_keywords)}")
    print(f"📚 Keyword groups: {len(KEYWORDS)}")

    platforms = [
        "linkedin",
        "facebook",
        "threads",
        "x"
    ]

    all_candidates = []

    for platform in platforms:

        print("\n" + "-" * 70)
        print(f"🔎 Scanning platform: {platform.upper()}")
        print("-" * 70)

        results = collect_candidate_posts(
            filtered_keywords,
            platform=platform
        )

        if results:
            print(
                f"✅ {platform.upper()}: "
                f"{len(results)} candidate posts"
            )
            all_candidates.extend(results)
        else:
            print(
                f"⚠️ {platform.upper()}: "
                f"No candidate posts found"
            )

    print("\n" + "=" * 70)
    print("📊 FINAL COLLECTION RESULT")
    print("=" * 70)
    print(f"Total candidate posts collected: {len(all_candidates)}")

    if all_candidates:

        send_to_n8n_webhook(
            all_candidates,
            use_test_webhook=False
        )

    else:
        print(
            "⚠️ No candidate posts were collected. "
            "Please check search parameters or API key."
        )