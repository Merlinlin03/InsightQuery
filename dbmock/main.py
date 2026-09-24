"""Deterministic, anonymous short-drama sample data for a dedicated Doris database."""

from __future__ import annotations

import argparse
import json
import os
import re
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

START_DATE = date(2026, 9, 1)
DATABASE = "insightquery_short_drama"
TABLES = (
    "dim_market",
    "dim_series",
    "dim_episode",
    "dim_user",
    "fact_episode_view",
    "fact_paywall_event",
    "fact_purchase",
)


def build_rows() -> dict[str, list[tuple]]:
    """Create two comparable seven-day windows with a deliberate US series change."""
    rows: dict[str, list[tuple]] = {name: [] for name in TABLES}
    rows["dim_market"] = [
        (1, "US", "en", "North America"),
        (2, "MX", "es", "LATAM"),
        (3, "BR", "pt", "LATAM"),
    ]
    rows["dim_series"] = [
        (1, "Midnight Contract", "Romance", "ai_assisted", START_DATE),
        (2, "Neon Promise", "Romance", "ai_assisted", START_DATE),
        (3, "The Last Signal", "Suspense", "ai_assisted", START_DATE),
        (4, "Second Horizon", "SciFi", "traditional", START_DATE),
    ]
    rows["dim_episode"] = [
        (series_id * 10 + episode_no, series_id, episode_no, int(episode_no == 3))
        for series_id in range(1, 5)
        for episode_no in range(1, 4)
    ]
    view_id = paywall_id = purchase_id = 0
    for day_index in range(14):
        event_date = START_DATE + timedelta(days=day_index)
        comparison = day_index >= 7
        for market_id in range(1, 4):
            for series_id in range(1, 5):
                affected = comparison and market_id == 1 and series_id == 1
                audience = 24 if market_id == 1 else 20
                for slot in range(audience):
                    user_id = (day_index + 1) * 100000 + market_id * 10000 + series_id * 1000 + slot
                    rows["dim_user"].append(
                        (user_id, market_id, event_date, "organic" if slot % 2 else "recommendation")
                    )
                    ep1_completed = slot < audience - 3
                    view_id += 1
                    rows["fact_episode_view"].append(
                        (view_id, user_id, series_id * 10 + 1, event_date, 1, int(ep1_completed), 75 if ep1_completed else 18)
                    )
                    next_episode_limit = 9 if affected else audience - 6
                    if slot >= next_episode_limit:
                        continue
                    ep2_completed = slot < next_episode_limit - 2
                    view_id += 1
                    rows["fact_episode_view"].append(
                        (view_id, user_id, series_id * 10 + 2, event_date, 1, int(ep2_completed), 76 if ep2_completed else 21)
                    )
                    if not ep2_completed:
                        continue
                    paywall_id += 1
                    rows["fact_paywall_event"].append(
                        (paywall_id, user_id, series_id * 10 + 3, event_date, "impression")
                    )
                    purchase_limit = 2 if affected else (5 if market_id == 1 else 4)
                    if slot > purchase_limit:
                        continue
                    purchase_id += 1
                    successful = slot < purchase_limit
                    price = Decimal("1.99") if series_id == 1 else Decimal("2.49")
                    rows["fact_purchase"].append(
                        (purchase_id, user_id, series_id * 10 + 3, event_date, price, "success" if successful else "failed")
                    )
                    if successful:
                        view_id += 1
                        rows["fact_episode_view"].append(
                            (view_id, user_id, series_id * 10 + 3, event_date, 1, 1, 84)
                        )
    return rows


