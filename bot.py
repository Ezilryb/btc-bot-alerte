import discord
from discord.ext import tasks, commands
import requests
import os

# ================= CONFIGURATION =================
ALERTES = [
    {"crypto": "bitcoin",      "sym": "BTC", "mention": "@btc", "palier": 10000, "channel_id": 1441472260757131327},
    {"crypto": "ethereum",     "sym": "ETH", "mention": "@eth", "palier": 5000,  "channel_id": 1443336254493036554},
    {"crypto": "solana",       "sym": "SOL", "mention": "@sol", "palier": 1000,  "channel_id": 1443254422204317809},
    {"crypto": "dogecoin",     "sym": "DOGE","mention": "@doge","palier": 500,   "channel_id": 1443254795392651305},
    {"crypto": "bittensor",    "sym": "TAO", "mention": "@tao", "palier": 100,   "channel_id": 1443336082174513264},
]

# Dictionnaire pour retrouver rapidement une crypto via son symbole ou sa mention
CRYPTO_MAP = {}
for item in ALERTES:
    CRYPTO_MAP[item["sym"].lower()] = item
    CRYPTO_MAP[item["mention"].lower()] = item  # permet !price @btc ou !price btc

# Stockage du dernier palier franchi (à la hausse uniquement)
derniers_paliers = {item["crypto"]: 0 for item in ALERTES}

# Bot avec préfixe de commande
intents = discord.Intents.default()
intents.message_content = True  # Important pour lire les commandes
bot = commands.Bot(command_prefix="!", intents=intents)

# ===============================================
# Tâche toutes les 35 secondes : vérification des paliers
# ===============================================
@tasks.loop(seconds=35)
async def check_all_prices():
    try:
        ids = ",".join(item["crypto"] for item in ALERTES)
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd"
        prices = requests.get(url, timeout=12).json()

        for item in ALERTES:
            crypto_id = item["crypto"]
            prix = prices.get(crypto_id, {}).get("usd")
            if not prix:
                continue

            palier_actuel = (prix // item["palier"]) * item["palier"]

            # Alerte seulement à la hausse
            if palier_actuel > derniers_paliers[crypto_id]:
                channel = bot.get_channel(item["channel_id"])
                if channel:
                    prochain_palier = palier_actuel + item["palier"]
                    await channel.send(
                        f"{item['mention']} **{item['sym']} VIENT DE FRANCHIR ${palier_actuel:,} !**\n"
                        f"Prix actuel ≈ **${prix:,.2f}** | Prochain palier : ${prochain_palier:,}"
                    )
                    derniers_paliers[crypto_id] = palier_actuel
                    print(f"[ALERTE] {item['sym']} → ${palier_actuel:,}")

    except Exception as e:
        print("Erreur API CoinGecko :", e)

# ===============================================
# Commande !price ou !prix
# ===============================================
@bot.command(aliases=["prix", "price", "p"])
async def prix(ctx, *, crypto: str):
    crypto = crypto.strip().lower()
    item = CRYPTO_MAP.get(crypto)

    if not item:
        await ctx.send("❌ Crypto non trouvée. Utilise : `btc`, `eth`, `sol`, `doge`, `tao` ou leurs @")
        return

    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={item['crypto']}&vs_currencies=usd"
        prix = requests.get(url, timeout=10).json()
        prix_usd = prix[item["crypto"]]["usd"]

        palier_actuel = (prix_usd // item["palier"]) * item["palier"]
        prochain = palier_actuel + item["palier"]
        manque = prochain - prix_usd

        await ctx.send(
            f"{item['mention']} **{item['sym']}**\n"
            f"Prix actuel : **${prix_usd:,.2f}**\n"
            f"Palier actuel : ${palier_actuel:,}\n"
            f"Prochain palier : ${prochain:,} (il manque ~${manque:,.0f})"
        )
    except:
        await ctx.send("⚠️ Erreur lors de la récupération du prix.")

# ===============================================
# Démarrage du bot
# ===============================================
@bot.event
async def on_ready():
    print(f"Bot connecté → {bot.user}")
    if not check_all_prices.is_running():
        check_all_prices.start()

# Lancement
bot.run(os.getenv("DISCORD_TOKEN"))
