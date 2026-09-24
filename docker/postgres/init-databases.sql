SELECT 'CREATE DATABASE insightquery_auth OWNER atguigu'
WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = 'insightquery_auth'
)
\gexec

SELECT 'CREATE DATABASE insightquery_meta OWNER atguigu'
WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = 'insightquery_meta'
)
\gexec

SELECT 'CREATE DATABASE insightquery_langgraph OWNER atguigu'
WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = 'insightquery_langgraph'
)
\gexec
