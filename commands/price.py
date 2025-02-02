import disnake
from datetime import datetime
from disnake.ext import commands
from utils.coin_utils import get_exact_match, get_crypto_data, search_coins
from utils.views import CurrencyConverter
from utils.paginator import PaginationView

@commands.slash_command(
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
