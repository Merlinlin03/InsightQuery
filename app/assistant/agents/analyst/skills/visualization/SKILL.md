---
name: visualization
description: 将 Analyst 已验证的分析结果制作成专业、美观、清晰的自包含 HTML 报告与图表。采用结构化排版、分栏网格与降噪设计；用于最终可视化、综合报告与展示交付。
---

# 专业商业数据可视化与 HTML 报告规范

## 1. 设计核心理念：结构化排版与认知降噪

报告混乱的根源通常在于**缺乏视觉层级**、**过多指标平铺**、**大段文字堆积**与**单列无限下滚**。优秀的分析报告必须遵循 **MECE 原则** 与 **BLUF（Bottom Line Up Front，结论前置）**，做到：

1. **强视觉层级（Visual Hierarchy）**：
   - **Hero KPI 只放 3~4 个核心指标**，严禁并排堆叠 8~10 个无主次的指标卡片；次要与诊断指标放入结构化小表。
   - **图文联动分栏（Split View）**：大盘走势图与核心业务发现左右分栏并排（6:4），让读者“左眼看图、右眼读结论”。
2. **结构化卡片（Componentized Cards）**：
   - 杜绝长篇大论的自然段；将类目分级、归因拆解放入“🟢 增长驱动 / 🔴 下滑预警 / ⚪ 结构切换”的分栏矩阵卡片中。
3. **表格视觉增强（Visualized Tables）**：
   - 表格不只填纯数字：为份额字段配置内联迷你进度条（Progress Mini-bar），为环比/增速配置红绿胶囊 Badge，提升扫描效率。
4. **技术细节下沉折叠（Collapsible Appendix）**：
   - 复杂的 SQL 逻辑、多口径核对表、数据字典使用原生 `<details class="accordion">` 封装，供深入审计时展开，不干扰正文主线阅读。
5. **严禁在 HTML 中输出内部文件路径（No Server Paths）**：
   - **绝对禁止**在 HTML 报告中展示服务器内部路径（如 `/data/...`、容器目录、本地文件路径、脚本文件名等）。用户在浏览器中无法访问服务器本地文件，输出路径不仅无用，还会破坏排版。数据溯源只需陈述数据源表名、业务口径、统计周期与样本量。
6. **完全自包含（Zero Dependency）**：
   - 纯内联 CSS，所有图表转为 Base64，无需外部网络，支持 `<details>` 原生无 JS 展开收起。

---

## 2. 报告标准信息架构（Information Architecture）

一份标准的商业分析报告由以下六大模块构成：

