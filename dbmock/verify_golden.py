"""Run golden SQL against the generated rows without requiring Doris."""

from __future__ import annotations

import re
import sqlite3
from datetime import date
from decimal import Decimal
from pathlib import Path

from main import build_rows, summarize


def local_connection(rows: dict[str, list[tuple]]) -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    ddl = (Path(__file__).parent / "schema.sql").read_text(encoding="utf-8")
    for table, body in re.findall(r"CREATE TABLE (\w+) \((.*?)\)\s*ENGINE", ddl, re.S):
        names = re.findall(r"^\s+(\w+)\s+[A-Z]", body, re.M)
        connection.execute(
            f"CREATE TABLE {table} ({', '.join(f'{name} TEXT' for name in names)})"
        )
        placeholders = ", ".join(["?"] * len(names))
        connection.executemany(
            f"INSERT INTO {table} VALUES ({placeholders})",
            [
                tuple(
                    str(value) if isinstance(value, (date, Decimal)) else value
                    for value in row
                )
                for row in rows[table]
            ],
        )
    return connection


def verify() -> dict:
    rows = build_rows()
    expected = summarize(rows)["us_midnight_contract"]
    connection = local_connection(rows)
    try:
        continuation = connection.execute(
            """
            SELECT CASE WHEN v.event_date < '2026-09-08' THEN 'baseline' ELSE 'current' END period,
                   COUNT(DISTINCT CASE WHEN e.episode_no = 1 THEN v.user_id END) ep1_users,
                   COUNT(DISTINCT CASE WHEN e.episode_no = 2 THEN v.user_id END) ep2_users
            FROM fact_episode_view v
            JOIN dim_episode e ON e.episode_id = v.episode_id
            JOIN dim_user u ON u.user_id = v.user_id
            WHERE u.market_id = 1 AND e.series_id = 1
            GROUP BY period ORDER BY period
            """
        ).fetchall()
        by_period = {period: (ep1, ep2) for period, ep1, ep2 in continuation}
        assert by_period["baseline"] == (168, 126)
        assert by_period["current"] == (168, 63)
        assert by_period["baseline"][1] / by_period["baseline"][0] == 0.75
        assert by_period["current"][1] / by_period["current"][0] == 0.375

        contributions = connection.execute(
            """
            SELECT CASE WHEN p.event_date < '2026-09-08' THEN 'baseline' ELSE 'current' END period,
                   u.market_id, e.series_id, ROUND(SUM(CAST(p.amount_usd AS REAL)), 2) revenue
            FROM fact_purchase p
            JOIN dim_user u ON u.user_id = p.user_id
            JOIN dim_episode e ON e.episode_id = p.episode_id
            WHERE p.status = 'success'
            GROUP BY period, u.market_id, e.series_id
            """
        ).fetchall()
        grouped = {(period, int(market), int(series)): revenue for period, market, series, revenue in contributions}
        baseline = grouped[("baseline", 1, 1)]
        current = grouped[("current", 1, 1)]
        assert round(baseline, 2) == float(expected["baseline"]["revenue_usd"])
        assert round(current, 2) == float(expected["current"]["revenue_usd"])
        total_delta = round(
            sum(value for (period, _, _), value in grouped.items() if period == "current")
            - sum(value for (period, _, _), value in grouped.items() if period == "baseline"),
            2,
        )
        component_delta = round(
            sum(
                grouped.get(("current", market, series), 0)
                - grouped.get(("baseline", market, series), 0)
                for market in range(1, 4)
                for series in range(1, 5)
            ),
            2,
        )
        assert total_delta == component_delta == -41.79

        conversion = connection.execute(
            """
            WITH exposures AS (
              SELECT CASE WHEN w.event_date < '2026-09-08' THEN 'baseline' ELSE 'current' END period,
                     u.market_id, e.series_id, COUNT(DISTINCT w.user_id) exposed_users
              FROM fact_paywall_event w
              JOIN dim_user u ON u.user_id = w.user_id
              JOIN dim_episode e ON e.episode_id = w.episode_id
              WHERE w.event_type = 'impression'
              GROUP BY period, u.market_id, e.series_id
            ), buyers AS (
              SELECT CASE WHEN p.event_date < '2026-09-08' THEN 'baseline' ELSE 'current' END period,
                     u.market_id, e.series_id, COUNT(DISTINCT p.user_id) paid_users
              FROM fact_purchase p
              JOIN dim_user u ON u.user_id = p.user_id
              JOIN dim_episode e ON e.episode_id = p.episode_id
              WHERE p.status = 'success'
              GROUP BY period, u.market_id, e.series_id
            )
            SELECT x.period, x.exposed_users, COALESCE(b.paid_users, 0)
            FROM exposures x
            LEFT JOIN buyers b ON b.period = x.period
                 AND b.market_id = x.market_id AND b.series_id = x.series_id
            WHERE x.market_id = 1 AND x.series_id = 1
            """
        ).fetchall()
        conversion_by_period = {period: (exposed, paid) for period, exposed, paid in conversion}
        assert conversion_by_period == {"baseline": (112, 35), "current": (49, 14)}
        return {
            "continuation_users": by_period,
            "paywall_to_unlock_users": conversion_by_period,
            "us_midnight_revenue_delta_usd": round(current - baseline, 2),
            "total_revenue_delta_usd": total_delta,
        }
    finally:
        connection.close()


if __name__ == "__main__":
    print(verify())
