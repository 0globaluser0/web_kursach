from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen


ROOT_DIR = Path(__file__).resolve().parent
DB_PATH = ROOT_DIR / "cryptotrade.db"
HOST = "127.0.0.1"
PORT = 8000


DATABASE_MODEL = {
    "roles": ["id", "code", "title"],
    "users": ["id", "role_id", "name", "email", "password", "balance_usd", "created_at", "is_simulated"],
    "currencies": ["id", "symbol", "name", "price", "color", "risk", "description", "price_mode", "market_symbol", "source", "last_sync_at", "last_sync_status", "last_sync_message"],
    "wallets": ["id", "user_id", "currency_id", "amount", "updated_at", "is_simulated"],
    "transactions": ["id", "user_id", "currency_id", "side", "quantity", "price", "total", "status", "created_at", "is_simulated"],
    "price_history": ["id", "currency_id", "price", "recorded_at", "position"],
    "system_settings": ["id", "simulation_enabled", "simulation_users_target", "simulation_trades_per_minute", "last_simulation_at", "simulation_carry"],
}

FOREIGN_KEYS = [
    ("users.role_id", "roles.id"),
    ("wallets.user_id", "users.id"),
    ("wallets.currency_id", "currencies.id"),
    ("transactions.user_id", "users.id"),
    ("transactions.currency_id", "currencies.id"),
    ("price_history.currency_id", "currencies.id"),
]

DEFAULT_CURRENCIES = [
    ("btc", "BTC", "Bitcoin", 68120.5, "#f7931a", "Высокий", "Крупнейшая криптовалюта с высокой ликвидностью и заметной волатильностью.", "auto", "BTCUSDT", "binance"),
    ("eth", "ETH", "Ethereum", 3520.75, "#627eea", "Средний", "Платформа смарт-контрактов, используемая для DeFi, NFT и приложений Web3.", "auto", "ETHUSDT", "binance"),
    ("sol", "SOL", "Solana", 154.32, "#14f195", "Высокий", "Высокопроизводительная сеть для быстрых транзакций и децентрализованных приложений.", "auto", "SOLUSDT", "binance"),
    ("ada", "ADA", "Cardano", 0.48, "#2a71d0", "Средний", "Блокчейн-платформа с акцентом на исследовательский подход и устойчивость.", "auto", "ADAUSDT", "binance"),
    ("bnb", "BNB", "BNB", 598.4, "#f3ba2f", "Средний", "Монета экосистемы Binance, используемая для комиссий, сервисов и DeFi-приложений.", "auto", "BNBUSDT", "binance"),
    ("xrp", "XRP", "XRP", 0.52, "#23292f", "Средний", "Актив сети XRP Ledger, ориентированной на быстрые переводы и платежную инфраструктуру.", "auto", "XRPUSDT", "binance"),
    ("doge", "DOGE", "Dogecoin", 0.14, "#c2a633", "Высокий", "Популярная мем-криптовалюта с высокой волатильностью и активным сообществом.", "auto", "DOGEUSDT", "binance"),
    ("avax", "AVAX", "Avalanche", 31.6, "#e84142", "Высокий", "Платформа для смарт-контрактов и быстрых блокчейн-сетей с поддержкой подсетей.", "auto", "AVAXUSDT", "binance"),
    ("dot", "DOT", "Polkadot", 6.85, "#e6007a", "Средний", "Сеть для взаимодействия блокчейнов, парачейнов и кроссчейн-приложений.", "auto", "DOTUSDT", "binance"),
    ("link", "LINK", "Chainlink", 15.9, "#2a5ada", "Средний", "Оракульная сеть для передачи внешних данных в смарт-контракты.", "auto", "LINKUSDT", "binance"),
    ("ltc", "LTC", "Litecoin", 84.2, "#345d9d", "Средний", "Один из ранних криптоактивов, ориентированный на быстрые и недорогие переводы.", "auto", "LTCUSDT", "binance"),
    ("trx", "TRX", "TRON", 0.115, "#ff0013", "Средний", "Блокчейн-сеть для быстрых переводов токенов и децентрализованных приложений.", "auto", "TRXUSDT", "binance"),
]


