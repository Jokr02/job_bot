# 💼 Discord JobBot – Modular Edition

Ein automatisierter Discord-Bot, der täglich oder manuell nach neuen IT-Jobs sucht (Adzuna API) und diese in einem Kanal postet. Bewerbungen können direkt über Discord per Button versendet werden. Modular aufgebaut für einfache Erweiterbarkeit.

---

## 🚀 Features

- 🔍 **Jobsuche** via Adzuna (andere APIs erweiterbar)
- 🕐 **Stündliche Jobsuche** + `/search_jobs_days`
- 💬 Slash-Commands & Discord UI Buttons
- 💾 Jobs speichern, löschen, exportieren
- 📤 Bewerbung per E-Mail mit PDF-Anschreiben & Zeugnissen
- 📎 PDF-Generierung aus Textvorlage (`anschreiben_vorlage.txt`)
- 🧹 Automatische Löschung alter Discord-Nachrichten (>30 Tage)
- 📡 Fehler- & Healthcheck via Discord Webhook
- 🔌 Modularer Aufbau (`core/`, `commands/`, `ui/`)

---

## 🧩 Projektstruktur

```bash
discord-jobbot/
├── bot.py                  # Startpunkt des Bots
├── config.json             # Keywords, Ort, Radius etc.
├── .env                    # API-Keys, Tokens, SMTP etc.
├── core/
│   ├── jobs.py             # Adzuna API Jobsuche + Loop
│   ├── config_utils.py     # Konfiguration lesen/schreiben
│   ├── emailer.py          # Bewerbung versenden
│   ├── pdf_generator.py    # PDF-Anschreiben erstellen
│   ├── logging.py          # Logging + Webhook
│   └── cleanup.py          # Alte Nachrichten löschen
├── ui/
│   └── views.py            # Discord Buttons (Bewerben / Löschen)
├── commands/
│   └── jobs.py             # Slash-Commands wie /search_jobs_days
├── data/
│   └── saved_jobs.json     # Gespeicherte Favoriten
```

---

## ⚙️ Einrichtung

### 1. Repository klonen

```bash
git clone https://github.com/DEIN_USERNAME/discord-jobbot.git
cd discord-jobbot
```

### 2. Abhängigkeiten installieren

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. `.env` Datei anlegen

```env
DISCORD_BOT_TOKEN=your_discord_token
DISCORD_CHANNEL_ID=123456789012345678
ERROR_WEBHOOK_URL=https://discord.com/api/webhooks/...

ADZUNA_APP_ID=your_adzuna_id
ADZUNA_APP_KEY=your_adzuna_key
ADZUNA_COUNTRY=de

SENDER_NAME=Max Mustermann
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_USER=your@email.com
SMTP_PASSWORD=yourpassword
```

---

## 💬 Befehle

| Befehl               | Beschreibung                                  |
|----------------------|-----------------------------------------------|
| `/search_jobs`       | Startet Jobsuche manuell                      |
| `/search_jobs_days`  | Suche nach Jobs der letzten X Tage           |
| `/favorites`         | Zeigt gespeicherte Jobs                       |
| `/clear_favorites`   | Löscht alle gespeicherten Jobs                |
| `/export_favorites`  | Exportiert gespeicherte Jobs als CSV          |

---

## 📄 Beispiel: Anschreiben-Vorlage

Datei: `anschreiben_vorlage.txt`

```txt
Bewerbung als {{job_title}}

Sehr geehrte Damen und Herren,
...

Mit freundlichen Grüßen
{{sender_name}}
```

---

## 🧪 Starten

```bash
python bot.py
```

---

## ✅ To-Do & Erweiterungen

- [x] Kununu-Bewertung integrieren
- [ ] Weitere APIs: Agentur für Arbeit, Stepstone
- [ ] UI: Bewerbungsvorschau oder Ranking
- [ ] Web-GUI zur Konfiguration

---

MIT License © 2025
