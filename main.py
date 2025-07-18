import os
import discord
import aiohttp
from discord.ext import commands
from discord import app_commands, Interaction, Embed, User
from flask import Flask
from threading import Thread
from ro_py import Client
from ro_py.utilities.errors import UserDoesNotExistError

# ─── Flask Keep-Alive ─────────────────────────────────────
app = Flask('')

@app.route('/')
def home():
    return "Bot attivo."

def run():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run).start()

# ─── Costanti e Setup ─────────────────────────────────────
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE")
GROUP_ID = 9927486
PERMESSI_AUTORIZZATI = [1226305676708679740, 1244221458096455730]

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ─── Utility ───────────────────────────────────────────────
def ha_permessi(member):
    return any(role.id in PERMESSI_AUTORIZZATI for role in member.roles)

async def get_user_id(session, username):
    url = f"https://users.roblox.com/v1/usernames/users"
    async with session.post(url, json={"usernames": [username], "excludeBannedUsers": False}) as resp:
        data = await resp.json()
        if data.get("data") and len(data["data"]) > 0:
            return data["data"][0]["id"]
        else:
            return None

async def get_csrf_token(session):
    async with session.post("https://auth.roblox.com/v2/logout") as resp:
        return resp.headers.get("x-csrf-token")

async def handle_action(interaction, func, success_message, username):
    try:
        await func()
        await interaction.response.send_message(f"✅ Utente **{username}** {success_message}.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Errore: {e}", ephemeral=True)