@dataclass
class TradeCheck:
    ok: bool
    message: str


def validate_trade(side: str, quantity: float, price: float, cash_usd: float, wallet_amount: float) -> TradeCheck:
    if side not in {"buy", "sell"}:
        return TradeCheck(False, "Неизвестный тип сделки.")
    if quantity <= 0:
        return TradeCheck(False, "Количество должно быть больше нуля.")

    total = round(quantity * price, 2)
    if side == "buy" and cash_usd < total:
        return TradeCheck(False, "Недостаточно USD для покупки.")
    if side == "sell" and wallet_amount < quantity:
        return TradeCheck(False, "Недостаточно монет для продажи.")

    return TradeCheck(True, "Сделка может быть выполнена.")


def bool_int(value: Any) -> int:
    return 1 if value else 0


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def ensure_column(db: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = [row["name"] for row in db.execute(f"PRAGMA table_info({table})")]

    if column not in columns:
        db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def table_exists(db: sqlite3.Connection, table: str) -> bool:
    row = db.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table,),
    ).fetchone()
    return row is not None


def migrate_transactions_without_orders(db: sqlite3.Connection) -> None:
    transaction_columns = [row["name"] for row in db.execute("PRAGMA table_info(transactions)")]
    orders_exist = table_exists(db, "orders")

    if "order_id" not in transaction_columns and not orders_exist:
        return

    db.execute("PRAGMA foreign_keys = OFF")
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions_new (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            currency_id TEXT NOT NULL REFERENCES currencies(id) ON DELETE CASCADE,
            side TEXT NOT NULL,
            quantity REAL NOT NULL,
            price REAL NOT NULL,
            total REAL NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            is_simulated INTEGER NOT NULL DEFAULT 0
        )
        """
    )

    if table_exists(db, "transactions"):
        db.execute(
            """
            INSERT OR IGNORE INTO transactions_new
            (id, user_id, currency_id, side, quantity, price, total, status, created_at, is_simulated)
            SELECT id, user_id, currency_id, side, quantity, price, total, status, created_at, is_simulated
            FROM transactions
            """
        )

    if orders_exist:
        db.execute(
            """
            INSERT OR IGNORE INTO transactions_new
            (id, user_id, currency_id, side, quantity, price, total, status, created_at, is_simulated)
            SELECT id, user_id, currency_id, side, quantity, price, total, status, created_at, is_simulated
            FROM orders
            """
        )

    if table_exists(db, "transactions"):
        db.execute("DROP TABLE transactions")
    if orders_exist:
        db.execute("DROP TABLE orders")
    db.execute("ALTER TABLE transactions_new RENAME TO transactions")
    db.execute("PRAGMA foreign_keys = ON")


def init_db() -> None:
    with connect() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS roles (
                id TEXT PRIMARY KEY,
                code TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                role_id TEXT NOT NULL REFERENCES roles(id),
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                balance_usd REAL NOT NULL,
                created_at TEXT NOT NULL,
                is_simulated INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS currencies (
                id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                color TEXT NOT NULL,
                risk TEXT NOT NULL,
                description TEXT NOT NULL,
                price_mode TEXT NOT NULL,
                market_symbol TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT 'manual',
                last_sync_at TEXT NOT NULL DEFAULT '',
                last_sync_status TEXT NOT NULL DEFAULT '',
                last_sync_message TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS wallets (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                currency_id TEXT NOT NULL REFERENCES currencies(id) ON DELETE CASCADE,
                amount REAL NOT NULL,
                updated_at TEXT NOT NULL,
                is_simulated INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                currency_id TEXT NOT NULL REFERENCES currencies(id) ON DELETE CASCADE,
                side TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                total REAL NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                is_simulated INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS price_history (
                id TEXT PRIMARY KEY,
                currency_id TEXT NOT NULL REFERENCES currencies(id) ON DELETE CASCADE,
                price REAL NOT NULL,
                recorded_at TEXT NOT NULL,
                position INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS system_settings (
                id TEXT PRIMARY KEY,
                simulation_enabled INTEGER NOT NULL,
                simulation_level INTEGER NOT NULL,
                last_simulation_at TEXT NOT NULL,
                simulation_users_target INTEGER NOT NULL,
                simulation_trades_per_minute INTEGER NOT NULL DEFAULT 6,
                simulation_carry REAL NOT NULL DEFAULT 0
            );
            """
        )
        migrate_transactions_without_orders(db)
        ensure_column(db, "system_settings", "simulation_trades_per_minute", "INTEGER NOT NULL DEFAULT 6")
        ensure_column(db, "system_settings", "simulation_carry", "REAL NOT NULL DEFAULT 0")
        db.executemany(
            "INSERT OR IGNORE INTO roles (id, code, title) VALUES (?, ?, ?)",
            [
                ("role-trader", "trader", "Трейдер"),
                ("role-admin", "admin", "Администратор"),
                ("role-simulator", "simulator", "Симулянт"),
            ],
        )
        db.execute("UPDATE users SET role_id = 'role-simulator' WHERE is_simulated = 1")
        db.executemany(
            """
            INSERT OR IGNORE INTO currencies
            (id, symbol, name, price, color, risk, description, price_mode, market_symbol, source,
             last_sync_at, last_sync_status, last_sync_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '', 'pending', 'Ожидает синхронизации')
            """,
            DEFAULT_CURRENCIES,
        )
        for currency_id, _, _, price, *_ in DEFAULT_CURRENCIES:
            exists = db.execute(
                "SELECT COUNT(*) FROM price_history WHERE currency_id = ?",
                (currency_id,),
            ).fetchone()[0]
            if not exists:
                db.execute(
                    """
                    INSERT INTO price_history (id, currency_id, price, recorded_at, position)
                    VALUES (?, ?, ?, '', 0)
                    """,
                    (f"{currency_id}-0", currency_id, price),
                )
        db.execute(
            """
            INSERT OR IGNORE INTO system_settings
            (id, simulation_enabled, simulation_level, last_simulation_at, simulation_users_target, simulation_trades_per_minute, simulation_carry)
            VALUES ('main', 0, 35, '', 4, 6, 0)
            """
        )


