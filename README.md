# Trading Bot — Binance Futures Testnet (USDT-M)

A simplified Python CLI trading bot that places **MARKET** and **LIMIT** orders on the
**Binance Futures Testnet (USDT-M)**, built with a clean, testable structure:
a dedicated API client layer, an order-placement layer, input validation, structured
logging, and a Click-based command-line interface.

> ⚠️ This bot is hard-wired to the **Futures Testnet** (`https://testnet.binancefuture.com`)
> only. It cannot be pointed at mainnet.

---

## Project Structure

```
trading_bot/
│── bot/
│   ├── __init__.py
│   ├── client.py            # Binance Futures Testnet client wrapper
│   ├── orders.py             # Order placement logic (MARKET / LIMIT)
│   ├── validators.py         # CLI input validation
│   ├── logging_config.py     # Centralized logging setup
│   └── cli.py                 # Click-based CLI entry point
├── logs/
│   └── trading_bot.log       # Example log: one MARKET + one LIMIT order
├── .env.example               # Template for API credentials
├── .gitignore
├── main.py                    # Application entry point
├── requirements.txt
└── README.md
```

**Separation of concerns:**
- `client.py` — knows *how* to talk to Binance (auth, base URL, connectivity).
- `orders.py` — knows *what* an order request/response looks like and how to handle
  API/network failures.
- `validators.py` — knows *whether* user input is well-formed, before any network call.
- `cli.py` — wires validation → client → orders together and formats output for a human.
- `logging_config.py` — one place to configure how/where logs are written.

---

## 1. Installation

**Requirements:** Python 3.9+

```bash
# Clone the repository
git clone <your-repo-url>
cd trading_bot

# (Recommended) create a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## 2. API Key Setup (Binance Futures Testnet)

1. Go to the Binance Futures Testnet: **https://testnet.binancefuture.com**
2. Register / log in (a separate account from Binance mainnet).
3. Navigate to **API Key** management and generate a new key pair.
4. Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

```env
BINANCE_API_KEY=your_testnet_api_key_here
BINANCE_API_SECRET=your_testnet_api_secret_here
```

The `.env` file is loaded automatically via `python-dotenv` and is excluded from
version control by `.gitignore`. **Never commit real API keys.**

You can verify your setup is working with:

```bash
python main.py ping
```

---

## 3. Running the Bot

### Check connectivity

```bash
python main.py ping
```

### Place a MARKET order

```bash
python main.py place-order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

### Place a LIMIT order

```bash
python main.py place-order --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 61500
```

### Optional: custom time-in-force for LIMIT orders

```bash
python main.py place-order --symbol ETHUSDT --side BUY --type LIMIT \
    --quantity 0.05 --price 3200 --time-in-force IOC
```

### Help

```bash
python main.py --help
python main.py place-order --help
```

### Example output

```
=== Order Request Summary ===
  Symbol       : BTCUSDT
  Side         : BUY
  Order Type   : MARKET
  Quantity     : 0.01
==============================

=== Order Response ===
  Order ID     : 3457123980
  Status       : FILLED
  Executed Qty : 0.01
  Avg Price    : 60123.40
=======================

SUCCESS: Order placed successfully.
```

Every request, response, and error is also written to `logs/trading_bot.log`
(see that file for real example entries from one MARKET order and one LIMIT order).

---

## 4. Validation & Error Handling

Input is validated **before** any network call is made:

| Field    | Rule                                                         |
|----------|---------------------------------------------------------------|
| symbol   | Required; normalized to uppercase; alphanumeric, 5–15 chars   |
| side     | Required; must be `BUY` or `SELL`                             |
| type     | Required; must be `MARKET` or `LIMIT`                         |
| quantity | Required; must be a positive number                            |
| price    | Required and positive **only** for `LIMIT` orders; ignored for `MARKET` |

Runtime failures are caught and reported with a clear, specific message and a
non-zero exit code, distinguishing between:
- **Validation errors** (bad CLI input)
- **Configuration errors** (missing/invalid API credentials)
- **Order rejections** (exchange rejected the order, e.g. bad symbol, insufficient
  testnet balance, filter violations)
- **Binance API errors** (authenticated but the API returned an error code)
- **Network failures** (timeouts, connection errors)
- **Unexpected errors** (logged with full traceback via `logger.exception`)

---

## 5. Logging

All requests, responses, and errors are logged to `logs/trading_bot.log` using a
rotating file handler (5 MB per file, 3 backups retained), so the log file:

- Records every order request exactly as sent to Binance
- Records every order response exactly as received from Binance
- Records validation failures, config errors, API errors, and network errors
- Stays useful rather than noisy — DEBUG-level chatter from the underlying HTTP
  library is not logged; only the bot's own request/response/error lines are

A console handler also prints warnings/errors to the terminal, while full detail
lives in the log file.

---

## 6. Assumptions

- **Futures Testnet only.** The bot is intentionally hard-coded to
  `https://testnet.binancefuture.com` (via `python-binance`'s `testnet=True` plus an
  explicit `FUTURES_URL` override) and cannot be redirected to mainnet.
- **USDT-M perpetual futures only** (`futures_create_order`), not Coin-M futures or spot.
- **Symbol/quantity/price precision (tick size, step size, lot size, min notional)
  is not pre-validated against `exchangeInfo`.** The bot performs shape-level
  validation (positive numbers, correct symbol format) and relies on Binance to
  reject values that violate exchange-specific filters; the resulting rejection is
  caught and reported clearly rather than causing a silent failure.
- **Single account, single order per invocation.** The CLI is designed for one
  order per run; scripting/looping multiple orders is left to the caller (e.g. a
  shell script invoking `main.py` repeatedly).
- **Default time-in-force for LIMIT orders is `GTC`**, configurable via
  `--time-in-force` (`GTC` / `IOC` / `FOK`).
- **Only `MARKET` and `LIMIT` order types are implemented** per the core
  requirements; no Stop-Limit/OCO/TWAP/Grid bonus feature is included in this
  submission.
- Credentials are read from environment variables (optionally via a local `.env`
  file); no credentials are hard-coded or logged.

---

## 7. Tech Stack

- Python 3.x
- [`python-binance`](https://python-binance.readthedocs.io/) — Binance API client
- [`click`](https://click.palletsprojects.com/) — CLI framework
- [`python-dotenv`](https://pypi.org/project/python-dotenv/) — `.env` loading
- Standard library `logging` (with `RotatingFileHandler`)

---

## 8. Disclaimer

This project interacts **only** with the Binance Futures **Testnet**, which uses
simulated funds and has no real financial value. It is provided for evaluation
purposes as part of a hiring application task.
