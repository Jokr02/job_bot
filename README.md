# 🛠️ Discord JobBot – Automated Job Search & Email Applications

The **Discord JobBot** searches for IT jobs daily based on your keywords and location, posts them directly to a Discord channel, and lets you **send full applications via button click** — including PDF cover letter, resume and references.

---

## 🚀 Features

- 🔍 Daily automated job search from sources like Adzuna and StepStone
- 💬 Send application emails from Discord with one click
- 📝 Dynamic PDF cover letter based on a text template
- 📎 Attach resume (PDF), certificates (PDF), and letter
- 💾 Save jobs to favorites or export them
- 🗓 Schedule job search time via Slash command
- ⚙️ Adjust location, radius and keywords at runtime
- 🔐 SMTP support (Gmail etc.), no cloud dependency
- 📄 Logging with rotation

---

## ⚙️ Setup

### 1. Clone or download

```bash
git clone https://github.com/Jokr02/job_bot.git
cd discord-jobbot
```

### 2. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Create `.env` file

```env
DISCORD_BOT_TOKEN=your_discord_token
DISCORD_CHANNEL_ID=123456789012345678

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your.email@gmail.com
SMTP_PASSWORD=your_app_password
SENDER_NAME=John Doe
```

### 4. Create a cover letter template

**Filename:** `anschreiben_vorlage.txt`

```txt
Application for {{job_title}}

Dear Sir or Madam,

I hereby apply for the position of {{job_title}}.

Sincerely,  
{{sender_name}}
```

You can customize the content. The variables `{{job_title}}` and `{{sender_name}}` will be replaced dynamically.

---

## 🧪 Run & test

```bash
python bot.py
```

Or run it as a system service or cron job.

---

## 💬 Available Slash Commands

| Command             | Description                                     |
|---------------------|-------------------------------------------------|
| `/favorites`         | Shows saved jobs with email action buttons      |
| `/clear_favorites`  | Deletes all saved jobs                          |
| `/export_favorites` | Exports saved jobs as CSV                       |
| `/set_time`         | Sets the daily search time (e.g. `12:00`)       |
| `/set_parameters`   | Sets location, radius and keywords              |
| `/send_testmail`    | Sends a test email with your attachments        |

---

## 📁 Example directory

```bash
discord-jobbot/
├── bot.py
├── anschreiben_vorlage.txt
├── lebenslauf.pdf
├── zeugnisse.pdf
├── .env
├── config.json
├── saved_jobs.json
├── jobs_seen.json
```

---

## 🛡️ GDPR/Privacy Notice

This bot runs **entirely on your own infrastructure**. No data is stored in the cloud. Applications are only sent when you manually confirm the action via Discord.

---

## 💬 Contact

Open an issue or reach out via Discord. Good luck with your job hunt! 🚀