def role_id_for_code(db: sqlite3.Connection, code: str) -> str:
    row = db.execute("SELECT id FROM roles WHERE code = ?", (code,)).fetchone()
    return row["id"] if row else "role-trader"


def state_from_db() -> dict[str, Any]:
    with connect() as db:
        users = [
            {
                "id": row["id"],
                "role": row["role_code"],
                "name": row["name"],
                "email": row["email"],
                "password": row["password"],
                "balanceUsd": row["balance_usd"],
                "createdAt": row["created_at"],
                "isSimulated": bool(row["is_simulated"]),
            }
            for row in db.execute(
                """
                SELECT users.*, roles.code AS role_code
                FROM users
                JOIN roles ON roles.id = users.role_id
                ORDER BY users.created_at
                """
            )
        ]

        history_rows = db.execute(
            "SELECT currency_id, price FROM price_history ORDER BY currency_id, position"
        ).fetchall()
        history_by_currency: dict[str, list[float]] = {}
        for row in history_rows:
            history_by_currency.setdefault(row["currency_id"], []).append(row["price"])

        currencies = [
            {
                "id": row["id"],
                "symbol": row["symbol"],
                "name": row["name"],
                "price": row["price"],
                "color": row["color"],
                "risk": row["risk"],
                "description": row["description"],
                "priceMode": row["price_mode"],
                "marketSymbol": row["market_symbol"],
                "source": row["source"],
                "lastSyncAt": row["last_sync_at"],
                "lastSyncStatus": row["last_sync_status"],
                "lastSyncMessage": row["last_sync_message"],
                "history": history_by_currency.get(row["id"], [row["price"]]),
            }
            for row in db.execute("SELECT * FROM currencies ORDER BY symbol")
        ]

        wallets = [
            {
                "id": row["id"],
                "userId": row["user_id"],
                "currencyId": row["currency_id"],
                "amount": row["amount"],
                "updatedAt": row["updated_at"],
                "isSimulated": bool(row["is_simulated"]),
            }
            for row in db.execute("SELECT * FROM wallets ORDER BY updated_at")
        ]

        transactions = [
            {
                "id": row["id"],
                "userId": row["user_id"],
                "currencyId": row["currency_id"],
                "side": row["side"],
                "quantity": row["quantity"],
                "price": row["price"],
                "total": row["total"],
                "status": row["status"],
                "createdAt": row["created_at"],
                "isSimulated": bool(row["is_simulated"]),
            }
            for row in db.execute("SELECT * FROM transactions ORDER BY created_at")
        ]

        settings_row = db.execute("SELECT * FROM system_settings WHERE id = 'main'").fetchone()
        settings = {
            "simulationEnabled": bool(settings_row["simulation_enabled"]) if settings_row else False,
            "simulationLevel": settings_row["simulation_level"] if settings_row and settings_row["simulation_level"] is not None else 35,
            "lastSimulationAt": settings_row["last_simulation_at"] if settings_row and settings_row["last_simulation_at"] is not None else "",
            "simulationUsersTarget": settings_row["simulation_users_target"] if settings_row and settings_row["simulation_users_target"] is not None else 4,
            "simulationTradesPerMinute": settings_row["simulation_trades_per_minute"] if settings_row and settings_row["simulation_trades_per_minute"] is not None else 6,
            "simulationCarry": settings_row["simulation_carry"] if settings_row and settings_row["simulation_carry"] is not None else 0,
        }

    return {
        "users": users,
        "data": {
            "currencies": currencies,
            "wallets": wallets,
            "transactions": transactions,
            "settings": settings,
        },
    }


