import disnake
from disnake.ext import commands, tasks
import requests
import matplotlib
matplotlib.use('Agg')  # Set backend before pyplot import
import matplotlib.pyplot as plt
import io
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from cachetools import TTLCache
from fuzzywuzzy import process
from concurrent.futures import ThreadPoolExecutor
import asyncio

load_dotenv()

# Initialize caches and executor
coin_list_cache = TTLCache(maxsize=1, ttl=timedelta(hours=6).seconds)
price_cache = TTLCache(maxsize=1000, ttl=timedelta(minutes=5).seconds)
chart_cache = TTLCache(maxsize=1000, ttl=timedelta(minutes=15).seconds)
executor = ThreadPoolExecutor()

bot = commands.InteractionBot(
    intents=disnake.Intents.default(),
    activity=disnake.Game(name="/help for crypto info!")
)

COINGECKO_URL = "https://api.coingecko.com/api/v3"
COIN_LIST_FILE = "coin_list.json"

# Global variables for coin data
coin_list = []
id_map = {}
name_map = {}
symbol_map = {}

async def fetch_coin_list():
    """Fetch and cache coin list from CoinGecko"""
    try:
        response = await asyncio.get_event_loop().run_in_executor(
            executor, requests.get, f"{COINGECKO_URL}/coins/list"
        )
        response.raise_for_status()
        coin_list = response.json()
        with open(COIN_LIST_FILE, "w") as f:
            json.dump(coin_list, f)
        return coin_list
    except Exception as e:
        print(f"Error fetching coin list: {e}")
        return None

