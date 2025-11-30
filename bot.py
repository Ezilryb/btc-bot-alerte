import discord
from discord.ext import tasks
import requests
import os

# ================= CONFIGURATION =================
# Ajoute ou retire des lignes très facilement
ALERTES = [
    {"crypto": "bitcoin",      "sym": "BTC",  "palier": 5000, "channel_id": 1441472260757131327},  # salon 1
    {"crypto": "ethereum",     "sym": "ETH",  "palier": 2500,  "channel_id": 1443336254493036554},  # change l'ID
    {"crypto": "solana",       "sym": "SOL",  "palier": 500,  "channel_id": 1443254422204317809},  # change l'ID
    {"crypto": "dogecoin",     "sym": "DOGE", "palier": 0.1,   "channel_id": 1443254795392651305},  # change l'ID
    {"crypto": "bittensor",    "sym": "TAO",  "palier": 50,   "channel_id": 1443336082174513264},  # change l'ID
]

# Stockage du dernier palier franchi pour chaque crypto
derniers_paliers = {item["crypto"]: 0 for item in ALERTES}

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@tasks.loop(seconds=35)
async def check_all_prices():
    try:
        # On récupère tous les prix en une seule requête (plus rapide et moins de rate-limit)
        ids = ",".join(item["crypto"] for item in ALERTES)
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd"
        prices = requests.get(url, timeout=12).json()

        for item in ALERTES:
            crypto = item["crypto"]
            sym = item["sym"]
            prix = prices.get(crypto, {}).get("usd")
            if not prix:
                continue

            palier_actuel = (prix // item["palier"]) * item["palier"]

            # Alerte uniquement à la hausse
            if palier_actuel > derniers_paliers[crypto]:
                channel = client.get_channel(item["channel_id"])
                if channel:
                    await channel.send(
                        f"**{sym} VIENT DE FRANCHIR ${palier_actuel:,}** !\n"
                        f"Prix actuel ≈ ${prix:,.2f}"
                    )
                    derniers_paliers[crypto] = palier_actuel
                    print(f"{sym} → ${palier_actuel:,}")

    except Exception as e:
        print("Erreur lors de la récupération des prix :", e)

@client.event
async def on_ready():
    print(f"Bot multi-crypto connecté : {client.user}")
    if not check_all_prices.is_running():
        check_all_prices.start()

# Lancement
client.run(os.getenv("DISCORD_TOKEN"))
