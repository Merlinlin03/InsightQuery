"""Build DataAgent metadata from the dedicated short-drama Doris DDL."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "dbmock" / "schema.sql"
OUTPUT = ROOT / "conf" / "meta_config.yaml"

TABLE_DESCRIPTIONS = {
    "dim_market": "海外短剧市场维度，每个市场一行。",
    "dim_series": "合成短剧内容维度，含题材与AI辅助制作分类标签。",
    "dim_episode": "短剧集数维度，第三集为付费解锁集。",
    "dim_user": "匿名合成用户维度，注册日期和市场用于分群。",
    "fact_episode_view": "每次短剧播放事件，支持第一集到第二集续看、完播分析。",
    "fact_paywall_event": "第三集付费墙展示事件，每条记录对应一次展示。",
    "fact_purchase": "短剧解锁交易，只有status为success计入收入。",
}
ALIASES = {
    "country_code": ["国家", "市场", "国家代码"],
    "language_code": ["语言", "内容语言"],
    "title": ["短剧名称", "剧名"],
    "genre": ["题材", "短剧题材"],
    "content_origin": ["内容来源", "AI辅助制作"],
    "episode_no": ["集数", "第几集"],
    "is_paywalled": ["付费集", "是否付费解锁"],
    "event_date": ["日期", "统计日"],
    "started": ["开播", "播放开始"],
    "completed": ["完播", "播放完成"],
    "event_type": ["付费墙事件类型"],
    "amount_usd": ["解锁收入", "美元金额"],
    "status": ["交易状态", "支付状态"],
}
INDEX_VALUES = {
    ("dim_market", "country_code"),
    ("dim_market", "language_code"),
    ("dim_series", "title"),
    ("dim_series", "genre"),
    ("dim_series", "content_origin"),
    ("fact_purchase", "status"),
}
REFERENCES = {
    ("dim_episode", "series_id"): ("dim_series", "series_id"),
    ("dim_user", "market_id"): ("dim_market", "market_id"),
    ("fact_episode_view", "user_id"): ("dim_user", "user_id"),
    ("fact_episode_view", "episode_id"): ("dim_episode", "episode_id"),
    ("fact_paywall_event", "user_id"): ("dim_user", "user_id"),
    ("fact_paywall_event", "episode_id"): ("dim_episode", "episode_id"),
    ("fact_purchase", "user_id"): ("dim_user", "user_id"),
    ("fact_purchase", "episode_id"): ("dim_episode", "episode_id"),
}


def metric(name: str, description: str, *columns: tuple[str, str], alias: list[str] | None = None) -> dict:
    return {
        "name": name,
        "description": description,
        "relevant_columns": [{"t_name": table, "c_name": column} for table, column in columns],
        "alias": alias or [],
    }


METRICS = [
    metric(
        "开播用户数",
        "周期内started=1的去重user_id；按剧集分析时先关联dim_episode和dim_series。",
        ("fact_episode_view", "user_id"), ("fact_episode_view", "started"),
        ("fact_episode_view", "episode_id"), alias=["观看用户", "播放用户"],
    ),
    metric(
        "次集续看率",
        "同一周期、同一剧中观看第1集的用户里，继续观看第2集的去重用户数 / 观看第1集的去重用户数；按用户匹配，不平均各剧比率。",
        ("fact_episode_view", "user_id"), ("fact_episode_view", "episode_id"),
        ("dim_episode", "episode_no"), ("dim_episode", "series_id"),
        alias=["第2集续看率", "二集续看率"],
    ),
    metric(
        "单集完播率",
        "sum(completed) / nullif(sum(started),0)，分析时限定相同集数、市场与日期窗口。",
        ("fact_episode_view", "completed"), ("fact_episode_view", "started"),
        ("fact_episode_view", "episode_id"),
        alias=["完播率"],
    ),
    metric(
        "付费墙展示用户数",
        "event_type='impression'的去重user_id；按剧集与市场拆解时保留同一统计粒度。",
        ("fact_paywall_event", "user_id"), ("fact_paywall_event", "event_type"),
        ("fact_paywall_event", "episode_id"),
        alias=["付费墙曝光用户"],
    ),
    metric(
        "成功解锁用户数",
        "status='success'的去重user_id；失败交易不计入。",
        ("fact_purchase", "user_id"), ("fact_purchase", "status"),
        ("fact_purchase", "episode_id"),
        alias=["付费用户", "解锁用户"],
    ),
    metric(
        "付费解锁转化率",
        "同一周期、同一剧集中付费墙展示用户里成功解锁的去重用户数 / 付费墙展示去重用户数；按用户匹配，零分母返回不可计算，不直接平均分组比率。",
        ("fact_purchase", "user_id"), ("fact_purchase", "status"),
        ("fact_paywall_event", "user_id"), ("fact_paywall_event", "event_type"),
        alias=["付费墙转化率", "解锁转化率"],
    ),
    metric(
        "成功解锁收入",
        "sum(fact_purchase.amount_usd) where status='success'，单位美元；失败交易不计入，按剧集/市场分项金额可加总。",
        ("fact_purchase", "amount_usd"), ("fact_purchase", "status"),
        ("fact_purchase", "episode_id"),
        alias=["短剧收入", "付费收入", "解锁收入"],
    ),
]


def build() -> dict:
    text = SCHEMA.read_text(encoding="utf-8")
    tables = []
    seen_columns = set()
    for table_name, body in re.findall(r"CREATE TABLE (\w+) \((.*?)\)\s*ENGINE", text, re.S):
        columns = []
        for column_name, description in re.findall(
            r"^\s+(\w+)\s+[A-Z][A-Z0-9(),]*\s+.*?COMMENT '([^']+)'",
            body,
            re.M,
        ):
            ref = REFERENCES.get((table_name, column_name))
            column = {
                "name": column_name,
                "description": description,
                "alias": ALIASES.get(column_name, []),
                "index_values": (table_name, column_name) in INDEX_VALUES,
            }
            if ref:
                column["reference_t_name"], column["reference_c_name"] = ref
            columns.append(column)
            seen_columns.add((table_name, column_name))
        assert columns, table_name
        tables.append({
            "name": table_name,
            "role": "fact" if table_name.startswith("fact_") else "dim",
            "description": TABLE_DESCRIPTIONS[table_name],
            "columns": columns,
        })
    assert set(TABLE_DESCRIPTIONS) == {table["name"] for table in tables}
    for definition in METRICS:
        for ref in definition["relevant_columns"]:
            assert (ref["t_name"], ref["c_name"]) in seen_columns, ref
    return {"tables": tables, "metrics": METRICS}


if __name__ == "__main__":
    OUTPUT.write_text(
        json.dumps(build(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {OUTPUT}")