def load_coin_list_from_file():
    """Load coin list from local file"""
    try:
        with open(COIN_LIST_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def build_maps(coins):
    """Build lookup maps from coin list"""
    id_map = {}
    name_map = {}
    symbol_map = {}
    
    for coin in coins:
        coin_id = coin['id']
        # ID map
        id_map[coin_id.lower()] = coin_id
        
        # Name map (first occurrence only)
        name_lower = coin['name'].lower()
        if name_lower not in name_map:
            name_map[name_lower] = coin_id
        
        # Symbol map (first occurrence only)
        symbol_lower = coin['symbol'].lower()
        if symbol_lower not in symbol_map:
            symbol_map[symbol_lower] = coin_id
    
    return id_map, name_map, symbol_map

def get_exact_match(query: str):
    """Check for exact match in lookup maps"""
    query_lower = query.lower()
    if query_lower in id_map:
        return id_map[query_lower]
    if query_lower in name_map:
        return name_map[query_lower]
    if query_lower in symbol_map:
        return symbol_map[query_lower]
    return None

async def search_coins(query: str):
    """Fuzzy search for coins with cached list"""
    if not coin_list:
        return []
    
    names = [(f"{coin['name']} ({coin['symbol']})", coin['id']) for coin in coin_list]
    results = process.extractBests(query, names, score_cutoff=50, limit=25)
    return [{"name": result[0][0], "id": result[0][1]} for result in results]

async def get_crypto_data(crypto_id: str):
    """Fetch cryptocurrency data with caching"""
    if crypto_id in price_cache:
        return price_cache[crypto_id]
    
    try:
        response = await asyncio.get_event_loop().run_in_executor(
            executor, requests.get,
            f"{COINGECKO_URL}/coins/{crypto_id}",
            {"params": {"localization": "false", "tickers": "false", "community_data": "false"}}
        )
        response.raise_for_status()
        data = response.json()
        price_cache[crypto_id] = data
        return data
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

class PaginationView(disnake.ui.View):
    """Paginated results view"""
    def __init__(self, embeds):
        super().__init__(timeout=60)
        self.embeds = embeds
        self.current_page = 0
        
    @disnake.ui.button(label="◀", style=disnake.ButtonStyle.gray)
    async def previous_button(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        self.current_page = max(0, self.current_page - 1)
        await interaction.response.edit_message(embed=self.embeds[self.current_page])
        
    @disnake.ui.button(label="▶", style=disnake.ButtonStyle.gray)
    async def next_button(self, button: disnake.ui.Button, interaction: disnake.Interaction):
        self.current_page = min(len(self.embeds)-1, self.current_page + 1)
        await interaction.response.edit_message(embed=self.embeds[self.current_page])

class MarketChartView(disnake.ui.View):
    """Interactive chart period selector"""
    def __init__(self, crypto_id, currency,embed):
        super().__init__(timeout=60)
        self.crypto_id = crypto_id
        self.currency = currency
        self.embed = embed
        
    async def generate_chart(self, days: int):
        """Generate chart with caching"""
        cache_key = f"{self.crypto_id}-{self.currency}-{days}"
        if cache_key in chart_cache:
            return chart_cache[cache_key]
        
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
            plt.savefig(buf, format='png')
            buf.seek(0)
            plt.close()
            
            chart_cache[cache_key] = buf
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

@bot.slash_command(
    name="price",
    description="Get current cryptocurrency price",
    options=[
        disnake.Option(
            name="crypto",
            description="Cryptocurrency name or symbol (e.g. bitcoin or btc)",
            type=disnake.OptionType.string,
            required=True
        ),
        disnake.Option(
            name="currency",
            description="Display currency",
            type=disnake.OptionType.string,
            required=False,
            choices=["usd", "eur", "bdt", "btc", "eth"]
        )
    ]
)
async def price(
    interaction: disnake.ApplicationCommandInteraction,
    crypto: str,
    currency: str = "usd"
):
    """Get cryptocurrency price with currency conversion buttons"""
    await interaction.response.defer()
    
    exact_id = get_exact_match(crypto)
    if exact_id:
        data = await get_crypto_data(exact_id)
        if data:
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
            
            view = CurrencyConverter(exact_id, currency)
            await interaction.edit_original_message(embed=embed, view=view)
            return

    # Show suggestions if no exact match
    results = await search_coins(crypto)
    if not results:
        return await interaction.edit_original_message(content="❌ Cryptocurrency not found!")
    
    embeds = []
    for i in range(0, len(results), 5):
        embed = disnake.Embed(title="Did you mean one of these?", color=0x7289da)
        for result in results[i:i+5]:
            embed.add_field(name=result['name'], value=f"`/price {result['id']}`", inline=False)
        embeds.append(embed)
    
    view = PaginationView(embeds) if len(embeds) > 1 else None
    await interaction.edit_original_message(embed=embeds[0], view=view)

@bot.slash_command(
    name="market",
    description="Get market data with price chart",
    options=[
        disnake.Option(
            name="crypto",
            description="Cryptocurrency name or symbol",
            type=disnake.OptionType.string,
            required=True
        ),
        disnake.Option(
            name="currency",
            description="Display currency",
            type=disnake.OptionType.string,
            required=False,
            choices=["usd", "eur", "bdt", "btc", "eth"]
        )
    ]
)
async def market(
    interaction: disnake.ApplicationCommandInteraction,
    crypto: str,
    currency: str = "usd"
):
    """Market data command with initial chart"""
    await interaction.response.defer()
    
    exact_id = get_exact_match(crypto)
    if not exact_id:
        return await interaction.edit_original_message(content="❌ Cryptocurrency not found!")
    
    data = await get_crypto_data(exact_id)
    if not data:
        return await interaction.edit_original_message(content="❌ Failed to fetch data!")
    
    # Create initial embed
    embed = disnake.Embed(
        title=f"{data['name']} Market Data",
        color=0x7289da,
        description=f"Rank: #{data['market_cap_rank']}"
    )
    embed.set_thumbnail(url=data["image"]["small"])
    
    # Add market data fields
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
    
    # Generate initial chart
    view = MarketChartView(exact_id, currency, embed)
    buf = await view.generate_chart(7)  # Default to 7-day chart
    
    if buf:
        file = disnake.File(buf, filename="chart.png")
        embed.set_image(file=file)
    
    await interaction.edit_original_message(embed=embed, view=view)

@tasks.loop(hours=6)
async def update_coin_list():
    global coin_list, id_map, name_map, symbol_map
    new_list = await fetch_coin_list()
    if new_list:
        coin_list = new_list
        id_map, name_map, symbol_map = build_maps(coin_list)
        print("Updated coin list and maps")

@bot.event
async def on_ready():
    global coin_list, id_map, name_map, symbol_map
    # Initial load
    coin_list = load_coin_list_from_file() or await fetch_coin_list()
    if not coin_list:
        print("Failed to load coin list")
        return
    
    # Build lookup maps
    id_map, name_map, symbol_map = build_maps(coin_list)
    
    # Start background tasks
    update_coin_list.start()
    print(f"Logged in as {bot.user}")

if __name__ == "__main__":
    bot.run(os.getenv("BOT_TOKEN"))