"""
client.py

Thin wrapper around python-binance's Client, hard-locked to the Binance
Futures Testnet (USDT-M). This isolates all "how do we talk to Binance"
concerns from order-placement business logic (orders.py) and the CLI
(cli.py), so the API layer can be swapped or mocked independently.
"""

import os

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
from dotenv import load_dotenv

from bot.logging_config import get_logger

logger = get_logger()

# Binance Futures Testnet (USDT-M) base URL, as specified in the task.
FUTURES_TESTNET_BASE_URL = "https://testnet.binancefuture.com"


class ClientConfigError(Exception):
    """Raised when the Binance client cannot be configured (e.g. missing keys)."""


class BinanceFuturesTestnetClient:
    """
    Wraps a python-binance `Client` instance configured exclusively for the
    Binance Futures Testnet. This class intentionally does NOT expose any
    way to point at mainnet, keeping the bot safe by construction.
    """

    def __init__(self, api_key: str = None, api_secret: str = None):
        # Load variables from a local .env file if present (no-op if absent
        # or if the variables are already set in the environment).
        load_dotenv()

        self.api_key = api_key or os.getenv("BINANCE_API_KEY")
        self.api_secret = api_secret or os.getenv("BINANCE_API_SECRET")

        if not self.api_key or not self.api_secret:
            raise ClientConfigError(
                "Missing API credentials. Set BINANCE_API_KEY and "
                "BINANCE_API_SECRET as environment variables or in a .env "
                "file (see .env.example)."
            )

        self._client = self._build_client()

    def _build_client(self) -> Client:
        """
        Construct a python-binance Client pinned to the Futures Testnet.

        python-binance's `testnet=True` flag switches both spot and futures
        endpoints to their respective testnets. We additionally set
        FUTURES_URL explicitly to the URL given in the task spec, so the
        target endpoint is unambiguous regardless of library version.
        """
        try:
            # ping=False: python-binance's Client otherwise pings the SPOT
            # testnet on init, which is an unnecessary dependency for a bot
            # that only ever talks to the Futures Testnet. We verify Futures
            # connectivity ourselves via ping() -> futures_ping() instead.
            client = Client(self.api_key, self.api_secret, testnet=True, ping=False)
            # Explicitly pin the futures base URL (belt-and-braces on top of
            # testnet=True) so we never accidentally hit mainnet.
            client.FUTURES_URL = f"{FUTURES_TESTNET_BASE_URL}/fapi"
            logger.info("Binance Futures Testnet client initialized (base_url=%s)",
                        FUTURES_TESTNET_BASE_URL)
            return client
        except (BinanceAPIException, BinanceRequestException) as exc:
            logger.error("Failed to initialize Binance client: %s", exc)
            raise ClientConfigError(f"Failed to initialize Binance client: {exc}") from exc

    def get_raw_client(self) -> Client:
        """Return the underlying python-binance Client for direct use."""
        return self._client

    def ping(self) -> bool:
        """
        Simple connectivity/credential check against the Futures Testnet.
        Returns True if reachable, raises the underlying exception otherwise.
        """
        try:
            self._client.futures_ping()
            logger.info("Futures Testnet ping successful.")
            return True
        except (BinanceAPIException, BinanceRequestException) as exc:
            logger.error("Futures Testnet ping failed: %s", exc)
            raise
