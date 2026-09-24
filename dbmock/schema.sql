-- Synthetic short-drama warehouse for InsightQuery. Dedicated database only.
CREATE TABLE dim_market (
    market_id INT NOT NULL COMMENT '市场ID',
    country_code VARCHAR(8) NOT NULL COMMENT '国家代码',
    language_code VARCHAR(8) NOT NULL COMMENT '内容语言代码',
    region VARCHAR(32) NOT NULL COMMENT '区域'
) ENGINE=OLAP UNIQUE KEY(market_id) DISTRIBUTED BY HASH(market_id) BUCKETS AUTO PROPERTIES ('replication_num'='1');

CREATE TABLE dim_series (
    series_id INT NOT NULL COMMENT '短剧ID',
    title VARCHAR(128) NOT NULL COMMENT '合成短剧名称',
    genre VARCHAR(32) NOT NULL COMMENT '题材',
    content_origin VARCHAR(32) NOT NULL COMMENT '内容制作类型，合成分类标签',
    release_date DATE NOT NULL COMMENT '上线日期'
) ENGINE=OLAP UNIQUE KEY(series_id) DISTRIBUTED BY HASH(series_id) BUCKETS AUTO PROPERTIES ('replication_num'='1');

CREATE TABLE dim_episode (
    episode_id INT NOT NULL COMMENT '剧集ID',
    series_id INT NOT NULL COMMENT '所属短剧ID',
    episode_no INT NOT NULL COMMENT '集数',
    is_paywalled TINYINT NOT NULL COMMENT '是否需付费解锁'
) ENGINE=OLAP UNIQUE KEY(episode_id) DISTRIBUTED BY HASH(episode_id) BUCKETS AUTO PROPERTIES ('replication_num'='1');

CREATE TABLE dim_user (
    user_id BIGINT NOT NULL COMMENT '匿名合成用户ID',
    market_id INT NOT NULL COMMENT '注册市场ID',
    signup_date DATE NOT NULL COMMENT '注册日期',
    acquisition_type VARCHAR(16) NOT NULL COMMENT '自然或推荐来源'
) ENGINE=OLAP UNIQUE KEY(user_id) DISTRIBUTED BY HASH(user_id) BUCKETS AUTO PROPERTIES ('replication_num'='1');

CREATE TABLE fact_episode_view (
    view_id BIGINT NOT NULL COMMENT '播放事件ID',
    user_id BIGINT NOT NULL COMMENT '匿名用户ID',
    episode_id INT NOT NULL COMMENT '剧集ID',
    event_date DATE NOT NULL COMMENT '播放UTC日期',
    started TINYINT NOT NULL COMMENT '是否开播',
    completed TINYINT NOT NULL COMMENT '是否完播',
    watch_seconds INT NOT NULL COMMENT '观看秒数'
) ENGINE=OLAP UNIQUE KEY(view_id) DISTRIBUTED BY HASH(view_id) BUCKETS AUTO PROPERTIES ('replication_num'='1');

CREATE TABLE fact_paywall_event (
    event_id BIGINT NOT NULL COMMENT '付费墙事件ID',
    user_id BIGINT NOT NULL COMMENT '匿名用户ID',
    episode_id INT NOT NULL COMMENT '付费剧集ID',
    event_date DATE NOT NULL COMMENT '展示UTC日期',
    event_type VARCHAR(16) NOT NULL COMMENT '事件类型，当前为impression'
) ENGINE=OLAP UNIQUE KEY(event_id) DISTRIBUTED BY HASH(event_id) BUCKETS AUTO PROPERTIES ('replication_num'='1');

CREATE TABLE fact_purchase (
    purchase_id BIGINT NOT NULL COMMENT '解锁交易ID',
    user_id BIGINT NOT NULL COMMENT '匿名用户ID',
    episode_id INT NOT NULL COMMENT '解锁剧集ID',
    event_date DATE NOT NULL COMMENT '交易UTC日期',
    amount_usd DECIMAL(10,2) NOT NULL COMMENT '交易金额美元',
    status VARCHAR(16) NOT NULL COMMENT 'success或failed'
) ENGINE=OLAP UNIQUE KEY(purchase_id) DISTRIBUTED BY HASH(purchase_id) BUCKETS AUTO PROPERTIES ('replication_num'='1');
