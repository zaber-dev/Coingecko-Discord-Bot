import disnake
from disnake.ext import commands
import os
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
from utils.coin_utils import fetch_coin_list, load_coin_list_from_file, build_maps
from utils.coin_utils import update_coin_list
from commands.price import price
from commands.market import market

load_dotenv()
executor = ThreadPoolExecutor()

bot = commands.InteractionBot(
    intents=disnake.Intents.default(),
    activity=disnake.Game(name="/help for crypto info!")
)

@bot.event
async def on_ready():
    global coin_list, id_map, name_map, symbol_map
    # Initial load
    coin_list = load_coin_list_from_file() or await fetch_coin_list(executor)
    if not coin_list:
        print("Failed to load coin list")
        return
    
    # Build lookup maps
    id_map, name_map, symbol_map = build_maps(coin_list)
    
    # Start background tasks
    update_coin_list.start()
    print(f"Logged in as {bot.user}")

# Register commands
bot.add_slash_command(price)
bot.add_slash_command(market)

if __name__ == "__main__":
    bot.run(os.getenv("BOT_TOKEN"))