# Coingecko Discord Bot

A Discord bot that provides cryptocurrency information and interactive charts using the Coingecko API.


## Features

- Fetch current cryptocurrency prices
- Display interactive price charts for different time periods
- Convert cryptocurrency prices to various currencies
- Paginated views for displaying multiple results
- Proper error handling
- Coin Suggestions for invalid searches

## Setup

1. Clone the repository:
    ```bash
    git clone https://github.com/zaber-dev/Coingecko-Discord-Bot.git
    cd Coingecko-Discord-Bot
    ```

2. Create a virtual environment and activate it:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Create a `.env` file based on the `.env.example`:
    ```bash
    cp .env.example .env
    ```

5. Add your Discord bot token to the `.env` file:
    ```properties
    BOT_TOKEN=your_discord_bot_token
    ```

## Usage

1. Run the bot:
    ```bash
    python main.py
    ```

2. Invite the bot to your Discord server using the OAuth2 URL with the necessary permissions.

## Commands

- `/price <crypto>`: Get the current price of a cryptocurrency.
- `/market <crypto>`: Get market data for a cryptocurrency.

## Interactive Views

- **MarketChartView**: Select different time periods to view price charts.
- **CurrencyConverter**: Convert cryptocurrency prices to different currencies.
- **PaginationView**: Navigate through multiple pages of results.

## Contributing

Feel free to open issues or submit pull requests if you have any improvements or bug fixes.

## License

This project is licensed under the MIT License.
