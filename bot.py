import discord
from discord.ext import commands
from discord import app_commands, Interaction, ButtonStyle
from discord.ui import Button, View
import requests
import json
import os
from dotenv import load_dotenv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from fpdf import FPDF

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")
DISCORD_GUILD_ID = os.getenv("DISCORD_GUILD_ID")
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SENDER_NAME = os.getenv("SENDER_NAME")
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")
ADZUNA_COUNTRY = os.getenv("ADZUNA_COUNTRY", "de")
ERROR_WEBHOOK_URL = os.getenv("ERROR_WEBHOOK_URL")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

user_data_path = "user_data"
os.makedirs(user_data_path, exist_ok=True)

def get_user_file(user_id):
    return os.path.join(user_data_path, f"{user_id}.json")

def save_user_data(user_id, data):
    with open(get_user_file(user_id), 'w') as f:
        json.dump(data, f)

def load_user_data(user_id):
    path = get_user_file(user_id)
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    else:
        return {
            "location": "",
            "radius": 10,
            "keywords": [],
            "contract_type": "",
            "working_model": "",
            "favorites": []
        }

@tree.command(name="set_parameters", description="Set job search parameters")
@app_commands.describe(
    location="City or area",
    radius="Radius in km",
    keywords="Comma-separated job titles",
    contract_type="permanent or temporary",
    working_model="remote, onsite, hybrid"
)
async def set_parameters(interaction: Interaction, location: str, radius: int, keywords: str, contract_type: str, working_model: str):
    data = load_user_data(interaction.user.id)
    data.update({
        "location": location,
        "radius": radius,
        "keywords": [k.strip() for k in keywords.split(',')],
        "contract_type": contract_type,
        "working_model": working_model
    })
    save_user_data(interaction.user.id, data)
    await interaction.response.send_message("Parameters saved.", ephemeral=True)

@tree.command(name="search_jobs", description="Search for jobs with saved parameters")
async def search_jobs(interaction: Interaction):
    user_id = interaction.user.id
    data = load_user_data(user_id)
    adzuna_jobs = fetch_adzuna_jobs(data)
    arbeitsagentur_jobs = fetch_arbeitsagentur_jobs(data)
    jobs = (adzuna_jobs or []) + (arbeitsagentur_jobs or [])

    if not jobs:
        await interaction.response.send_message("No jobs found.", ephemeral=True)
        return

    for job in jobs[:5]:
        view = View()
        btn = Button(label="Favorite", style=ButtonStyle.primary)

        async def favorite_callback(i: Interaction, job=job):
            d = load_user_data(user_id)
            d['favorites'].append(job)
            save_user_data(user_id, d)
            await i.response.send_message("Job added to favorites.", ephemeral=True)

        btn.callback = favorite_callback
        view.add_item(btn)

        await interaction.channel.send(
            f"**{job['title']}**\n{job['location']}\n{job['description'][:200]}...",
            view=view
        )
    await interaction.response.send_message("Jobs listed above.", ephemeral=True)

def fetch_adzuna_jobs(params):
    url = f"https://api.adzuna.com/v1/api/jobs/{ADZUNA_COUNTRY}/search/1"
    query = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "results_per_page": 5,
        "what": ' '.join(params['keywords']),
        "where": params['location'],
        "distance": params['radius'],
        "contract_type": params['contract_type']
    }
    response = requests.get(url, params=query)
    if response.status_code == 200:
        data = response.json()
        return [
            {
                "title": j['title'],
                "location": j['location']['display_name'],
                "description": j['description'],
                "company": j.get('company', {}).get('display_name', ''),
                "url": j['redirect_url']
            } for j in data.get('results', [])
        ]
    return []

