import os
import discord
from discord.ext import commands
from discord import app_commands, Interaction
from flask import Flask
from threading import Thread

# ─── Flask keep-alive server ───────────────────────────────────────────────
app = Flask('')

@app.route('/')
def home():
    return "Bot attivo."

def run():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run).start()

# ─── Discord bot setup ─────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.wait_until_ready()
    try:
        synced = await bot.tree.sync()
        print(f"[DEBUG] Comandi slash sincronizzati: {len(synced)}")
    except Exception as e:
        print(f"[DEBUG] Errore sincronizzazione: {e}")
    print(f"[DEBUG] Bot connesso come {bot.user}")

# ─── Porto d'armi ──────────────────────────────────────────────────────────
@bot.tree.command(name="esito-porto-armi", description="Invia esito porto d'armi in DM")
@app_commands.describe(
    destinatario="Utente a cui inviare l'esito",
    nome_funzionario="Nome del funzionario",
    esito="Esito della richiesta (ACCOGLIE o RIGETTA)",
    nome_richiedente="Nome del richiedente",
    data_emissione="Data di emissione dell'esito (formato GG/MM/AAAA)"
)
async def esito_porto_armi(
    interaction: Interaction,
    destinatario: discord.User,
    nome_funzionario: str,
    esito: str,
    nome_richiedente: str,
    data_emissione: str
):
    esito = esito.upper()
    if esito not in ["ACCOGLIE", "RIGETTA"]:
        await interaction.response.send_message("❌ L'esito deve essere 'ACCOGLIE' o 'RIGETTA'.", ephemeral=True)
        return

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
        await interaction.response.send_message("❌ Impossibile inviare il messaggio: il destinatario ha i DM chiusi.", ephemeral=True)

# ─── GPG ────────────────────────────────────────────────────────────────────
@bot.tree.command(name="esito-gpg", description="Invia esito GPG in DM")
@app_commands.describe(
    destinatario="Utente a cui inviare l'esito",
    nome_funzionario="Nome del funzionario",
    esito="Esito della richiesta (ACCOGLIE o RIGETTA)",
    nome_richiedente="Nome del richiedente",
    data_emissione="Data di emissione dell'esito (formato GG/MM/AAAA)"
)
async def esito_gpg(
    interaction: Interaction,
    destinatario: discord.User,
    nome_funzionario: str,
    esito: str,
    nome_richiedente: str,
    data_emissione: str
):
    esito = esito.upper()
    if esito not in ["ACCOGLIE", "RIGETTA"]:
        await interaction.response.send_message("❌ L'esito deve essere 'ACCOGLIE' o 'RIGETTA'.", ephemeral=True)
        return

    embed = discord.Embed(
        title="ESITO RICHIESTA GPG",
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
        await interaction.response.send_message("❌ Impossibile inviare il messaggio: il destinatario ha i DM chiusi.", ephemeral=True)

# ─── GRUOP COMMAND ────────────────────────────────────────────────────────────────────

group_id = 8730810
allowed_role_id = 1244221476719296604 

def get_client():
    return Client(cookie="COOKIE") 

async def handle_action(ctx, action_func, action_name, username):
    try:
        await action_func()
        await ctx.send(f"L'utente **{username}** è stato {action_name} correttamente.", ephemeral=True)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            retry_after = int(e.response.headers.get("Retry-After", "5"))
            await ctx.send(
                f"⚠️ Roblox ha bloccato temporaneamente le richieste (rate limit). Riprova tra **{retry_after} secondi**.",
                ephemeral=True
            )
        else:
            await ctx.send(f"❌ Errore HTTP durante l'operazione: `{str(e)}`", ephemeral=True)
    except Exception as e:
        await ctx.send(f"❌ Errore generico durante l'operazione: `{str(e)}`", ephemeral=True)

@slash_command(name="set_group_role", description="Imposta un ruolo specifico a un utente nel gruppo Roblox")
@slash_option(name="username", description="Username dell'utente", required=True, opt_type=OptionType.STRING)
@slash_option(name="rank_id", description="ID del ruolo nel gruppo Roblox", required=True, opt_type=OptionType.INTEGER)
async def set_group_role(ctx: SlashContext, username: str, rank_id: int):
    if allowed_role_id not in [role.id for role in ctx.author.roles]:
        return await ctx.send("⛔ Non hai il permesso per usare questo comando.", ephemeral=True)

    client = get_client()
    user = await client.get_user_by_username(username)
    group = await client.get_group(group_id)

    await handle_action(
        ctx,
        lambda: group.set_rank(user, rank_id),
        f"impostato al ruolo con ID {rank_id}",
        username
    )

@slash_command(name="accept_group", description="Accetta un utente nel gruppo Roblox e assegna 'Porto d'Arma'")
@slash_option(name="username", description="Username dell'utente da accettare", required=True, opt_type=OptionType.STRING)
async def accept_group(ctx: SlashContext, username: str):
    if allowed_role_id not in [role.id for role in ctx.author.roles]:
        return await ctx.send("⛔ Non hai il permesso per usare questo comando.", ephemeral=True)

    client = get_client()
    user = await client.get_user_by_username(username)
    group = await client.get_group(group_id)

    roles = await group.get_roles()
    porto_arma_role = next((r for r in roles if r.name.lower() == "porto d'arma"), None)

    if not porto_arma_role:
        return await ctx.send("❌ Il ruolo 'Porto d'Arma' non è stato trovato nel gruppo Roblox.", ephemeral=True)

    async def accept_and_set_role():
        await group.accept_user(user)
        await group.set_rank(user, porto_arma_role.id)

    await handle_action(ctx, accept_and_set_role, "accettato e assegnato il ruolo 'Porto d'Arma'", username)

@bot.event
async def on_ready():
    await bot.wait_until_ready()
    try:
        await bot.add_cog(GroupManagement(bot))
        synced = await bot.tree.sync()
        print(f"[DEBUG] Comandi sincronizzati: {len(synced)}")
    except Exception as e:
        print(f"[DEBUG] Errore sincronizzazione: {e}")
    print(f"[DEBUG] Bot pronto come {bot.user}")


# ─── Avvio bot ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    token = os.getenv("MINISTERO_TOKEN")
    if token:
        print("[DEBUG] Avvio bot...")
        bot.run(token)
    else:
        print("[DEBUG] Variabile MINISTERO_TOKEN non trovata.")
