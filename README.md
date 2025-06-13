## JobBot - Discord Job Search Bot

JobBot is a feature-rich Discord bot that automatically fetches job listings from various sources, displays them in a Discord channel, and allows for interaction, filtering, saving, and even application preparation.

---

### 🌟 Features

* Scheduled job search via Adzuna, Honeypot, IHK, Joblift
* Manual job search via `/search_jobs_days`
* Save favorites with buttons and manage via `/favourites`
* One-click PDF export for saved jobs
* Email application preparation with preview
* OpenAI-powered job description summarization
* Kununu rating integration (⭐ shown in job postings)
* Configurable work type filter via `/update_work_type`
* Clear chat with `/clear_chat`
* Admin commands for updating config and testing

---

### 📂 Project Structure

```
/opt/discord-jobbot/
├── bot.py                # Main bot file
├── config.json           # Job search config
├── saved_jobs.json       # Stored favorites
├── saved_pdfs/           # Exported job PDFs
├── .env                  # Secrets and API keys
├── requirements.txt      # Python dependencies
```

---

### ⚙️ Setup Instructions

1. **Clone or copy the bot files** into your desired directory.
2. **Install dependencies**:

```bash
pip install -r requirements.txt
```

3. **Create a `.env` file** with the following keys:

```env
DISCORD_BOT_TOKEN=your_discord_token
DISCORD_GUILD_ID=your_guild_id
DISCORD_CHANNEL_ID=channel_id_for_jobs
ERROR_WEBHOOK_URL=your_error_webhook
JOB_WEBHOOK_URL=webhook_for_job_posts

SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=you@example.com
SMTP_PASSWORD=yourpassword
SENDER_NAME=JobBot

ADZUNA_APP_ID=...
ADZUNA_APP_KEY=...
ADZUNA_COUNTRY=de

OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o
```

4. **Set up `config.json`**:

```json
{
  "location": "Berlin",
  "radius": 50,
  "keywords": ["linux", "python"],
  "work_type": "remote"
}
```

5. **Start the bot**:

```bash
python bot.py
```

---

### 🤖 Usage Overview

* `/search_jobs_days tage:3` ➔ Fetch jobs from last 3 days
* `/favourites` ➔ Show saved jobs with action buttons
* `/update_config` ➔ Update search location, radius, keywords
* `/update_work_type` ➔ Set preferred work type (onsite/hybrid/remote)
* `/clear_chat` ➔ Removes old job messages from chat
* Buttons:

  * "⭐ Speichern" to save job
  * "📄 PDF exportieren" to generate a job summary
  * "✉ Bewerbung vorbereiten" if company email is available

---

### 🔹 Kununu Integration

Jobs now include an optional line:

```
✨ Kununu-Rating: ⭐ 3.9/5
```

This is fetched live and displayed in the job embed using company name normalization.

---

### ☕ Contribution

Feel free to open an issue or fork the repo and add features!

---

### ⚠️ Notes

* Make sure all `.env` variables are correctly set.
* OpenAI API key must have access to the model you use (`gpt-4o` recommended).
* Discord slash commands may require a few minutes to sync on first launch.

---

**Enjoy automated job hunting with JobBot!**
