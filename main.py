import os
import discord
from discord.ext import commands
from discord import app_commands, Interaction
from flask import Flask
from threading import Thread
from ro_py import Client  # pip install ro_py

# ─── Flask keep-alive server ───────────────────────────────────────────────
app = Flask('')

@app.route('/')
def home():
    return "Bot attivo."

def run():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run).start()

# ─── Costanti ───────────────────────────────────────────────────────────────
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE")
group_id = 8730810
PERMESSI_AUTORIZZATI = [1226305676708679740, 1244221458096455730]

# ─── Discord bot setup ──────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ─── Utility ────────────────────────────────────────────────────────────────
def ha_permessi(member):
    return any(role.id in PERMESSI_AUTORIZZATI for role in member.roles)

def get_client():
    return Client(ROBLOX_COOKIE)

async def handle_action(interaction, azione, messaggio_successo, username):
    try:
        await azione()
        await interaction.response.send_message(
            f"✅ Utente **{username}** {messaggio_successo}.", ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(
            f"❌ Errore durante l'esecuzione dell'azione: {e}", ephemeral=True
        )

# ─── Comando: Esito Porto d'Armi ────────────────────────────────────────────
@tree.command(name="esito-porto-armi", description="Invia esito porto d'armi in DM")
@app_commands.describe(
    destinatario="Utente a cui inviare l'esito",
    nome_funzionario="Nome del funzionario",
    esito="Esito della richiesta (ACCOGLIE o RIGETTA)",
    nome_richiedente="Nome del richiedente",
    data_emissione="Data dell'esito (formato GG/MM/AAAA)"
)
async def esito_porto_armi(interaction: Interaction, destinatario: discord.User, nome_funzionario: str, esito: str, nome_richiedente: str, data_emissione: str):
    esito = esito.upper()
    if esito not in ["ACCOGLIE", "RIGETTA"]:
        return await interaction.response.send_message("❌ L'esito deve essere 'ACCOGLIE' o 'RIGETTA'.", ephemeral=True)

    embed = discord.Embed(
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
        await interaction.response.send_message(f"✅ Esito inviato a {destinatario.mention} in DM.", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ Il destinatario ha i DM chiusi.", ephemeral=True)

# ─── Comando: Esito GPG ─────────────────────────────────────────────────────
@tree.command(name="esito-gpg", description="Invia esito GPG in DM")
@app_commands.describe(
    destinatario="Utente a cui inviare l'esito",
    nome_funzionario="Nome del funzionario",
    esito="Esito della richiesta (ACCOGLIE o RIGETTA)",
    nome_richiedente="Nome del richiedente",
    data_emissione="Data dell'esito (formato GG/MM/AAAA)"
)
async def esito_gpg(interaction: Interaction, destinatario: discord.User, nome_funzionario: str, esito: str, nome_richiedente: str, data_emissione: str):
    await esito_porto_armi(interaction, destinatario, nome_funzionario, esito, nome_richiedente, data_emissione)

# ─── Comando: Accept Group ────────────────────────────────────────────────
@tree.command(name="accept_group", description="Accetta un utente nel gruppo Roblox e assegna 'Porto d'Arma'")
@app_commands.describe(username="Username dell'utente da accettare")
async def accept_group(interaction: Interaction, username: str):
    member = interaction.guild.get_member(interaction.user.id)
    if not member or not ha_permessi(member):
        return await interaction.response.send_message("⛔ Non hai il permesso per usare questo comando.", ephemeral=True)

    client = get_client()
    user = await client.get_user_by_username(username)
    group = await client.get_group(group_id)

    roles = await group.get_roles()
    porto_arma_role = next((r for r in roles if r.name.lower() == "porto d'arma"), None)
    if not porto_arma_role:
        return await interaction.response.send_message("❌ Il ruolo 'Porto d'Arma' non è stato trovato.", ephemeral=True)

    async def accept_and_assign():
        await group.accept_user(user)
        await group.set_rank(user, porto_arma_role.id)

    await handle_action(interaction, accept_and_assign, "accettato e assegnato al ruolo 'Porto d'Arma'", username)

# ─── Comando: Set Group Role ──────────────────────────────────────────────
@tree.command(name="set_group_role", description="Imposta un ruolo specifico a un utente nel gruppo Roblox")
@app_commands.describe(username="Username dell'utente", rank_name="Nome del ruolo nel gruppo Roblox")
async def set_group_role(interaction: Interaction, username: str, rank_name: str):
    member = interaction.guild.get_member(interaction.user.id)
    if not member or not ha_permessi(member):
        return await interaction.response.send_message("⛔ Non hai il permesso per usare questo comando.", ephemeral=True)

    client = get_client()
    user = await client.get_user_by_username(username)
    group = await client.get_group(group_id)

    roles = await group.get_roles()
    matching_role = next((r for r in roles if r.name.lower() == rank_name.lower()), None)
    if not matching_role:
        return await interaction.response.send_message(f"❌ Il ruolo '{rank_name}' non è stato trovato nel gruppo.", ephemeral=True)

    await handle_action(interaction, lambda: group.set_rank(user, matching_role.id), f"impostato al ruolo '{matching_role.name}'", username)

# ─── Comando: Kick Group ─────────────────────────────────────────────
@tree.command(name="kick_group", description="Rimuove un utente dal gruppo Roblox")
@app_commands.describe(username="Username dell'utente da rimuovere")
async def kick_group(interaction: Interaction, username: str):
    member = interaction.guild.get_member(interaction.user.id)
    if not member or not ha_permessi(member):
        return await interaction.response.send_message("⛔ Non hai il permesso per usare questo comando.", ephemeral=True)

    client = get_client()
    user = await client.get_user_by_username(username)
    group = await client.get_group(group_id)

    await handle_action(interaction, lambda: group.exile_user(user), "rimosso dal gruppo", username)

# ─── Avvio bot ─────────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    try:
        synced = await tree.sync()
        print(f"[DEBUG] Comandi sincronizzati ({len(synced)}): {[cmd.name for cmd in synced]}")
    except Exception as e:
        print(f"[ERRORE] Sync fallita: {e}")

if __name__ == "__main__":
    token = os.getenv("MINISTERO_TOKEN")
    if token:
        print("[DEBUG] Avvio bot...")
        bot.run(token)
    else:
        print("[DEBUG] Variabile MINISTERO_TOKEN non trovata.")
