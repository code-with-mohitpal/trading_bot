"""
main.py

Entry point for the Trading Bot CLI (Binance Futures Testnet).

Examples:
    python main.py place-order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
    python main.py place-order --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 60000
    python main.py ping
"""

from bot.cli import cli

if __name__ == "__main__":
    cli()