def fetch_arbeitsagentur_jobs(params):
    try:
        base_url = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs"
        headers = {"Accept": "application/json"}
        query = {
            "page": 1,
            "pav": "false",
            "umkreis": params['radius'],
            "arbeitsort": params['location'],
            "was": ' '.join(params['keywords'])
        }
        response = requests.get(base_url, headers=headers, params=query)
        if response.status_code == 200:
            data = response.json()
            return [
                {
                    "title": j['titel'],
                    "location": j['arbeitsort'],
                    "description": j.get('refnr'),
                    "company": j.get('arbeitgeber'),
                    "url": f"https://jobboerse.arbeitsagentur.de/vamJB/startseite.html?refnr={j.get('refnr')}"
                } for j in data.get('stellenangebote', [])
            ]
    except Exception as e:
        if ERROR_WEBHOOK_URL:
            requests.post(ERROR_WEBHOOK_URL, json={"content": f"Arbeitsagentur API Error: {str(e)}"})
    return []

@tree.command(name="favorites", description="Show favorite jobs")
async def favorites(interaction: Interaction):
    data = load_user_data(interaction.user.id)
    favs = data.get('favorites', [])
    if not favs:
        await interaction.response.send_message("No favorites yet.", ephemeral=True)
        return

    for idx, job in enumerate(favs):
        view = View()

        async def delete_callback(i: Interaction, idx=idx):
            d = load_user_data(interaction.user.id)
            del d['favorites'][idx]
            save_user_data(interaction.user.id, d)
            await i.response.send_message("Favorite deleted.", ephemeral=True)

        async def apply_callback(i: Interaction, job=job):
            try:
                send_application(job)
                await i.response.send_message("Application sent.", ephemeral=True)
            except Exception as e:
                if ERROR_WEBHOOK_URL:
                    requests.post(ERROR_WEBHOOK_URL, json={"content": f"Error: {str(e)}"})
                await i.response.send_message("Failed to send application.", ephemeral=True)

        view.add_item(Button(label="Delete", style=ButtonStyle.danger, callback=delete_callback))
        view.add_item(Button(label="Apply", style=ButtonStyle.success, callback=apply_callback))

        await interaction.channel.send(
            f"**{job['title']}**\n{job['location']}\n{job['url']}",
            view=view
        )
    await interaction.response.send_message("Favorites listed.", ephemeral=True)

@tree.command(name="debug_guild_id", description="Zeigt deine GUILD-ID")
async def debug_guild_id(interaction: Interaction):
    await interaction.response.send_message(f"Guild ID: `{interaction.guild_id}`", ephemeral=True)

def send_application(job):
    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = SMTP_USER
    msg['Subject'] = f"Application for {job['title']}"

    with open("anschreiben_vorlage.txt", "r") as f:
        text = f.read().replace("{{job_title}}", job['title']).replace("{{sender_name}}", SENDER_NAME)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in text.splitlines():
        pdf.cell(200, 10, txt=line, ln=True)
    pdf_path = "anschreiben.pdf"
    pdf.output(pdf_path)

    msg.attach(MIMEText("Please find my application attached.", 'plain'))

    for file in [pdf_path, "lebenslauf.pdf", "zeugnisse.pdf"]:
        with open(file, "rb") as f:
            part = MIMEApplication(f.read(), Name=os.path.basename(file))
            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file)}"'
            msg.attach(part)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
@tree.command(name="ping", description="Antwortet mit Pong!")
async def ping(interaction: Interaction):
    await interaction.response.send_message("Pong!", ephemeral=True)

@bot.event
async def on_ready():
    guild_id = os.getenv("DISCORD_GUILD_ID")
    if guild_id:
        guild = discord.Object(id=int(guild_id))
        synced = await tree.sync(guild=guild)
        print(f"Synchronized {len(synced)} commands with guild {guild_id}")
    else:
        synced = await tree.sync()
        print(f"Synchronized {len(synced)} global commands")

    print(f"Bot logged in as {bot.user}")
    channel_id = os.getenv("DISCORD_CHANNEL_ID")
    if channel_id:
        channel = bot.get_channel(int(channel_id))
        if channel:
            await channel.send("✅ Der Bot ist jetzt online und bereit.")


bot.run(DISCORD_TOKEN)
