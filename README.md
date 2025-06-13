# Discord JobBot

A feature-rich Discord bot for finding, managing, and applying to jobs via the Adzuna API and other job boards like Agentur für Arbeit, IHK, and Honeypot. The bot supports job searching, job saving, PDF export, OpenAI-powered summarization, and automated email application sending.

---

## 🧩 Features

- 🔍 Job search via Adzuna API, Agentur, Honeypot, and IHK
- 💾 Save jobs to favorites
- 📤 Apply to jobs via email with auto-generated PDF
- 📄 Export job details as a summarized PDF (OpenAI powered)
- 🧹 Clear job messages with `/clear_chat`
- 📅 Schedule daily job searches
- ✉️ Send test job applications
- 🔧 Full configuration via slash commands

---

## 🛠 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Jokr02/discord-jobbot.git
cd discord-jobbot
```

### 2. Setup Python Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Create Necessary Files

- `.env` – environment secrets and API keys
- `config.json` – search parameters
- `saved_jobs.json` – saved job storage
- `anschreiben_vorlage.txt` – cover letter template
- PDF files: `lebenslauf.pdf`, `zeugnisse.pdf`

### 4. Run the Bot
```bash
python bot.py
```

---

## 📁 Directory Structure

```
discord-jobbot/
│
├── bot.py                  # Main bot logic
├── config.json             # Search configuration
├── saved_jobs.json         # Saved jobs storage
├── .env                    # API keys & secrets
├── lebenslauf.pdf          # Resume PDF
├── zeugnisse.pdf           # Certificates PDF
├── anschreiben_vorlage.txt # Cover letter template
├── saved_pdfs/             # Exported job PDFs
└── logs/                   # Daily logs
```

---

## ⚙️ Configuration

### `.env` sample

```
DISCORD_BOT_TOKEN=your_discord_token
DISCORD_GUILD_ID=your_guild_id
DISCORD_CHANNEL_ID=your_channel_id

ERROR_WEBHOOK_URL=https://discord.com/api/webhooks/...
JOB_WEBHOOK_URL=https://discord.com/api/webhooks/...

SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your@email.com
SMTP_PASSWORD=your_password
SENDER_NAME=Max Mustermann

ADZUNA_APP_ID=your_adzuna_id
ADZUNA_APP_KEY=your_adzuna_key
ADZUNA_COUNTRY=de

OPENAI_MODEL=gpt-4o
OPENAI_API_KEY=your_openai_key
```

### `config.json` sample

```json
{
  "location": "Berlin",
  "radius": 50,
  "keywords": ["linux", "python"],
  "work_type": "all",
  "execution_time": "12:00"
}
```

### `saved_jobs.json` (example)
```json
[
  {
    "id": "123456",
    "title": "Linux Admin",
    "company": "Example AG",
    "location": "Berlin",
    "url": "https://..."
  }
]
```

---

## 💬 Commands

| Command | Description |
|--------|-------------|
| `/favorites` | Show saved jobs |
| `/update_config` | Change search parameters |
| `/config` | Show current search config |
| `/set_time` | Set daily job search time |
| `/search_jobs_days` | Search for jobs from the last X days |
| `/search_jobs_dropdown` | Search jobs via dropdown selector |
| `/clear_favorites` | Remove all saved jobs |
| `/send_testmail` | Send a test application |
| `/clear_chat` | Delete previous bot messages |

---

## 🤖 Usage Notes

- PDF generation uses OpenAI to summarize job descriptions
- Email applications include attachments and custom cover letter
- Ensure all required files and secrets are present

---

## 📬 License

MIT — use freely, but give credit :)
