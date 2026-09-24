# SPEC: InsightQuery AI 短剧运营智数归因

## Overview

以 CommerceLens 为代码基座，构建面向海外 AI 短剧内容消费与付费转化的自然语言问数及指标变化归因系统。沿用其页面布局、Planner/Explorer/Analyst/Reviewer、元数据检索、只读 SQL、沙箱和审查链路；将电商数仓与示例替换为可复现的合成短剧业务。业务场景参考昆仑万维公开的 DramaWave/SkyReels 产品，不声称接入其内部系统或真实数据。

## Scope and success criteria

1. 项目独立位于 `InsightQuery`，源 CommerceLens 不变。
2. 默认业务库、元数据、合成数据、示例问题和 README 均围绕短剧消费、续看与付费解锁。
3. 前端保留 CommerceLens 的布局与交互，仅改品牌、标题、默认示例和必要说明。
4. 合成数据能够解释至少三类变化：续看率、付费解锁转化率、收入；分析必须呈现基准期、对比期、分项贡献与数据限制。
5. 对可加总指标校验分项变化之和等于总变化；比率指标按汇总分子与分母计算。
6. Docker Compose 项目名、服务容器、宿主机端口、数据库、索引和沙箱命名空间与 CommerceLens 隔离。

## Data models

所有业务数据为匿名合成数据。事件保留 `event_date`、`market_id`、`user_id`，时间按 UTC 日统计。核心实体如下：

| Entity | Key fields | Grain / relationship |
| --- | --- | --- |
| `dim_market` | `market_id`, `country_code`, `language_code`, `region` | 每市场一行 |
| `dim_series` | `series_id`, `title`, `genre`, `content_origin`, `release_date` | 每部剧一行；`content_origin` 为合成内容分类 |
| `dim_episode` | `episode_id`, `series_id`, `episode_no`, `is_paywalled` | 每集一行，关联剧集 |
| `dim_user` | `user_id`, `market_id`, `signup_date`, `acquisition_type` | 匿名用户一行；不存个人信息 |
| `fact_episode_view` | `view_id`, `user_id`, `episode_id`, `event_date`, `started`, `completed`, `watch_seconds` | 每次有效播放一行 |
| `fact_paywall_event` | `event_id`, `user_id`, `episode_id`, `event_date`, `event_type` | 每次付费墙展示或解锁尝试一行 |
| `fact_purchase` | `purchase_id`, `user_id`, `episode_id`, `event_date`, `amount_usd`, `status` | 每笔交易一行，仅成功交易计收入 |

业务口径：开播用户为周期内至少一次 `started=1` 的去重用户；完播率为完播播放次数/开播播放次数；次集续看率按同一用户、同一剧、相邻集计算，不直接平均各剧比率；付费解锁转化率为同周期付费墙展示用户中成功购买的去重用户数/付费墙展示去重用户数；收入为成功购买的美元金额。按市场、语言、内容来源、题材和剧集下钻。跨日留存需要另行设计连续用户数据和完整观察窗口，本版合成数据不支持该指标。

## User flows and API contracts

1. 管理员初始化专用 Doris 数据库并生成合成数据；导入 `conf/meta_config.yaml`，后台完成语义索引同步。初始化只作用于专用数据库，已有业务表时拒绝覆盖。
2. 用户登录后在现有聊天页面提问；现有聊天 API 与 SSE/会话契约不变。
3. Planner 委派 Explorer 检索短剧元数据、生成只读 SQL 并查询；归因问题再委派 Analyst 产出证据表及 HTML 报告，Reviewer 复算审查。
4. 三个黄金问题：某市场次集续看率为何变化、哪类剧集贡献了付费解锁转化变化、收入变化主要来自哪些市场与剧集。输出应明确“数据贡献”与“原因假设”的区别。

## File structure

- 复制 CommerceLens 的 `app/`、`web/`、`docker/`、运行配置及必要脚本作为底座，不复制 Git 历史、日志、密钥或电商原始素材。
- `dbmock/`：替换为短剧专用 Doris DDL、确定性合成数据生成与质量校验。
- `conf/meta_config.yaml`：与新 DDL 一致的表、字段、指标语义配置。
- `conf/app_config.yaml`、`conf/.env.example`：默认数据库名改为独立短剧库。
- `app/assistant/agents/*/prompt.py`：仅加入短剧领域约束，保留原 Agent 职责和安全规则。
- `web/src/pages/Chat/components/ChatMessages.tsx` 及必要品牌位置：替换电商问题和可见产品文案，不重做视觉布局。
- `README.md`：产品定位、合成数据说明、启动、三个示例问题、与 GrowthTriage 的边界。

## Edge cases and error handling

- 付费墙分母为零时转化率为不可计算；失败或退款交易不计成功收入。
- 多次播放和多次付费墙展示不得重复计算去重用户指标。
- 剧集跨期上线、未完结观察窗口和小样本在归因报告中标注。
- 不跨表直接相加不同粒度的事实，避免播放与购买 JOIN 放大收入。
- 初始化不得清除源 CommerceLens 数据库；新数据库已有表时停止并提示。
- 外部 LLM、Doris、Elasticsearch、Redis 等依赖不可用时明确报告，不能声称端到端通过。

## Out of scope

- 广告 Campaign/Creative、CPI、ROAS 与用户反馈联合诊断；这些属于 GrowthTriage。
- 接入昆仑万维内部系统、真实用户数据、真实付费流水或外部广告账户。
- AI 短剧生成模型训练、视频生产、素材投放执行及因果效果证明。
- 前端重设计、底座无关的架构重构。

## Open questions

无阻断项。默认以 DramaWave 式短剧消费和付费解锁为业务场景，采用自造品牌剧集与合成数据。
