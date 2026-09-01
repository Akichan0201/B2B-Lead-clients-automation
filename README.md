# B2B Lead Intelligence System — Stage 1A Baseline Pipeline

An automated public lead discovery pipeline that searches for B2B client intent posts across social platforms (LinkedIn, Facebook, Threads) and web search indexes, normalizes candidate data, relays it to n8n via Production Webhook, and appends raw collected posts to **Google Sheets (`lead_posts_raw`)**.

---

## 🏗️ Active Stage 1A Architecture

```text
Host / Terminal (python trigger_scan.py)
   │
   ├──> Query Python Microservice (POST http://localhost:8000/api/v1/collect)
   │        └── Searches Serper/Google index for target keywords on LinkedIn, Facebook & Threads
   │
   └──> Relay Candidates Payload ──> n8n Production Webhook (POST /webhook/trigger-lead-scan)
                                             │
                                             ▼
                                     [n8n Code Node]
                                  (Split candidates into 1 item per post)
                                             │
                                             ▼
                                  [n8n Google Sheets Node]
                                (Append rows to 'lead_posts_raw')
```

---

## 📁 Repository Structure

```text
d:/02. STUDY/Client Lead Automation/
├── docker-compose.yml                      # Docker services (postgres, python_collector, n8n)
├── schema.sql                              # PostgreSQL DDL schema & keyword catalog
├── .env.example                            # Safe template for environment variables
├── .gitignore                              # Git exclusion rules
├── n8n_stage1a_webhook_to_sheets.json      # Active Stage 1A n8n workflow JSON (Import to n8n)
├── trigger_scan.py                         # Host CLI script to trigger multi-platform collection
├── python_service/
│   ├── Dockerfile                          # Container setup for Python microservice
│   ├── main.py                             # FastAPI collector application (/health, /api/v1/collect)
│   └── requirements.txt                    # Python dependencies (FastAPI, uvicorn, pydantic, requests)
└── README.md                               # Project documentation
```

---

## ⚙️ Requirements & Dependencies

### Docker Container Dependencies (Python Microservice)
- `fastapi`
- `uvicorn`
- `pydantic`
- `requests`

### Host Machine CLI Dependencies (`trigger_scan.py`)
- Python 3.9+
- `requests` (`pip install requests`)

---

## 🚀 Environment Setup & Deployment

### 1. Configure `.env`
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Configure your secrets in `.env`:
```env
SEARCH_API_KEY=your_serper_api_key_here
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
POSTGRES_DB=lead_intelligence
POSTGRES_PORT=5432
PYTHON_COLLECTOR_URL=http://localhost:8000
N8N_WEBHOOK_URL=https://adzkiaalma.app.n8n.cloud/webhook/trigger-lead-scan
```

### 2. Start Services with Docker Compose
```bash
docker compose up -d --build
```

Services running:
- **Python Collector**: `http://localhost:8000` (Health: `GET /health`, Collector: `POST /api/v1/collect`)
- **n8n Instance**: `http://localhost:5678` (Local container)
- **PostgreSQL**: `localhost:5432`

### 3. Setup n8n Production Webhook & Google Sheets
1. Open n8n Dashboard.
2. Import `n8n_stage1a_webhook_to_sheets.json`.
3. Configure your Google Sheets credential in n8n and set the target document ID & sheet name (`lead_posts_raw`).
4. Activate the Workflow!

---

## 🔍 How to Run the Discovery Pipeline

Run `trigger_scan.py` from your terminal:
```bash
python trigger_scan.py
```

Execution flow:
1. Validates Python Collector health on `http://localhost:8000/health`.
2. Queries LinkedIn, Facebook, and Threads for 50+ intent keywords.
3. Receives normalized candidate objects (text, URL, author, matched keywords, SHA-256 text hash).
4. Relays candidate payload to n8n Webhook.
5. n8n splits payload into distinct items and appends them to Google Sheets (`lead_posts_raw`).

---

## 🎯 Supported Platforms & Keyword Categories

### Target Platforms (Public Indexed Posts)
- **LinkedIn** (`site:linkedin.com/posts`)
- **Facebook** (`site:facebook.com`)
- **Threads** (`site:threads.net`)

### Active Keyword Groups
- **`website`**: `"butuh website"`, `"need a web developer"`, `"looking for website developer"`
- **`software`**: `"butuh aplikasi"`, `"cari programmer"`, `"looking for software agency"`
- **`agency_outsource`**: `"butuh agency"`, `"mencari partner IT"`, `"looking for IT company"`
- **`problem_intent`**: `"website bermasalah"`, `"butuh redesign website"`, `"need help with website"`
- **`hiring_intent`**: `"butuh bantuan untuk"`, `"siapa yang bisa bantu"`, `"recommend web developer"`

---

## 🔒 Security & Environment Variables

- `.env` contains actual secret keys and passwords and is excluded from Git via `.gitignore`.
- `.env.example` provides a clean template with dummy placeholders.
- `n8n_stage1a_webhook_to_sheets.json` contains no embedded API keys or passwords.

---

## 🔮 Planned / Future Stages (Roadmap)

The following capabilities are architected for subsequent stages and are **NOT** active in Stage 1A:
- **Stage 1B**: Gemini AI Lead Qualification (BUYER vs PROVIDER & AGENCY vs HR JOB discrimination).
- **Stage 1C**: Lead Scoring Engine (0–100 score calculation & HOT/WARM/COLD temperature assignment).
- **Stage 1D**: PostgreSQL Lead Warehouse Persistence.
- **Stage 1E**: Multi-tier Deduplication (PostgreSQL SHA-256 hash & URL matching).
- **Stage 2**: Automated Follow-up & Outreach Sequences (WhatsApp, Email, Telegram, Calendar Booking).
