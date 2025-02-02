import disnake
import requests
import io
import matplotlib.pyplot as plt
from datetime import datetime
from utils.coin_utils import chart_cache, get_crypto_data
COINGECKO_URL = "https://api.coingecko.com/api/v3"

class MarketChartView(disnake.ui.View):
    """Interactive chart period selector"""
    def __init__(self, crypto_id, currency, embed):
        super().__init__(timeout=60)
        self.crypto_id = crypto_id
        self.currency = currency
        self.embed = embed
        
    async def generate_chart(self, days: int):
        """Generate chart with caching"""
        cache_key = f"{self.crypto_id}-{self.currency}-{days}"
        if cache_key in chart_cache:
            buf = chart_cache[cache_key]
            plt.savefig(buf, format='png')
            buf.seek(0)
            plt.close()
            return buf
        
        try:
            response = requests.get(
                f"{COINGECKO_URL}/coins/{self.crypto_id}/market_chart",
                params={"vs_currency": self.currency, "days": days}
            )
            response.raise_for_status()
            data = response.json()
            
            prices = [point[1] for point in data["prices"]]
            dates = [datetime.fromtimestamp(point[0]/1000) for point in data["prices"]]
            
            plt.figure(figsize=(10, 5))
            plt.plot(dates, prices, color="#5865F2")
            plt.title(f"{days}-Day Price Chart ({self.currency.upper()})")
            plt.xlabel("Date")
            plt.ylabel("Price")
            plt.grid(True)
            plt.tight_layout()
            
            buf = io.BytesIO()
            chart_cache[cache_key] = buf
            plt.savefig(buf, format='png')
            buf.seek(0)
            plt.close()
            return buf
        except Exception as e:
            print(f"Error generating chart: {e}")
            return None

    @disnake.ui.button(label="1D", style=disnake.ButtonStyle.primary)
    async def day_button(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        buf = await self.generate_chart(1)
        if buf:
            file = disnake.File(buf, filename="chart.png")
            self.embed.set_image(file=file)
            await interaction.response.edit_message(embed=self.embed)
            
    @disnake.ui.button(label="7D", style=disnake.ButtonStyle.primary)
    async def week_button(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        buf = await self.generate_chart(7)
        if buf:
            file = disnake.File(buf, filename="chart.png")
            self.embed.set_image(file=file)
            await interaction.response.edit_message(embed=self.embed)
            
    @disnake.ui.button(label="30D", style=disnake.ButtonStyle.primary)
    async def month_button(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        buf = await self.generate_chart(30)
        if buf:
            file = disnake.File(buf, filename="chart.png")
            self.embed.set_image(file=file)
            await interaction.response.edit_message(embed=self.embed)

    @disnake.ui.button(label="90D", style=disnake.ButtonStyle.primary)
    async def three_month_button(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        buf = await self.generate_chart(90)
        if buf:
            file = disnake.File(buf, filename="chart.png")
            self.embed.set_image(file=file)
            await interaction.response.edit_message(embed=self.embed)

    @disnake.ui.button(label="1Y", style=disnake.ButtonStyle.primary)
    async def year_button(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        buf = await self.generate_chart(365)
        if buf:
            file = disnake.File(buf, filename="chart.png")
            self.embed.set_image(file=file)
            await interaction.response.edit_message(embed=self.embed)

class CurrencyConverter(disnake.ui.View):
    """Interactive currency converter buttons"""
    def __init__(self, crypto_id, currency):
        super().__init__(timeout=60)
        self.crypto_id = crypto_id
        self.currency = currency
        self.currencies = ["usd", "eur", "btc", "eth"]

    async def update_price(self, interaction: disnake.Interaction, currency: str):
        data = await get_crypto_data(self.crypto_id)
        if not data:
            return await interaction.response.send_message("Failed to fetch data", ephemeral=True)
        
        try:
            price = data["market_data"]["current_price"][currency]
        except KeyError:
            return await interaction.response.send_message("Invalid currency", ephemeral=True)
        
        embed = interaction.message.embeds[0]
        embed.set_field_at(
            0,
            name="Current Price",
            value=f"{price:.4f} {currency.upper()}",
            inline=False
        )
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
