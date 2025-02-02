import disnake
from disnake.ext import commands
import requests
import matplotlib.pyplot as plt
import io
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

bot = commands.Bot(
    command_prefix="!",
    intents=disnake.Intents.all(),
    activity=disnake.Game(name="/help for crypto info!")
)

COINGECKO_URL = "https://api.coingecko.com/api/v3"

async def get_crypto_data(crypto_id):
    """Fetch cryptocurrency data from CoinGecko API"""
    try:
        response = requests.get(
            f"{COINGECKO_URL}/coins/{crypto_id}",
            params={"localization": "false", "tickers": "false", "community_data": "false"}
        )
        return response.json()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

class CurrencyConverter(disnake.ui.View):
    """Interactive currency converter buttons"""
    def __init__(self, crypto_id, original_currency):
        super().__init__(timeout=60)
        self.crypto_id = crypto_id
        self.original_currency = original_currency
        self.currencies = ["usd", "eur", "btc", "eth"]

    async def update_price(self, interaction: disnake.Interaction, currency):
        data = await get_crypto_data(self.crypto_id)
        if not data:
            return await interaction.response.send_message("Failed to fetch data", ephemeral=True)
        
        price = data["market_data"]["current_price"][currency]
        embed = interaction.message.embeds[0]
        embed.description = f"**1 {data['symbol'].upper()}** = {price:.4f} {currency.upper()}"
        await interaction.response.edit_message(embed=embed)

    @disnake.ui.button(label="USD", style=disnake.ButtonStyle.primary)
    async def usd_button(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        await self.update_price(interaction, "usd")

    @disnake.ui.button(label="EUR", style=disnake.ButtonStyle.primary)
    async def eur_button(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        await self.update_price(interaction, "eur")

    @disnake.ui.button(label="BTC", style=disnake.ButtonStyle.primary)
    async def btc_button(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        await self.update_price(interaction, "btc")

    @disnake.ui.button(label="ETH", style=disnake.ButtonStyle.primary)
    async def eth_button(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        await self.update_price(interaction, "eth")

@bot.slash_command(name="price", description="Get current cryptocurrency price")
async def price(
    interaction: disnake.ApplicationCommandInteraction,
    crypto: str = commands.Param(description="Cryptocurrency symbol (e.g., bitcoin)"),
    currency: str = commands.Param(default="usd", description="Currency to display price in")
):
    await interaction.response.defer()
    data = await get_crypto_data(crypto)
    
    if not data:
        return await interaction.edit_original_message(content="❌ Cryptocurrency not found!")
    
    embed = disnake.Embed(
        title=f"{data['name']} ({data['symbol'].upper()}) Price",
        color=0x00ff00 if data["market_data"]["price_change_percentage_24h"] >= 0 else 0xff0000,
        timestamp=datetime.utcnow()
    )
    embed.set_thumbnail(url=data["image"]["small"])
    embed.add_field(
        name="Current Price",
        value=f"{data['market_data']['current_price'][currency]} {currency.upper()}",
        inline=False
    )
    embed.add_field(
        name="24h Change",
        value=f"{data['market_data']['price_change_percentage_24h']:.2f}%",
        inline=True
    )
    embed.set_footer(text="Data from CoinGecko")
    
    view = CurrencyConverter(crypto, currency)
    await interaction.edit_original_message(embed=embed, view=view)

@bot.slash_command(name="market", description="Get market details for a cryptocurrency")
async def market(
    interaction: disnake.ApplicationCommandInteraction,
    crypto: str = commands.Param(description="Cryptocurrency symbol (e.g., bitcoin)")
):
    await interaction.response.defer()
    data = await get_crypto_data(crypto)
    
    if not data:
        return await interaction.edit_original_message(content="❌ Cryptocurrency not found!")
    
    embed = disnake.Embed(
        title=f"{data['name']} Market Data",
        color=0x7289da,
        description=f"Rank: #{data['market_cap_rank']}"
    )
    embed.set_thumbnail(url=data["image"]["small"])
    
    market_data = data["market_data"]
    fields = [
        ("Market Cap", f"${market_data['market_cap']['usd']:,.2f}"),
        ("24h Volume", f"${market_data['total_volume']['usd']:,.2f}"),
        ("Circulating Supply", f"{market_data['circulating_supply']:,.2f}"),
        ("All-Time High", f"${market_data['ath']['usd']:,.2f}"),
        ("All-Time Low", f"${market_data['atl']['usd']:,.2f}")
    ]
    
    for name, value in fields:
        embed.add_field(name=name, value=value, inline=True)
    
    await interaction.edit_original_message(embed=embed)

@bot.slash_command(name="chart", description="Get 7-day price chart for a cryptocurrency")
async def chart(
    interaction: disnake.ApplicationCommandInteraction,
    crypto: str = commands.Param(description="Cryptocurrency symbol (e.g., bitcoin)"),
    currency: str = commands.Param(default="usd", description="Currency to display price in")
):
    await interaction.response.defer()
    
    try:
        response = requests.get(
            f"{COINGECKO_URL}/coins/{crypto}/market_chart",
            params={"vs_currency": currency, "days": "7"}
        )
        data = response.json()
    except Exception as e:
        return await interaction.edit_original_message(content="❌ Failed to fetch chart data")
    
    prices = [point[1] for point in data["prices"]]
    dates = [datetime.fromtimestamp(point[0]/1000) for point in data["prices"]]
    
    plt.figure(figsize=(10, 5))
    plt.plot(dates, prices, color="#5865F2")
    plt.title(f"7-Day Price Chart ({currency.upper()})")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.grid(True)
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    file = disnake.File(buf, filename="chart.png")
    await interaction.edit_original_message(file=file)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

if __name__ == "__main__":
    bot.run(os.getenv("BOT_TOKEN"))