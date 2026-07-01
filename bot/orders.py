"""
orders.py

Order placement logic for Binance Futures Testnet. This module knows how
to turn validated order parameters into a `futures_create_order` API call,
and how to log/interpret the request and response. It has no knowledge of
the CLI or of argument parsing.
"""

from decimal import Decimal
from typing import Optional

import requests
from binance.exceptions import BinanceAPIException, BinanceOrderException, BinanceRequestException

from bot.client import BinanceFuturesTestnetClient
from bot.logging_config import get_logger

logger = get_logger()


class OrderExecutionError(Exception):
    """Raised when an order fails to execute for any reason (API, network, etc.)."""


class OrderManager:
    """
    Encapsulates order placement against Binance Futures Testnet.
    """

    def __init__(self, testnet_client: BinanceFuturesTestnetClient):
        self.client = testnet_client.get_raw_client()

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        time_in_force: str = "GTC",
    ) -> dict:
        """
        Place a MARKET or LIMIT order on Binance Futures Testnet.

        Args:
            symbol: Normalized trading pair, e.g. 'BTCUSDT'.
            side: 'BUY' or 'SELL'.
            order_type: 'MARKET' or 'LIMIT'.
            quantity: Order quantity (Decimal).
            price: Limit price (Decimal), required only for LIMIT orders.
            time_in_force: Time-in-force for LIMIT orders (default 'GTC').

        Returns:
            The raw order response dict from Binance.

        Raises:
            OrderExecutionError: on any API, order, or network-level failure.
        """
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": str(quantity),
        }
        if order_type == "LIMIT":
            params["price"] = str(price)
            params["timeInForce"] = time_in_force

        logger.info("Order request | %s", params)

        try:
            response = self.client.futures_create_order(**params)
            logger.info("Order response | %s", response)
            return response

        except BinanceOrderException as exc:
            logger.error("Order rejected by exchange | request=%s | error=%s", params, exc)
            raise OrderExecutionError(f"Order rejected by exchange: {exc}") from exc

        except BinanceAPIException as exc:
            logger.error("Binance API error | request=%s | error=%s", params, exc)
            raise OrderExecutionError(f"Binance API error ({exc.status_code}): {exc.message}") from exc

        except BinanceRequestException as exc:
            logger.error("Malformed request/response | request=%s | error=%s", params, exc)
            raise OrderExecutionError(f"Malformed request or response: {exc}") from exc

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exc:
            logger.error("Network failure while placing order | request=%s | error=%s", params, exc)
            raise OrderExecutionError(f"Network failure while contacting Binance: {exc}") from exc

        except requests.exceptions.RequestException as exc:
            logger.error("HTTP request failure | request=%s | error=%s", params, exc)
            raise OrderExecutionError(f"HTTP request failure: {exc}") from exc

        except Exception as exc:  # noqa: BLE001 - final safety net, always logged
            logger.exception("Unexpected error while placing order | request=%s", params)
            raise OrderExecutionError(f"Unexpected error while placing order: {exc}") from exc

    def place_market_order(self, symbol: str, side: str, quantity: Decimal) -> dict:
        """Convenience wrapper for a MARKET order."""
        return self.place_order(symbol=symbol, side=side, order_type="MARKET", quantity=quantity)

    def place_limit_order(
        self, symbol: str, side: str, quantity: Decimal, price: Decimal, time_in_force: str = "GTC"
    ) -> dict:
        """Convenience wrapper for a LIMIT order."""
        return self.place_order(
            symbol=symbol,
            side=side,
            order_type="LIMIT",
            quantity=quantity,
            price=price,
            time_in_force=time_in_force,
        )
