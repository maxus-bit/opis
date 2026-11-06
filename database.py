import math
import sqlite3
from pathlib import Path
from typing import List, Optional, Tuple


DATABASE_NAME = "project.db"
DATABASE_PATH = Path(__file__).resolve().with_name(DATABASE_NAME)


def get_connection() -> sqlite3.Connection:
    """Створює підключення до SQLite з увімкненими зовнішніми ключами."""
    connection = sqlite3.connect(DATABASE_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def create_tables() -> None:
    """Створює таблиці пального, заправників і замовлень."""
    connection = get_connection()
    try:
        with connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS fuels (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    price_per_liter REAL NOT NULL,
                    stock_liters REAL NOT NULL,
                    status TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS refuelers (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    shift INTEGER NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS refueling_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fuel_id INTEGER NOT NULL,
                    refueler_id INTEGER NOT NULL,
                    liters REAL NOT NULL,
                    total_price REAL NOT NULL,
                    order_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (fuel_id) REFERENCES fuels(id) ON DELETE CASCADE,
                    FOREIGN KEY (refueler_id) REFERENCES refuelers(id)
                )
                """
            )
    finally:
        connection.close()


def add_initial_data() -> None:
    """Додає початкове пальне та оператора, якщо їх ще немає."""
    initial_fuels = [
        (1, "LPG Propan-Butan (Standard)", 34.50, 4500.0, "Available"),
        (2, "LPG Mustang Premium", 35.90, 3200.0, "Available"),
        (3, "LPG Euro 5", 34.90, 5100.0, "Available"),
        (4, "LPG Eco Clean", 35.20, 1500.0, "Available"),
        (5, "LPG Winter Mix", 36.00, 800.0, "Low Stock"),
    ]

    connection = get_connection()
    try:
        with connection:
            fuel_count = connection.execute(
                "SELECT COUNT(*) FROM fuels"
            ).fetchone()[0]
            if fuel_count == 0:
                connection.executemany(
                    """
                    INSERT INTO fuels
                        (id, name, price_per_liter, stock_liters, status)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    initial_fuels,
                )

            connection.execute(
                """
                INSERT OR IGNORE INTO refuelers (id, name, shift)
                VALUES (?, ?, ?)
                """,
                (101, "Олексій Петренко", 1),
            )
    finally:
        connection.close()


def get_fuels() -> List[Tuple]:
    """Повертає всі види пального, відсортовані за ID."""
    connection = get_connection()
    try:
        return connection.execute(
            """
            SELECT id, name, price_per_liter, stock_liters, status
            FROM fuels
            ORDER BY id
            """
        ).fetchall()
    finally:
        connection.close()


def add_fuel(
    fuel_id: int,
    name: str,
    price_per_liter: float,
    stock_liters: float,
) -> bool:
    """Додає пальне; повертає False, якщо ID вже зайнятий."""
    if (
        fuel_id <= 0
        or not name.strip()
        or not math.isfinite(price_per_liter)
        or not math.isfinite(stock_liters)
        or price_per_liter <= 0
        or stock_liters < 0
    ):
        raise ValueError("Некоректні дані пального.")

    status = "Available" if stock_liters >= 1000 else "Low Stock"
    connection = get_connection()
    try:
        with connection:
            try:
                connection.execute(
                    """
                    INSERT INTO fuels
                        (id, name, price_per_liter, stock_liters, status)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (fuel_id, name.strip(), price_per_liter, stock_liters, status),
                )
            except sqlite3.IntegrityError:
                return False
        return True
    finally:
        connection.close()


def update_fuel_price_stock(
    fuel_id: int,
    price_per_liter: float,
    stock_liters: float,
) -> bool:
    """Оновлює ціну, залишок і статус; повідомляє, чи знайдено пальне."""
    if (
        not math.isfinite(price_per_liter)
        or not math.isfinite(stock_liters)
        or price_per_liter <= 0
        or stock_liters < 0
    ):
        raise ValueError("Ціна має бути > 0, а залишок — >= 0.")

    status = "Available" if stock_liters >= 1000 else "Low Stock"
    connection = get_connection()
    try:
        with connection:
            cursor = connection.execute(
                """
                UPDATE fuels
                SET price_per_liter = ?, stock_liters = ?, status = ?
                WHERE id = ?
                """,
                (price_per_liter, stock_liters, status, fuel_id),
            )
        return cursor.rowcount > 0
    finally:
        connection.close()


def delete_fuel(fuel_id: int) -> bool:
    """Видаляє пальне за ID разом із пов'язаними замовленнями."""
    connection = get_connection()
    try:
        with connection:
            cursor = connection.execute("DELETE FROM fuels WHERE id = ?", (fuel_id,))
        return cursor.rowcount > 0
    finally:
        connection.close()


def delete_all_fuels() -> None:
    """Видаляє всі позиції пального та пов'язані записи заправок."""
    connection = get_connection()
    try:
        with connection:
            connection.execute("DELETE FROM fuels")
    finally:
        connection.close()


def search_fuels(query: str) -> List[Tuple]:
    """Шукає пальне за частиною назви без урахування регістру."""
    connection = get_connection()
    try:
        return connection.execute(
            """
            SELECT id, name, price_per_liter, stock_liters, status
            FROM fuels
            WHERE name LIKE ? COLLATE NOCASE
            ORDER BY name
            """,
            (f"%{query.strip()}%",),
        ).fetchall()
    finally:
        connection.close()


def create_refueling_transaction(
    fuel_id: int,
    refueler_id: int,
    liters: float,
    total_price: float,
) -> Optional[int]:
    """Атомарно зменшує залишок і зберігає замовлення."""
    if (
        not math.isfinite(liters)
        or not math.isfinite(total_price)
        or liters <= 0
        or total_price <= 0
    ):
        raise ValueError("Об'єм і сума замовлення мають бути додатними числами.")

    connection = get_connection()
    try:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            "SELECT stock_liters FROM fuels WHERE id = ?",
            (fuel_id,),
        ).fetchone()
        if row is None or row[0] < liters:
            connection.rollback()
            return None

        new_stock = row[0] - liters
        new_status = "Available" if new_stock >= 1000 else "Low Stock"
        connection.execute(
            "UPDATE fuels SET stock_liters = ?, status = ? WHERE id = ?",
            (new_stock, new_status, fuel_id),
        )
        cursor = connection.execute(
            """
            INSERT INTO refueling_orders
                (fuel_id, refueler_id, liters, total_price)
            VALUES (?, ?, ?, ?)
            """,
            (fuel_id, refueler_id, liters, total_price),
        )
        order_id = cursor.lastrowid
        connection.commit()
        return order_id
    except sqlite3.Error:
        connection.rollback()
        raise
    finally:
        connection.close()


def get_refueling_orders_joined() -> List[Tuple]:
    """Повертає заправки разом із назвами пального та заправника."""
    connection = get_connection()
    try:
        return connection.execute(
            """
            SELECT
                refueling_orders.id,
                fuels.name,
                refuelers.name,
                refueling_orders.liters,
                refueling_orders.total_price,
                refueling_orders.order_date
            FROM refueling_orders
            JOIN fuels ON refueling_orders.fuel_id = fuels.id
            JOIN refuelers ON refueling_orders.refueler_id = refuelers.id
            ORDER BY refueling_orders.id DESC
            """
        ).fetchall()
    finally:
        connection.close()