# ─── Comandi di invio esiti ────────────────────────────────
@tree.command(name="esito-porto-armi", description="Invia esito porto d'armi in DM")
@app_commands.describe(
    destinatario="Utente a cui inviare l'esito",
    nome_funzionario="Nome del funzionario",
    esito="Esito (ACCOGLIE o RIGETTA)",
    nome_richiedente="Nome del richiedente",
    data_emissione="Data (formato GG/MM/AAAA)"
)
async def esito_porto_armi(interaction: Interaction, destinatario: User, nome_funzionario: str, esito: str, nome_richiedente: str, data_emissione: str):
    esito = esito.upper()
    if esito not in ["ACCOGLIE", "RIGETTA"]:
        return await interaction.response.send_message("❌ L'esito deve essere 'ACCOGLIE' o 'RIGETTA'.", ephemeral=True)

    embed = Embed(
        title="ESITO RICHIESTA PORTO D'ARMA",
        description=(
            "**VISTO** il regolamento sul rilascio del porto d'armi emesso in data 02/06/2024\n"
            "**VISTO** l'articolo 27 del testo unico delle leggi di pubblica sicurezza\n\n"
            f"Il funzionario **{nome_funzionario}**\n\n"
            f"**{esito}**\n\n"
            f"La richiesta per il porto d'armi del sig. **{nome_richiedente}**.\n\n"
            f"Lì, d'ufficio, il funzionario **{nome_funzionario}**\n"
            f"**{data_emissione}**"
        ),
        color=0x2b2d31
    )
    embed.set_footer(
        text="Sistema di Comunicazioni Dirette – Ministero dell'Interno",
        icon_url=interaction.client.user.avatar.url if interaction.client.user.avatar else None
    )

    try:
        await destinatario.send(embed=embed)
        await interaction.response.send_message(f"✅ Esito inviato a {destinatario.mention}.", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ Il destinatario ha i DM chiusi.", ephemeral=True)

@tree.command(name="esito-gpg", description="Invia esito GPG in DM")
@app_commands.describe(
    destinatario="Utente",
    nome_funzionario="Nome del funzionario",
    esito="ACCOGLIE o RIGETTA",
    nome_richiedente="Nome del richiedente",
    data_emissione="Data (GG/MM/AAAA)"
)
async def esito_gpg(interaction: Interaction, destinatario: User, nome_funzionario: str, esito: str, nome_richiedente: str, data_emissione: str):
    await esito_porto_armi(interaction, destinatario, nome_funzionario, esito, nome_richiedente, data_emissione)

# ─── Comando: Accept Group ─────────────────────────────────
async def roblox_user_exists(username: str) -> int | None:
    url = "https://users.roblox.com/v1/usernames/users"
    payload = {
        "usernames": [username],
        "excludeBannedUsers": False
    }
    headers = {
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            if data["data"]:
                return data["data"][0]["id"]
            return None

@tree.command(name="accept_group", description="Accetta un utente nel gruppo Roblox e assegna il ruolo 'Porto d'Arma'")
@app_commands.describe(username="Username dell'utente Roblox")
async def accept_group(interaction: Interaction, username: str):
    member = interaction.guild.get_member(interaction.user.id)
    if not member or not ha_permessi(member):
        return await interaction.response.send_message("⛔ Non hai il permesso per usare questo comando.", ephemeral=True)

    await interaction.response.defer(ephemeral=True)

    try:
        user_id = await roblox_user_exists(username)
        if not user_id:
            return await interaction.followup.send(f"❌ L'utente **{username}** non esiste su Roblox.", ephemeral=True)

        client = Client(ROBLOX_COOKIE)
        group = await client.get_group(GROUP_ID)
        join_requests = await group.get_join_requests()

        join_user = None
        async for req in join_requests:
            if req.requester.id == user_id:  # ✅ attributo corretto
                join_user = req
                break

        if not join_user:
            return await interaction.followup.send(f"❌ L'utente **{username}** non ha inviato richiesta di accesso al gruppo.", ephemeral=True)

        await group.accept_join_request(user_id)

        roles = await group.get_roles()
        porto_arma_role = next((r for r in roles if r.name.lower() == "porto d'arma"), None)
        if not porto_arma_role:
            return await interaction.followup.send("❌ Ruolo 'Porto d'Arma

# ─── Comando: Kick Group ────────────────────────────────────
@tree.command(name="kick_group", description="Espelle un utente dal gruppo Roblox")
@app_commands.describe(username="Username dell'utente")
async def kick_group(interaction: Interaction, username: str):
    member = interaction.guild.get_member(interaction.user.id)
    if not member or not ha_permessi(member):
        return await interaction.response.send_message("⛔ Non hai il permesso.", ephemeral=True)

    async with aiohttp.ClientSession(cookies={".ROBLOSECURITY": ROBLOX_COOKIE}) as session:
        user_id = await get_user_id(session, username)
        if not user_id:
            return await interaction.response.send_message(f"❌ L'utente Roblox **{username}** non esiste.", ephemeral=True)

        csrf = await get_csrf_token(session)

        async def exile():
            await session.delete(
                f"https://groups.roblox.com/v1/groups/{GROUP_ID}/users/{user_id}",
                headers={"x-csrf-token": csrf}
            )

        await handle_action(interaction, exile, "espulso dal gruppo", username)

# ─── Comando: Set Group Role ───────────────────────────────
@tree.command(name="set_group_role", description="Imposta un ruolo a un utente nel gruppo Roblox")
@app_commands.describe(username="Username Roblox", rank_name="Nome del ruolo")
async def set_group_role(interaction: Interaction, username: str, rank_name: str):
    member = interaction.guild.get_member(interaction.user.id)
    if not member or not ha_permessi(member):
        return await interaction.response.send_message("⛔ Non hai il permesso.", ephemeral=True)

    async with aiohttp.ClientSession(cookies={".ROBLOSECURITY": ROBLOX_COOKIE}) as session:
        user_id = await get_user_id(session, username)
        if not user_id:
            return await interaction.response.send_message(f"❌ Utente Roblox **{username}** non trovato.", ephemeral=True)

        csrf = await get_csrf_token(session)

        async with session.get(f"https://groups.roblox.com/v1/groups/{GROUP_ID}/roles") as r:
            data = await r.json()
            role = next((r for r in data["roles"] if r["name"].lower() == rank_name.lower()), None)
            if not role:
                return await interaction.response.send_message(f"❌ Ruolo '{rank_name}' non trovato nel gruppo.", ephemeral=True)

        async def set_rank():
            await session.patch(
                f"https://groups.roblox.com/v1/groups/{GROUP_ID}/users/{user_id}",
                json={"roleId": role["id"]},
                headers={"x-csrf-token": csrf}
            )

        await handle_action(interaction, set_rank, f"impostato al ruolo '{role['name']}'", username)

# ─── Avvio Bot ──────────────────────────────────────────────
@bot.event
async def on_ready():
    try:
        synced = await tree.sync()
        print(f"[DEBUG] Comandi sincronizzati: {[cmd.name for cmd in synced]}")
    except Exception as e:
        print(f"[ERRORE] Sync fallita: {e}")

if __name__ == "__main__":
    token = os.getenv("MINISTERO_TOKEN")
    if token:
        print("[DEBUG] Avvio bot...")
        bot.run(token)
    else:
        print("[ERRORE] Variabile MINISTERO_TOKEN non trovata.")