def replace_users(db: sqlite3.Connection, users: list[dict[str, Any]]) -> None:
    user_ids = [user["id"] for user in users if user.get("id")]

    for user in users:
        db.execute(
            """
            INSERT INTO users
            (id, role_id, name, email, password, balance_usd, created_at, is_simulated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                role_id = excluded.role_id,
                name = excluded.name,
                email = excluded.email,
                password = excluded.password,
                balance_usd = excluded.balance_usd,
                created_at = excluded.created_at,
                is_simulated = excluded.is_simulated
            """,
            (
                user["id"],
                role_id_for_code(db, user.get("role", "trader")),
                user.get("name", "Пользователь"),
                user.get("email", ""),
                user.get("password", ""),
                float(user.get("balanceUsd", 0)),
                user.get("createdAt", ""),
                bool_int(user.get("isSimulated")),
            ),
        )

    if user_ids:
        placeholders = ",".join("?" for _ in user_ids)
        db.execute(f"DELETE FROM users WHERE is_simulated = 1 AND id NOT IN ({placeholders})", user_ids)


def replace_data(db: sqlite3.Connection, data: dict[str, Any]) -> None:
    currency_ids = []
    for currency in data.get("currencies", []):
        currency_ids.append(currency["id"])
        db.execute(
            """
            INSERT INTO currencies
            (id, symbol, name, price, color, risk, description, price_mode, market_symbol, source,
             last_sync_at, last_sync_status, last_sync_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                symbol = excluded.symbol,
                name = excluded.name,
                price = excluded.price,
                color = excluded.color,
                risk = excluded.risk,
                description = excluded.description,
                price_mode = excluded.price_mode,
                market_symbol = excluded.market_symbol,
                source = excluded.source,
                last_sync_at = excluded.last_sync_at,
                last_sync_status = excluded.last_sync_status,
                last_sync_message = excluded.last_sync_message
            """,
            (
                currency["id"],
                currency.get("symbol", ""),
                currency.get("name", ""),
                float(currency.get("price", 0)),
                currency.get("color", "#0f9f6e"),
                currency.get("risk", "Средний"),
                currency.get("description", ""),
                currency.get("priceMode", "manual"),
                currency.get("marketSymbol", ""),
                currency.get("source", "manual"),
                currency.get("lastSyncAt", ""),
                currency.get("lastSyncStatus", ""),
                currency.get("lastSyncMessage", ""),
            ),
        )
        db.execute("DELETE FROM price_history WHERE currency_id = ?", (currency["id"],))
        history = list(currency.get("history") or [currency.get("price", 0)])[-30:]
        for index, price in enumerate(history):
            db.execute(
                """
                INSERT INTO price_history (id, currency_id, price, recorded_at, position)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    f"{currency['id']}-{index}",
                    currency["id"],
                    float(price),
                    currency.get("lastSyncAt") or currency.get("createdAt") or "",
                    index,
                ),
            )

    wallet_ids = []
    for wallet in data.get("wallets", []):
        wallet_ids.append(wallet["id"])
        db.execute(
            """
            INSERT INTO wallets (id, user_id, currency_id, amount, updated_at, is_simulated)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                user_id = excluded.user_id,
                currency_id = excluded.currency_id,
                amount = excluded.amount,
                updated_at = excluded.updated_at,
                is_simulated = excluded.is_simulated
            """,
            (
                wallet["id"],
                wallet["userId"],
                wallet["currencyId"],
                float(wallet.get("amount", 0)),
                wallet.get("updatedAt", ""),
                bool_int(wallet.get("isSimulated")),
            ),
        )

    if wallet_ids:
        placeholders = ",".join("?" for _ in wallet_ids)
        db.execute(f"DELETE FROM wallets WHERE is_simulated = 1 AND id NOT IN ({placeholders})", wallet_ids)
    else:
        db.execute("DELETE FROM wallets WHERE is_simulated = 1")

    transaction_ids = []
    for transaction in data.get("transactions", []):
        transaction_ids.append(transaction["id"])
        db.execute(
            """
            INSERT INTO transactions
            (id, user_id, currency_id, side, quantity, price, total, status, created_at, is_simulated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                user_id = excluded.user_id,
                currency_id = excluded.currency_id,
                side = excluded.side,
                quantity = excluded.quantity,
                price = excluded.price,
                total = excluded.total,
                status = excluded.status,
                created_at = excluded.created_at,
                is_simulated = excluded.is_simulated
            """,
            (
                transaction["id"],
                transaction["userId"],
                transaction["currencyId"],
                transaction.get("side", ""),
                float(transaction.get("quantity", 0)),
                float(transaction.get("price", 0)),
                float(transaction.get("total", 0)),
                transaction.get("status", "Исполнено"),
                transaction.get("createdAt", ""),
                bool_int(transaction.get("isSimulated")),
            ),
        )

    if transaction_ids:
        placeholders = ",".join("?" for _ in transaction_ids)
        db.execute(f"DELETE FROM transactions WHERE is_simulated = 1 AND id NOT IN ({placeholders})", transaction_ids)
    else:
        db.execute("DELETE FROM transactions WHERE is_simulated = 1")

    settings = data.get("settings") or {}
    db.execute("DELETE FROM system_settings")
    db.execute(
        """
        INSERT INTO system_settings
        (id, simulation_enabled, simulation_level, last_simulation_at, simulation_users_target, simulation_trades_per_minute, simulation_carry)
        VALUES ('main', ?, ?, ?, ?, ?, ?)
        """,
        (
            bool_int(settings.get("simulationEnabled")),
            int(settings.get("simulationLevel", 35)),
            settings.get("lastSimulationAt", ""),
            int(settings.get("simulationUsersTarget", 4)),
            int(settings.get("simulationTradesPerMinute", 6)),
            float(settings.get("simulationCarry", 0)),
        ),
    )


def update_state(payload: dict[str, Any]) -> dict[str, Any]:
    with connect() as db:
        try:
            db.execute("BEGIN")
            if "users" in payload:
                replace_users(db, payload["users"] or [])
            if "data" in payload:
                replace_data(db, payload["data"] or {})
            db.commit()
        except Exception:
            db.rollback()
            raise
    return state_from_db()


def fetch_binance_klines(symbol: str, interval: str, limit: int) -> list[dict[str, Any]]:
    safe_symbol = "".join(character for character in symbol.upper() if character.isalnum())[:20]
    safe_interval = interval if interval in {"1m", "5m", "15m", "1h"} else "1m"
    safe_limit = max(20, min(500, int(limit or 120)))
    query = urlencode({"symbol": safe_symbol, "interval": safe_interval, "limit": safe_limit})
    request = Request(
        f"https://api.binance.com/api/v3/klines?{query}",
        headers={"User-Agent": "CryptoTradeCourseProject/1.0"},
    )

    with urlopen(request, timeout=8) as response:
        payload = json.loads(response.read().decode("utf-8"))

    candles = []
    for row in payload:
        candles.append(
            {
                "time": int(row[0] // 1000),
                "open": float(row[1]),
                "high": float(row[2]),
                "low": float(row[3]),
                "close": float(row[4]),
                "volume": float(row[5]),
                "source": "Binance",
            }
        )
    return candles


def coinbase_product(symbol: str) -> str:
    normalized = "".join(character for character in symbol.upper() if character.isalnum())

    if normalized.endswith("USDT"):
        return f"{normalized[:-4]}-USD"
    if normalized.endswith("USD"):
        return f"{normalized[:-3]}-USD"
    return f"{normalized}-USD"


def fetch_coinbase_candles(symbol: str, interval: str, limit: int) -> list[dict[str, Any]]:
    granularity_map = {"1m": 60, "5m": 300, "15m": 900, "1h": 3600}
    granularity = granularity_map.get(interval, 60)
    safe_limit = max(20, min(300, int(limit or 120)))
    query = urlencode({"granularity": granularity})
    request = Request(
        f"https://api.exchange.coinbase.com/products/{coinbase_product(symbol)}/candles?{query}",
        headers={"User-Agent": "CryptoTradeCourseProject/1.0"},
    )

    with urlopen(request, timeout=8) as response:
        payload = json.loads(response.read().decode("utf-8"))

    candles = []
    for row in sorted(payload, key=lambda item: item[0])[-safe_limit:]:
        candles.append(
            {
                "time": int(row[0]),
                "open": float(row[3]),
                "high": float(row[2]),
                "low": float(row[1]),
                "close": float(row[4]),
                "volume": float(row[5]) if len(row) > 5 else 0,
                "source": "Coinbase",
            }
        )
    return candles


def fetch_klines(symbol: str, interval: str, limit: int) -> list[dict[str, Any]]:
    errors = []

    for provider in (fetch_binance_klines, fetch_coinbase_candles):
        try:
            candles = provider(symbol, interval, limit)
            if candles:
                return candles
        except Exception as error:
            errors.append(str(error))

    raise RuntimeError("Market candle sources are unavailable: " + "; ".join(errors))


class CryptoTradeHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(ROOT_DIR), **kwargs)

    def api_response(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/state":
            self.api_response(HTTPStatus.OK, state_from_db())
            return
        if path == "/api/health":
            self.api_response(HTTPStatus.OK, {"ok": True, "database": str(DB_PATH)})
            return
        if path == "/api/klines":
            params = parse_qs(parsed.query)
            try:
                candles = fetch_klines(
                    params.get("symbol", ["BTCUSDT"])[0],
                    params.get("interval", ["1m"])[0],
                    int(params.get("limit", ["120"])[0]),
                )
                self.api_response(HTTPStatus.OK, {"ok": True, "candles": candles})
            except Exception as error:
                self.api_response(HTTPStatus.BAD_GATEWAY, {"ok": False, "message": str(error), "candles": []})
            return
        if path.endswith(".db"):
            self.api_response(HTTPStatus.FORBIDDEN, {"ok": False, "message": "Database file is not a static asset"})
            return
        super().do_GET()

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path != "/api/state":
            self.api_response(HTTPStatus.NOT_FOUND, {"ok": False, "message": "API endpoint not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            state = update_state(payload)
            self.api_response(HTTPStatus.OK, {"ok": True, "state": state})
        except Exception as error:
            self.api_response(HTTPStatus.BAD_REQUEST, {"ok": False, "message": str(error)})


def run_server() -> None:
    init_db()
    server = ThreadingHTTPServer((HOST, PORT), CryptoTradeHandler)
    print("CryptoTrade backend")
    print(f"Site: http://{HOST}:{PORT}/index.html")
    print(f"SQLite database: {DB_PATH}")
    print("Stop: Ctrl+C")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
