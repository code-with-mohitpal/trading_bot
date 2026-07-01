"""
cli.py

Command-line interface for the trading bot, built with Click.

Usage examples:

    python main.py place-order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01

    python main.py place-order --symbol BTCUSDT --side SELL --type LIMIT \\
        --quantity 0.01 --price 60000

Run `python main.py --help` or `python main.py place-order --help` for details.
"""

import sys

import click

from bot.client import BinanceFuturesTestnetClient, ClientConfigError
from bot.logging_config import setup_logging
from bot.orders import OrderExecutionError, OrderManager
from bot.validators import ValidationError, validate_order_input


@click.group()
def cli():
    """Simplified Trading Bot for Binance Futures Testnet (USDT-M)."""
    setup_logging()


@cli.command("place-order")
@click.option("--symbol", required=True, help="Trading pair symbol, e.g. BTCUSDT.")
@click.option(
    "--side",
    required=True,
    type=click.Choice(["BUY", "SELL"], case_sensitive=False),
    help="Order side.",
)
@click.option(
    "--type",
    "order_type",
    required=True,
    type=click.Choice(["MARKET", "LIMIT"], case_sensitive=False),
    help="Order type.",
)
@click.option("--quantity", required=True, help="Order quantity, e.g. 0.01.")
@click.option(
    "--price",
    required=False,
    default=None,
    help="Limit price. Required when --type=LIMIT, ignored for MARKET.",
)
@click.option(
    "--time-in-force",
    required=False,
    default="GTC",
    type=click.Choice(["GTC", "IOC", "FOK"], case_sensitive=False),
    help="Time in force for LIMIT orders (default: GTC).",
)
def place_order(symbol, side, order_type, quantity, price, time_in_force):
    """Validate input and place a MARKET or LIMIT order on Futures Testnet."""
    logger = setup_logging()

    # 1. Validate all input before touching the network.
    try:
        clean = validate_order_input(
            symbol=symbol, side=side, order_type=order_type, quantity=quantity, price=price
        )
    except ValidationError as exc:
        click.secho(f"[VALIDATION ERROR] {exc}", fg="red", bold=True)
        logger.error("Validation failed: %s", exc)
        sys.exit(1)

    # 2. Print a clear order request summary before submission.
    click.secho("\n=== Order Request Summary ===", fg="cyan", bold=True)
    click.echo(f"  Symbol       : {clean['symbol']}")
    click.echo(f"  Side         : {clean['side']}")
    click.echo(f"  Order Type   : {clean['order_type']}")
    click.echo(f"  Quantity     : {clean['quantity']}")
    if clean["order_type"] == "LIMIT":
        click.echo(f"  Price        : {clean['price']}")
        click.echo(f"  Time in Force: {time_in_force.upper()}")
    click.echo("==============================\n")

    # 3. Build the API client (fails fast if credentials are missing/invalid).
    try:
        testnet_client = BinanceFuturesTestnetClient()
    except ClientConfigError as exc:
        click.secho(f"[CONFIG ERROR] {exc}", fg="red", bold=True)
        logger.error("Client configuration failed: %s", exc)
        sys.exit(1)

    # 4. Place the order.
    order_manager = OrderManager(testnet_client)
    try:
        response = order_manager.place_order(
            symbol=clean["symbol"],
            side=clean["side"],
            order_type=clean["order_type"],
            quantity=clean["quantity"],
            price=clean["price"],
            time_in_force=time_in_force.upper(),
        )
    except OrderExecutionError as exc:
        click.secho(f"[ORDER FAILED] {exc}", fg="red", bold=True)
        sys.exit(1)

    # 5. Print a clear order response summary.
    click.secho("=== Order Response ===", fg="green", bold=True)
    click.echo(f"  Order ID     : {response.get('orderId')}")
    click.echo(f"  Status       : {response.get('status')}")
    click.echo(f"  Executed Qty : {response.get('executedQty')}")
    click.echo(f"  Avg Price    : {response.get('avgPrice', 'N/A')}")
    click.echo("=======================\n")
    click.secho("SUCCESS: Order placed successfully.", fg="green", bold=True)


@cli.command("ping")
def ping():
    """Check connectivity to Binance Futures Testnet using configured credentials."""
    logger = setup_logging()
    try:
        testnet_client = BinanceFuturesTestnetClient()
        testnet_client.ping()
        click.secho("SUCCESS: Connected to Binance Futures Testnet.", fg="green", bold=True)
    except ClientConfigError as exc:
        click.secho(f"[CONFIG ERROR] {exc}", fg="red", bold=True)
        logger.error("Client configuration failed: %s", exc)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        click.secho(f"[PING FAILED] {exc}", fg="red", bold=True)
        logger.exception("Ping failed")
        sys.exit(1)


if __name__ == "__main__":
    cli()
