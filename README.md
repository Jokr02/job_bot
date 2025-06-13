# 🤖 Discord JobBot

A Discord bot that searches for job offers from multiple platforms, allows saving favorites, generates PDFs with AI summaries, and supports daily automated searches.

---

## 🚀 Features

- `/search_jobs_days days:X` – fetch jobs from the past `X` days
- `/favorites` – view your saved jobs (with PDF export and apply prep)
- 📄 Export job ads as individual PDFs
- ✉️ AI-generated job summaries using OpenAI
- 📬 Daily automated job search based on `config.json`
- 🧹 `/clear_chat` command to clean up test messages
- 🔐 Configurable via `.env` and `config.json`

---

## 🗂️ Folder Structure
```
discord-jobbot/
├── bot.py # Main bot script
├── config.json # Bot & search settings
├── saved_jobs.json # Saved jobs (favorites)
├── saved_pdfs/ # Generated job PDFs
├── .env # Environment variables
├── requirements.txt # Python dependencies
```
## 🛠️ Installation

### 1. Clone the repo

```bash
git clone https://github.com/Jokr02/discord-jobbot.git
cd discord-jobbot
```
2. Install dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
3. Create .env
Create a file called .env in the project root:

```env
DISCORD_TOKEN=your_discord_bot_token
DISCORD_CHANNEL_ID=1234567890
JOB_WEBHOOK_URL=https://discord.com/api/webhooks/...
ERROR_WEBHOOK_URL=https://discord.com/api/webhooks/...
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-3.5-turbo
```
⚙️ Configuration
Edit config.json:

```json
{
  "location": "Erfurt",
  "radius": 20,
  "keywords": ["Python", "Entwickler"],
  "daily_search_time": "09:00"
}
```
▶️ Running the Bot
```bash
python bot.py
```
Make sure the bot has:

Message Content Intent enabled in the Discord Developer Portal

Necessary permissions in your server (Send Messages, Manage Messages, Use Slash Commands)

📌 Slash Commands
/search_jobs_days days:X – find jobs from the past X days

/favorites – show saved jobs with action buttons

/clear_chat – remove bot messages from channel

📦 Export Options
Save jobs as favorites

Export each as a detailed PDF with AI summary

AI summarizes:

Job tasks

Required qualifications

Company overview

🧠 AI Integration
Uses OpenAI's GPT (gpt-3.5-turbo, gpt-4o, etc.)

Summary is generated from scraped job page content

Make sure your API key has sufficient quota

📋 TODO / Ideas
Export all favorites as ZIP

Multi-language support

OAuth login for LinkedIn or StepStone API (future)

📄 License
MIT – feel free to use and improve this bot.

🤝 Contributions
Pull requests are welcome! For major changes, please open an issue first to discuss your idea.
