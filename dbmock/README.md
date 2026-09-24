# 合成短剧数据

运行 python main.py 可离线生成并校验两组可比的七日业务数据，输出行数和美国市场示例指标；无需数据库或模型密钥。

专用 Doris 库为 insightquery_short_drama。将 .env.example 复制为 .env，填写连接参数后，在本目录运行 uv run --env-file .env main.py --load，写入七张新表。加载器遇到已有数据表会拒绝覆盖，也拒绝操作其他数据库。不要将 .env 提交到仓库。

日期固定为 2026-09-01 至 2026-09-14，前七天为基准期，后七天为对比期。剧集和用户均为虚构匿名数据，content_origin 是合成分类标签，未使用 DramaWave 内部数据。

修改 schema.sql 后，运行 python build_meta_config.py 更新 ../conf/meta_config.yaml。该文件采用 JSON 语法，兼容 YAML 解析。
