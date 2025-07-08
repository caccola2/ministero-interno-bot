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

# /pec

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
        title="PEC UFFICIALE",
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

    embed.set_footer(text="Sistema di Comunicazioni Dirette – Ministero dell'Interno")
    embed.set_thumbnail(url="https://images-ext-1.discordapp.net/external/xGLWVd2zFMgVyzlmlOftc5PQKUO7tz7vq5GnBWqNThQ/%3Fformat%3Dwebp%26quality%3Dlossless%26width%3D706%26height%3D706/https/images-ext-1.discordapp.net/external/YQkJmHL1IFP5GQs6M_v-wnUCdYAS860VpUDrLqQSKxc/%253Fformat%253Dwebp%2526quality%253Dlossless%2526width%253D565%2526height%253D565/https/images-ext-1.discordapp.net/external/po18tbb9zrjuaU74rCFYf9FsOwn0cmlrE1MOpxtgNPA/%25253Fsize%25253D4096/https/cdn.discordapp.com/icons/1244219836574208080/9ef51275997c0ecac492c9581d98ac37.png?format=webp&quality=lossless&width=530&height=530")

    try:
        await destinatario.send(embed=embed, file=file)
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
