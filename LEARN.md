# Learn More About This Project

## Overview
This project utilizes the CoinGecko free API to fetch comprehensive cryptocurrency data at the bot's startup. This includes retrieving all coin information, such as the price, market cap, rank, volume and its associated charts of different timespans.

## Features
- Fetches and caches cryptocurrency data at startup to optimize API usage.
- Provides two main commands:
  - `/price <crypto>`: Retrieves real-time price details of a specific cryptocurrency.
  - `/market <crypto>`: Fetches market details along with price charts for various time spans.
- Implements a caching mechanism to reduce redundant API requests, ensuring compliance with CoinGecko API rate limits.
- Displays interactive price charts for different timeframes.
- Suggests possible coin names for invalid search queries.
- Proper error handling and user-friendly responses.

## Technical Details
- The bot caches coin information at startup to prevent frequent API calls.
- It uses asynchronous API requests to improve performance.
- Interactive components such as paginated views and dropdown selections enhance user experience.
- Designed to be lightweight and efficient, reducing unnecessary API calls and ensuring responsiveness.

## How to Use
To interact with the bot, use:
- `/price <crypto>`: Get the latest price of the specified cryptocurrency.
- `/market <crypto>`: Fetch market data, including charts for different timeframes.

## Contribution
Contributions are welcome! Feel free to submit issues or pull requests to improve the bot's functionality and efficiency.

