"""
Trading Bot package for Binance Futures Testnet (USDT-M).

This package provides a clean, reusable structure for placing orders on
Binance Futures Testnet, split into:
    - client.py            : Binance API client wrapper (testnet only)
    - orders.py             : Order placement business logic
    - validators.py         : CLI input validation
    - logging_config.py     : Centralized logging configuration
    - cli.py                 : Command-line interface (Click)
"""

__version__ = "1.0.0"
