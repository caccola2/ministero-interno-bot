import os
import discord
from discord.ext import commands
from discord import app_commands, ui, Interaction, TextStyle
from flask import Flask
from threading import Thread
import unicodedata

app = Flask('')

@app.route('/')
def home():
    return "Bot attivo."

def run():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run).start()

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

# PORTO D'ARMA ESITO

@bot.tree.command(name="esito-porto-armi", description="Invia esito porto d'armi in DM")
@app_commands.describe(
    destinatario="Utente a cui inviare l'esito",
    nome_funzionario="Nome del funzionario",
    esito="Esito della richiesta (ACCOGLIE o RIGETTA)",
    nome_richiedente="Nome del richiedente",
    data_emissione="Data di emissione dell'esito (formato GG/MM/AAAA)"
)
async def esito_portodarma(
    interaction: discord.Interaction,
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



if __name__ == "__main__":
    token = os.getenv("MINISTERO_TOKEN")
    if token:
        print("[DEBUG] Avvio bot...")
        bot.run(token)
    else:
        print("[DEBUG] Variabile MINISTERO_TOKEN non trovata.")