```text
┌─────────────────────────────────────────────────────────────┐
│ 1. 简洁顶部 Header：报告主标题 + 关键元数据胶囊 (窗口/口径/版本)  │
├─────────────────────────────────────────────────────────────┤
│ 2. 核心 KPI 矩阵 (3~4 个 Hero Cards，大字号 + 涨跌对比胶囊)    │
├──────────────────────────────┬──────────────────────────────┤
│ 3. 总体趋势走势图 (Base64)    │ 3. 核心业务判断 (3~4 条关键发现)│
│    (左侧 58% 宽度)           │    (右侧 42% 结构化卡片)     │
├──────────────────────────────┴──────────────────────────────┤
│ 4. 结构与归因矩阵卡片 (分栏：🟢 增长引擎 / 🔴 承压类目 / ⚪ 波动) │
├─────────────────────────────────────────────────────────────┤
│ 5. 重点维度明细数据表 (带份额迷你进度条 + 增长率 Badge)        │
├─────────────────────────────────────────────────────────────┤
│ 6. 深入下钻图表区 (2 列并排图表卡片)                          │
├─────────────────────────────────────────────────────────────┤
│ 7. 可折叠附录 (<details> 封装多口径核对、方法限制与 SQL 溯源)   │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 标准 HTML 报告模板与内联 CSS 系统

生成最终 HTML 时，必须直接使用并遵循以下结构化样式系统：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>分析报告标题</title>
<style>
  :root {
    --bg-page: #f8fafc;
    --bg-card: #ffffff;
    --border: #e2e8f0;
    --border-hover: #cbd5e1;
    --text-main: #0f172a;
    --text-sub: #334155;
    --text-muted: #64748b;
    --text-light: #94a3b8;
    --blue: #2563eb;
    --blue-bg: #eff6ff;
    --blue-border: #bfdbfe;
    --green: #059669;
    --green-bg: #ecfdf5;
    --green-border: #a7f3d0;
    --red: #dc2626;
    --red-bg: #fef2f2;
    --red-border: #fecaca;
    --amber: #d97706;
    --amber-bg: #fffbeb;
    --amber-border: #fde68a;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "WenQuanYi Zen Hei", sans-serif;
    background-color: var(--bg-page);
    color: var(--text-sub);
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
  }

  .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 32px 24px 80px;
  }

  /* 1. 报告头部 */
  .report-header {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 24px 28px;
    margin-bottom: 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
  }

  .header-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 10px;
  }

  .report-title {
    font-size: 24px;
    font-weight: 700;
    color: var(--text-main);
    letter-spacing: -0.02em;
  }

  .meta-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 8px;
  }

  .meta-pill {
    display: inline-flex;
    align-items: center;
    background: #f1f5f9;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 3px 10px;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-sub);
  }

  /* 2. 核心 KPI 网格 (严格限制 3~4 个卡片) */
  .hero-kpis {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
  }

  .kpi-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 18px 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    position: relative;
  }

  .kpi-card.primary {
    border-top: 3px solid var(--blue);
  }

  .kpi-title {
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--text-muted);
    margin-bottom: 6px;
  }

  .kpi-value {
    font-size: 26px;
    font-weight: 700;
    color: var(--text-main);
    font-variant-numeric: tabular-nums;
    line-height: 1.2;
  }

  .kpi-meta {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    margin-top: 8px;
    color: var(--text-muted);
  }

  /* 胶囊标签 */
  .badge {
    display: inline-flex;
    align-items: center;
    gap: 3px;
    font-size: 11.5px;
    font-weight: 600;
    padding: 2px 7px;
    border-radius: 4px;
  }
  .badge-pos { background: var(--green-bg); color: var(--green); border: 1px solid var(--green-border); }
  .badge-neg { background: var(--red-bg); color: var(--red); border: 1px solid var(--red-border); }
  .badge-neutral { background: #f1f5f9; color: var(--text-muted); border: 1px solid var(--border); }

  /* 3. 分栏布局 (左右并排) */
  .split-row {
    display: grid;
    grid-template-columns: 1.4fr 1fr;
    gap: 20px;
    margin-bottom: 28px;
    align-items: stretch;
  }

  @media (max-width: 900px) {
    .split-row { grid-template-columns: 1fr; }
  }

  .panel-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    display: flex;
    flex-direction: column;
  }

  .panel-title {
    font-size: 15px;
    font-weight: 600;
    color: var(--text-main);
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid #f1f5f9;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  /* 结构化结论条目 */
  .insight-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
    list-style: none;
    flex: 1;
  }

  .insight-item {
    background: #f8fafc;
    border: 1px solid var(--border);
    border-left: 3px solid var(--blue);
    border-radius: 8px;
    padding: 12px 14px;
    font-size: 13px;
    line-height: 1.6;
  }

  .insight-item.danger { border-left-color: var(--red); }
  .insight-item.success { border-left-color: var(--green); }
  .insight-item.warning { border-left-color: var(--amber); }

  .insight-item b {
    color: var(--text-main);
    font-weight: 600;
  }

  /* 4. 类目分级卡片阵列 (三列/两列网格) */
  .segment-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 16px;
    margin-bottom: 28px;
  }

  .segment-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px 18px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
  }

  .segment-card.growth { border-top: 3px solid var(--green); }
  .segment-card.drop { border-top: 3px solid var(--red); }
  .segment-card.stable { border-top: 3px solid var(--text-muted); }

  .segment-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
  }

  .segment-title {
    font-size: 14px;
    font-weight: 700;
    color: var(--text-main);
  }

  .segment-body {
    font-size: 13px;
    color: var(--text-sub);
    line-height: 1.6;
  }

  /* 5. 增强数据表格 */
  .table-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    margin-bottom: 28px;
  }

  .table-header-box {
    padding: 16px 20px;
    border-bottom: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .table-title {
    font-size: 15px;
    font-weight: 600;
    color: var(--text-main);
  }

  .table-scroll {
    overflow-x: auto;
    max-height: 480px;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
    text-align: left;
  }

  th {
    background: #f8fafc;
    color: var(--text-sub);
    font-weight: 600;
    font-size: 12px;
    padding: 10px 14px;
    border-bottom: 1px solid var(--border);
    white-space: nowrap;
    position: sticky;
    top: 0;
    z-index: 1;
  }

  td {
    padding: 9px 14px;
    border-bottom: 1px solid #f1f5f9;
    color: var(--text-sub);
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }

  tbody tr:hover td {
    background: #f8fafc;
  }

  .num { text-align: right; }
  .center { text-align: center; }

  /* 进度条单元格 */
  .bar-cell {
    display: flex;
    align-items: center;
    gap: 8px;
    justify-content: flex-end;
  }

  .bar-bg {
    width: 64px;
    height: 6px;
    background: #e2e8f0;
    border-radius: 3px;
    overflow: hidden;
  }

  .bar-fill {
    height: 100%;
    background: var(--blue);
    border-radius: 3px;
  }

  /* 6. 可折叠附录 (原生无需 JS) */
  details.accordion {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    margin-bottom: 12px;
    overflow: hidden;
    transition: all 0.2s;
  }

  details.accordion summary {
    padding: 14px 18px;
    font-size: 13.5px;
    font-weight: 600;
    color: var(--text-main);
    cursor: pointer;
    user-select: none;
    background: #f8fafc;
    border-bottom: 1px solid transparent;
  }

  details.accordion[open] summary {
    border-bottom-color: var(--border);
    background: var(--bg-card);
  }

  details.accordion .content {
    padding: 16px 18px;
    font-size: 13px;
    line-height: 1.6;
    color: var(--text-sub);
  }

  /* 页脚 */
  .report-footer {
    margin-top: 48px;
    border-top: 1px solid var(--border);
    padding-top: 16px;
    font-size: 12px;
    color: var(--text-muted);
    display: flex;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
  }
</style>
</head>
<body>
<div class="container">
  <header class="report-header">
    <div class="header-top">
      <h1 class="report-title">短剧次集续看与付费解锁变化分析</h1>
      <span class="badge badge-neutral">合成数据</span>
    </div>
    <div class="meta-pills">
      <span class="meta-pill">基准期：2026-09-01 至 2026-09-07</span>
      <span class="meta-pill">对比期：2026-09-08 至 2026-09-14</span>
      <span class="meta-pill">市场：US</span>
    </div>
  </header>
  <section class="section">
    <h2 class="section-title">核心结论</h2>
    <p>从已校验的证据表填入开播用户、次集续看、付费墙展示、成功解锁和收入的基准值、当前值与变化量。</p>
    <p>按短剧与市场展示贡献量，并说明样本量、未解释变化和待验证假设。观察性数据不得写成因果证明。</p>
  </section>
  <section class="section">
    <h2 class="section-title">证据与口径</h2>
    <p>图表和表格必须由本次查询结果生成。付费收入仅计入 status=success 的交易；比率由汇总分子与分母重新计算。</p>
  </section>
  <footer class="report-footer">InsightQuery · AI 短剧运营智数归因 · 合成数据</footer>
</div>
</body>
</html>
```

