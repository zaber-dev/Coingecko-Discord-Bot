import requests
import json
from datetime import datetime, timedelta
from cachetools import TTLCache
from fuzzywuzzy import process
from concurrent.futures import ThreadPoolExecutor
import asyncio
from disnake.ext import tasks

# Initialize caches and executor
executor = ThreadPoolExecutor()

COINGECKO_URL = "https://api.coingecko.com/api/v3"
COIN_LIST_FILE = "../coin_list.json"

# Global variables for coin data
coin_list = []
id_map = {}
name_map = {}
symbol_map = {}
executor = ThreadPoolExecutor()

# Initialize caches
coin_list_cache = TTLCache(maxsize=1, ttl=timedelta(hours=6).seconds)
price_cache = TTLCache(maxsize=1000, ttl=timedelta(minutes=5).seconds)
chart_cache = TTLCache(maxsize=1000, ttl=timedelta(minutes=15).seconds)

@tasks.loop(hours=6)
async def update_coin_list():
    global coin_list, id_map, name_map, symbol_map
    new_list = await fetch_coin_list(executor)
    if new_list:
        coin_list = new_list
        id_map, name_map, symbol_map = build_maps(coin_list)
        print("Updated coin list and maps")

async def fetch_coin_list(executor):
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