def summarize(rows: dict[str, list[tuple]]) -> dict:
    """Validate foreign keys and produce auditable baseline/current aggregates."""
    users = {row[0] for row in rows["dim_user"]}
    episodes = {row[0] for row in rows["dim_episode"]}
    for table, user_col, episode_col in (
        ("fact_episode_view", 1, 2),
        ("fact_paywall_event", 1, 2),
        ("fact_purchase", 1, 2),
    ):
        for row in rows[table]:
            assert row[user_col] in users and row[episode_col] in episodes, table
    for table, table_rows in rows.items():
        assert len(table_rows) == len({row[0] for row in table_rows}), table

    starts: dict[tuple[str, int, int], int] = defaultdict(int)
    paywalls: dict[tuple[str, int, int], int] = defaultdict(int)
    purchases: dict[tuple[str, int, int], int] = defaultdict(int)
    revenue: dict[tuple[str, int, int], Decimal] = defaultdict(Decimal)
    user_market = {row[0]: row[1] for row in rows["dim_user"]}

    def key(user_id: int, episode_id: int, event_date: date) -> tuple[str, int, int]:
        period = "baseline" if event_date < START_DATE + timedelta(days=7) else "current"
        return period, user_market[user_id], episode_id // 10

    for _, user_id, episode_id, event_date, started, *_ in rows["fact_episode_view"]:
        if episode_id % 10 == 2 and started:
            starts[key(user_id, episode_id, event_date)] += 1
    for _, user_id, episode_id, event_date, event_type in rows["fact_paywall_event"]:
        assert event_type == "impression"
        paywalls[key(user_id, episode_id, event_date)] += 1
    for _, user_id, episode_id, event_date, amount, status in rows["fact_purchase"]:
        if status == "success":
            purchases[key(user_id, episode_id, event_date)] += 1
            revenue[key(user_id, episode_id, event_date)] += amount
    assert sum(revenue.values()) == sum(
        row[4] for row in rows["fact_purchase"] if row[5] == "success"
    )
    us_series = [("baseline", 1, 1), ("current", 1, 1)]
    assert starts[us_series[1]] < starts[us_series[0]]
    assert purchases[us_series[1]] < purchases[us_series[0]]
    return {
        "rows": {name: len(value) for name, value in rows.items()},
        "us_midnight_contract": {
            period: {
                "episode_2_starts": starts[(period, 1, 1)],
                "paywall_users": paywalls[(period, 1, 1)],
                "successful_unlocks": purchases[(period, 1, 1)],
                "revenue_usd": str(revenue[(period, 1, 1)]),
            }
            for period in ("baseline", "current")
        },
    }


def load_doris(rows: dict[str, list[tuple]]) -> None:
    """Insert into a fresh dedicated database; never replace existing tables."""
    import pymysql

    password = os.environ["DB_PASSWORD"]
    db_name = os.environ.get("DB_NAME", DATABASE)
    if db_name != DATABASE or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", db_name):
        raise ValueError(f"只允许初始化专用数据库 {DATABASE}")
    connection = pymysql.connect(
        host=os.environ.get("DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("DB_PORT", "9031")),
        user=os.environ.get("DB_USER", "atguigu"),
        password=password,
        autocommit=True,
        charset="utf8mb4",
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
            cursor.execute(f"USE {db_name}")
            cursor.execute("SHOW TABLES")
            if cursor.fetchall():
                raise RuntimeError(f"{db_name} 已有数据表，拒绝覆盖")
            schema = (Path(__file__).parent / "schema.sql").read_text(encoding="utf-8")
            for statement in schema.split(";"):
                if statement.strip():
                    cursor.execute(statement)
            for table in TABLES:
                table_rows = rows[table]
                placeholders = ", ".join(["%s"] * len(table_rows[0]))
                statement = f"INSERT INTO {table} VALUES ({placeholders})"
                for offset in range(0, len(table_rows), 500):
                    cursor.executemany(statement, table_rows[offset : offset + 500])
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="InsightQuery 合成短剧数据")
    parser.add_argument("--load", action="store_true", help="写入空的专用 Doris 数据库")
    args = parser.parse_args()
    rows = build_rows()
    print(json.dumps(summarize(rows), ensure_ascii=False, indent=2))
    if args.load:
        load_doris(rows)
        print("Doris 专用数据库初始化完成")


if __name__ == "__main__":
    main()
