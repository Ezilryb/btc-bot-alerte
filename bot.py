import discord
from discord.ext import tasks
import requests
import os

# === CONFIG ===
CHANNEL_ID = 1441472260757131327  # Ton salon
PALIER = 10000
CRYPTO = "bitcoin"
FIAT = "usd"

dernier_palier = 0
intents = discord.Intents.default()
client = discord.Client(intents=intents)

@tasks.loop(seconds=35)
async def check_btc_price():
    global dernier_palier
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={CRYPTO}&vs_currencies={FIAT}"
        r = requests.get(url, timeout=10)
        prix = r.json()[CRYPTO][FIAT]
        palier_actuel = (prix // PALIER) * PALIER
        if palier_actuel > dernier_palier and palier_actuel != dernier_palier:
            channel = client.get_channel(CHANNEL_ID)
            if channel:
                await channel.send(
                    f"🚀 **BITCOIN VIENT DE FRANCHIR ${palier_actuel:,}** !\n"
                    f"Prix actuel ≈ ${prix:,.0f}"
                )
                dernier_palier = palier_actuel
                print(f"Alerte envoyée : ${palier_actuel:,}")
    except Exception as e:
        print(f"Erreur : {e}")

@client.event
async def on_ready():
    print(f"✅ Bot connecté : {client.user}")
    if not check_btc_price.is_running():
        check_btc_price.start()

client.run(os.getenv("DISCORD_TOKEN"))
