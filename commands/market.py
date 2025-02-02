import disnake
from disnake.ext import commands
from utils.coin_utils import get_exact_match, get_crypto_data
from utils.views import MarketChartView

@commands.slash_command(
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
