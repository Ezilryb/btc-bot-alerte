import discord
from discord.ext import tasks
import requests
import os

# ================= CONFIGURATION =================
# Ajoute ou retire des lignes très facilement
# Ajoutez l'ID du rôle pour chaque crypto (obtenez-le via Discord : Paramètres serveur > Rôles > Copier ID)
ALERTES = [
    {"crypto": "bitcoin",      "sym": "BTC",  "palier": 1000, "channel_id": 1441472260757131327, "role_id": 1443999707423703252},  # Remplacez par l'ID réel du rôle (ex. "btc-alert")
    {"crypto": "ethereum",     "sym": "ETH",  "palier": 1000,  "channel_id": 1443336254493036554, "role_id": 1444000028287832205},  # Remplacez par l'ID réel
    {"crypto": "solana",       "sym": "SOL",  "palier": 500,  "channel_id": 1443254422204317809, "role_id": 1444000115277828157},  # Remplacez par l'ID réel
    {"crypto": "dogecoin",     "sym": "DOGE", "palier": 0.1,   "channel_id": 1443254795392651305, "role_id": 1444000201743401081},  # Remplacez par l'ID réel
    {"crypto": "bittensor",    "sym": "TAO",  "palier": 100,   "channel_id": 1443336082174513264, "role_id": 1444000642648510595},  # Remplacez par l'ID réel
]

# Stockage du dernier palier franchi pour chaque crypto
derniers_paliers = {item["crypto"]: 0 for item in ALERTES}

intents = discord.Intents.default()
client = discord.Client(intents=intents)

async def initialize_paliers():
    try:
        ids = ",".join(item["crypto"] for item in ALERTES)
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd"
        prices = requests.get(url, timeout=12).json()

        for item in ALERTES:
            crypto = item["crypto"]
            prix = prices.get(crypto, {}).get("usd")
            if not prix:
                print(f"Pas de prix pour {crypto}")
                continue
            palier_actuel = (prix // item["palier"]) * item["palier"]
            derniers_paliers[crypto] = palier_actuel
            print(f"Initialisé {item['sym']} à ${palier_actuel:,.2f} (prix actuel: ${prix:,.2f})")

    except Exception as e:
        print("Erreur lors de l'initialisation des paliers :", e)

@tasks.loop(seconds=35)
async def check_all_prices():
    try:
        ids = ",".join(item["crypto"] for item in ALERTES)
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd"
        prices = requests.get(url, timeout=12).json()

        for item in ALERTES:
            crypto = item["crypto"]
            sym = item["sym"]
            prix = prices.get(crypto, {}).get("usd")
            if not prix:
                print(f"Pas de prix pour {crypto}")
                continue

            palier_actuel = (prix // item["palier"]) * item["palier"]
            print(f"Check {sym}: prix ${prix:,.2f}, palier_actuel ${palier_actuel:,.2f}, dernier ${derniers_paliers[crypto]:,.2f}")

            channel = client.get_channel(item["channel_id"])
            if channel:
                role_mention = ""
                if "role_id" in item and item["role_id"]:
                    role = channel.guild.get_role(item["role_id"])
                    if role:
                        role_mention = f"{role.mention} "
                    else:
                        print(f"Rôle non trouvé pour {sym} (ID: {item['role_id']})")

                if palier_actuel > derniers_paliers[crypto]:
                    # Alerte à la hausse
                    threshold = palier_actuel
                    await channel.send(
                        f"{role_mention}**{sym} VIENT DE FRANCHIR ${threshold:,.2f}** !\n"
                        f"Prix actuel ≈ ${prix:,.2f}"
                    )
                    derniers_paliers[crypto] = palier_actuel
                    print(f"{sym} ↑ ${threshold:,.2f} - Alerte envoyée !")

                elif palier_actuel < derniers_paliers[crypto]:
                    # Alerte à la baisse
                    threshold = palier_actuel + item["palier"]
                    await channel.send(
                        f"{role_mention}**{sym} VIENT DE PASSER EN DESSOUS DE ${threshold:,.2f}** !\n"
                        f"Prix actuel ≈ ${prix:,.2f}"
                    )
                    derniers_paliers[crypto] = palier_actuel
                    print(f"{sym} ↓ ${threshold:,.2f} - Alerte envoyée !")
                
                else:
                    print(f"{sym} : Pas de changement de palier")

            else:
                print(f"Channel non trouvé pour {sym} (ID: {item['channel_id']})")

    except Exception as e:
        print("Erreur lors de la récupération des prix :", e)

@client.event
async def on_ready():
    print(f"Bot multi-crypto connecté : {client.user}")
    await initialize_paliers()
    
    # Test d'envoi de message dans chaque channel pour vérifier les permissions
    for item in ALERTES:
        channel = client.get_channel(item["channel_id"])
        if channel:
            await channel.send(f"Test: Bot ready for {item['sym']} - Vérifiez si ce message apparaît !")
            print(f"Test message envoyé pour {item['sym']} dans channel {item['channel_id']}")
        else:
            print(f"Impossible d'envoyer test pour {item['sym']} : Channel non trouvé")
    
    if not check_all_prices.is_running():
        check_all_prices.start()

# Lancement
client.run(os.getenv("DISCORD_TOKEN"))
