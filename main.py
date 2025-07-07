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

# ✅ /pec
class PecForm(ui.Modal, title="Invio Comunicazione PEC"):
    contenuto = ui.TextInput(
        label="✒️ Contenuto del messaggio",
        style=TextStyle.paragraph,
        placeholder="Testo completo della comunicazione",
        required=True
    )
    firma = ui.TextInput(
        label="Firma (es. Grado e Nome)",
        style=TextStyle.short,
        placeholder="Es: Funzionario supercaccola2",
        required=True
    )

    def __init__(self, destinatario: discord.Member):
        super().__init__()
        self.destinatario = destinatario

    async def on_submit(self, interaction: Interaction):
        embed = discord.Embed(
            title="PEC UFFICIALE",
            description=(
                "**Ministero dell'Interno**\n\n"
                f"{self.contenuto.value.strip()}\n\n"
                f"—\n*{self.firma.value.strip()}*"
            ),
            color=discord.Color.dark_blue()
        )
        embed.set_footer(
            text="Sistema di Comunicazioni Dirette – Ministero dell'Interno",
            icon_url=interaction.client.user.avatar.url  # Logo del bot
        )

        try:
            await self.destinatario.send(embed=embed)
            await interaction.response.send_message("PEC inviata correttamente via DM.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("L'utente ha i DM disattivati.", ephemeral=True)

@bot.tree.command(name="pec", description="Invia una comunicazione ufficiale in DM.")
@app_commands.describe(destinatario="Utente destinatario della PEC")
async def pec(interaction: Interaction, destinatario: discord.Member):
    RUOLI_AUTORIZZATI = [1244227229496643677]
    if not any(r.id in RUOLI_AUTORIZZATI for r in interaction.user.roles):
        await interaction.response.send_message("Non hai i permessi per usare questo comando.", ephemeral=True)
        return

    await interaction.response.send_modal(PecForm(destinatario))


if __name__ == "__main__":
    token = os.getenv("MINISTERO_TOKEN")
    if token:
        print("[DEBUG] Avvio bot...")
        bot.run(token)
    else:
        print("[DEBUG] Variabile MINISTERO_TOKEN non trovata.")