---

## 4. 图表高清现代美化参数 (Matplotlib / Seaborn)

绘制图表时，必须通过 Python 设置统一的高清现代商务图表风格：

```python
import matplotlib.pyplot as plt

plt.rcParams['figure.dpi'] = 200
plt.rcParams['font.family'] = 'WenQuanYi Zen Hei'
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 10

# 极简配色
PALETTE = {
    'primary': '#2563eb',    # 皇家蓝 (主趋势)
    'success': '#059669',    # 翡翠绿 (正增长)
    'danger': '#dc2626',     # 玫瑰红 (下滑)
    'warning': '#d97706',    # 琥珀金 (预警)
    'slate': '#64748b',      # 中性灰
    'grid': '#f1f5f9',       # 极淡网格
    'bg': '#ffffff',
}

def setup_clean_chart(ax, title=None):
    ax.set_facecolor('#ffffff')
    ax.figure.patch.set_facecolor('#ffffff')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#cbd5e1')
    ax.spines['bottom'].set_color('#cbd5e1')
    ax.yaxis.grid(True, linestyle='--', alpha=0.6, color=PALETTE['grid'])
    ax.xaxis.grid(False)
    if title:
        ax.set_title(title, fontsize=13, weight='bold', color='#0f172a', pad=12)
    ax.tick_params(colors='#475569', labelsize=9.5)
```

---

## 5. 生成报告自检准则 (Quality Checklist)

在保存交付前，对照以下项进行自查：
1. [ ] **无视觉过载**：顶部 Hero KPI 严格控制在 3~4 个以内，没有 8~10 个指标平铺。
2. [ ] **分栏图文对应**：大盘走势图采用 6:4 分栏并排展示，右侧为精炼结论。
3. [ ] **分类结构清晰**：增长/下滑剧集采用分栏卡片（绿色/红色/灰色）组织，而非单一长段落。
4. [ ] **表格带视觉辅助**：主要表格包含占比 mini-bar 或涨跌幅 Badge，表头置顶。
5. [ ] **技术细节折叠**：指标定义、口径对照放入 `<details>` 折叠，保持主干清爽。
6. [ ] **严禁内部文件路径**：HTML 中绝对不出现服务器/容器内部路径（如 `/data/...`、`.parquet/.csv` 本地磁盘路径、`scripts/...` 脚本路径等），溯源仅呈现业务表名、指标与口径。
7. [ ] **完全自包含**：所有图表 Base64 内嵌，离线双击即可完美呈现。
