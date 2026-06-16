# -*- coding: utf-8 -*-
"""
第四步：数据可视化展示
======================
基于第二步和第三步的分析结果，生成综合可视化图表和 HTML Dashboard。

图表列表：
  1. 用户行为转化漏斗图
  2. 品类热度排行 Top 15（横向柱状图）
  3. 用户分群雷达图
  4. 用户分群 PCA 散点图
  5. 商品关联网络图
  6. 推荐策略对比图（热门 vs 关联 vs 群体偏好覆盖度）
  7. 综合 HTML Dashboard

输入文件：
  - result/models/hot_products.csv
  - result/models/association_rules.csv
  - result/models/cluster_profiles_business.csv
  - result/models/cluster_category_preferences.csv
  - result/models/recommendations.json
  - result/reports/analysis_summary.json

输出文件：
  - result/figures/step4_funnel.png
  - result/figures/step4_category_ranking.png
  - result/figures/step4_cluster_radar.png
  - result/figures/step4_cluster_pca.png
  - result/figures/step4_association_network.png
  - result/figures/step4_recommendation_comparison.png
  - result/dashboard.html（综合仪表盘）
"""

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # 非交互式后端
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns

# ---------- 路径配置 ----------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULT_MODELS = PROJECT_ROOT / "result" / "models"
RESULT_REPORTS = PROJECT_ROOT / "result" / "reports"
RESULT_FIGURES = PROJECT_ROOT / "result" / "figures"

# 全局 matplotlib 设置（中文字体）
sns.set_style("whitegrid", rc={
    "font.sans-serif": ["SimHei", "Microsoft YaHei"],
    "axes.unicode_minus": False,
})

# 配色
PALETTE = sns.color_palette("Set2", 8)


def ensure_dirs():
    RESULT_FIGURES.mkdir(parents=True, exist_ok=True)
    RESULT_MODELS.mkdir(parents=True, exist_ok=True)


def load_csv(filename):
    path = RESULT_MODELS / filename
    if not path.exists():
        print(f"[WARN] 文件不存在: {path}")
        return pd.DataFrame()
    return pd.read_csv(path)


def load_json(filename):
    path = RESULT_REPORTS / filename
    if not path.exists():
        path = RESULT_MODELS / filename  # 也在 models 下找
    if not path.exists():
        print(f"[WARN] 文件不存在: {path}")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ==================== 图表 1：用户行为转化漏斗图 ====================
def plot_behavior_funnel(summary: dict):
    """绘制行为转化漏斗图（浏览→加购→购买）。"""
    behaviors = summary.get("behavior_funnel", {})
    if not behaviors:
        print("[WARN] analysis_summary.json 中无 behavior_stats，跳过漏斗图")
        return

    stages = ["浏览 (view)", "加购 (cart)", "购买 (purchase)"]
    counts = [
        behaviors.get("view_count", 0),
        behaviors.get("cart_count", 0),
        behaviors.get("purchase_count", 0),
    ]

    fig, ax = plt.subplots(figsize=(10, 6))

    colors_vals = ["#4CAF50", "#FF9800", "#F44336"]
    # 创建漏斗效果
    max_count = max(counts)
    bar_widths = [c / max_count * 0.8 for c in counts]

    y_pos = [2, 1, 0]
    for i, (y, w, c, stage, cnt) in enumerate(zip(y_pos, bar_widths, colors_vals, stages, counts)):
        ax.barh(y, w, height=0.6, color=c, alpha=0.85, edgecolor="white", linewidth=1.5)
        ax.text(w / 2, y, f"{stage}\n{cnt:,} 次", ha="center", va="center",
                fontsize=12, fontweight="bold", color="white")

        if i > 0:
            prev_w = bar_widths[i - 1]
            rate = cnt / counts[i - 1] * 100 if counts[i - 1] > 0 else 0
            ax.text(prev_w + 0.01, (y_pos[i] + y_pos[i - 1]) / 2,
                    f"转化率 {rate:.1f}%", fontsize=10, color="#666", va="center")

    ax.set_xlim(0, 1.0)
    ax.set_yticks([])
    ax.set_title("电商用户行为转化漏斗", fontsize=16, fontweight="bold", pad=20)
    ax.set_xlabel("相对比例", fontsize=11)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)

    plt.tight_layout()
    path = RESULT_FIGURES / "step4_funnel.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✓ 漏斗图已保存: {path}")


# ==================== 图表 2：品类热度排行 Top 15 ====================
def plot_category_ranking(hot_df: pd.DataFrame):
    """绘制品类购买次数 Top 15 横向柱状图。"""
    if hot_df.empty:
        print("[WARN] hot_products.csv 为空，跳过品类排行图")
        return

    # 按 category_code 聚合购买次数
    cat_stats = hot_df.groupby("category_code").agg(
        total_purchase=("purchase_count", "sum"),
        total_revenue=("revenue", "sum"),
    ).reset_index().sort_values("total_purchase", ascending=False).head(15)

    fig, ax = plt.subplots(figsize=(12, 7))

    colors = sns.color_palette("viridis", len(cat_stats))
    bars = ax.barh(range(len(cat_stats)), cat_stats["total_purchase"], color=colors, edgecolor="white")

    ax.set_yticks(range(len(cat_stats)))
    # 简化类别名
    labels = [c.replace("electronics.", "").replace("appliances.", "").replace("computers.", "") for c in cat_stats["category_code"]]
    ax.set_yticklabels(labels, fontsize=10)

    for i, (bar, val) in enumerate(zip(bars, cat_stats["total_purchase"])):
        ax.text(bar.get_width() + max(cat_stats["total_purchase"]) * 0.01, bar.get_y() + bar.get_height() / 2,
                f"{int(val):,}", va="center", fontsize=9)

    ax.set_title("品类购买热度 Top 15", fontsize=16, fontweight="bold")
    ax.set_xlabel("购买次数", fontsize=11)
    ax.invert_yaxis()

    plt.tight_layout()
    path = RESULT_FIGURES / "step4_category_ranking.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✓ 品类排行图已保存: {path}")


# ==================== 图表 3：用户分群雷达图 ====================
def plot_cluster_radar(cluster_profiles_business: pd.DataFrame):
    """绘制用户分群雷达图（使用业务特征）。"""
    if cluster_profiles_business.empty:
        print("[WARN] cluster_profiles_business.csv 为空，跳过雷达图")
        return

    df = cluster_profiles_business.copy().set_index("cluster")

    # 选择用于雷达图的特征
    radar_cols = ["event_count", "unique_products", "cart_count", "purchase_count", "session_duration_min", "purchase_amount", "unique_categories"]
    available_cols = [c for c in radar_cols if c in df.columns]
    if len(available_cols) < 3:
        print("[WARN] 雷达图可用特征不足，跳过")
        return

    # 标准化（0-1）
    data = df[available_cols].copy()
    for col in available_cols:
        max_val = data[col].max()
        if max_val > 0:
            data[col] = data[col] / max_val

    # 雷达图
    num_vars = len(available_cols)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]  # 闭合

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))

    colors = PALETTE[:len(data)]
    for i, (cluster_id, row) in enumerate(data.iterrows()):
        values = row.tolist()
        values += values[:1]
        ax.fill(angles, values, alpha=0.1, color=colors[i])
        ax.plot(angles, values, "o-", linewidth=2, label=f"Cluster {int(cluster_id)}", color=colors[i])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(available_cols, fontsize=9)
    ax.set_title("用户分群雷达图（标准化特征）", fontsize=16, fontweight="bold", pad=30)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=9)

    plt.tight_layout()
    path = RESULT_FIGURES / "step4_cluster_radar.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✓ 雷达图已保存: {path}")


# ==================== 图表 4：用户分群 PCA 散点图（占位，step2 已有） ====================
def plot_cluster_pca():
    """
    Step2 已生成 PCA 散点图 (cluster_pca.png)，此处标注。
    如需要基于新数据重新生成，可扩充此函数。
    """
    existing = RESULT_FIGURES / "cluster_pca.png"
    if existing.exists():
        print(f"  ✓ PCA 散点图已存在（Step2）: {existing}")
    else:
        print("[INFO] cluster_pca.png 未找到，Step2 可能未生成")


# ==================== 图表 5：商品关联网络图（占位，step2 已有） ====================
def plot_association_network():
    """Step2 已生成关联网络图，此处标注。"""
    existing = RESULT_FIGURES / "association_network.png"
    if existing.exists():
        print(f"  ✓ 关联网络图已存在（Step2）: {existing}")
    else:
        print("[INFO] association_network.png 未找到")


# ==================== 图表 6：推荐策略效果对比图 ====================
def plot_recommendation_comparison(rec_data: dict):
    """绘制推荐策略对比图：各策略覆盖的商品/规则数量。"""
    if not rec_data:
        print("[WARN] recommendations.json 为空，跳过推荐对比图")
        return

    hot_by_purchase = len([r for r in rec_data.get("hot_recommendations", []) if r.get("strategy") == "hot_by_purchase"])
    hot_by_revenue = len([r for r in rec_data.get("hot_recommendations", []) if r.get("strategy") == "hot_by_revenue"])
    association_count = len(rec_data.get("association_recommendations", []))
    cluster_count = len(rec_data.get("cluster_recommendations", []))
    cluster_product_count = sum(
        len(c.get("hot_products_in_category", []))
        for c in rec_data.get("cluster_recommendations", [])
    )

    categories = ["按购买量\n热门推荐", "按销售额\n热门推荐", "关联规则\n推荐", "群体偏好\n推荐(聚类数)", "群体偏好\n推荐(商品数)"]
    values = [hot_by_purchase, hot_by_revenue, association_count, cluster_count, cluster_product_count]
    colors_list = ["#4CAF50", "#2196F3", "#FF9800", "#9C27B0", "#E91E63"]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(categories, values, color=colors_list, edgecolor="white", linewidth=1.5, width=0.6)

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(1, max(values) * 0.02),
                str(val), ha="center", fontsize=12, fontweight="bold")

    ax.set_title("推荐策略效果对比", fontsize=16, fontweight="bold")
    ax.set_ylabel("数量", fontsize=11)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    path = RESULT_FIGURES / "step4_recommendation_comparison.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✓ 推荐对比图已保存: {path}")


# ==================== HTML Dashboard ====================
def generate_dashboard(summary: dict, rec_data: dict):
    """生成综合 HTML Dashboard，嵌入所有图表。"""
    # 提取关键指标
    behaviors = summary.get("behavior_funnel", {})
    view_count = behaviors.get("view_count", 0)
    cart_count = behaviors.get("cart_count", 0)
    purchase_count = behaviors.get("purchase_count", 0)
    total_users = summary.get("data_overview", {}).get("total_users", 0)
    total_sessions = summary.get("data_overview", {}).get("total_sessions", 0)

    view_to_cart = cart_count / view_count * 100 if view_count > 0 else 0
    view_to_purchase = purchase_count / view_count * 100 if view_count > 0 else 0
    cart_to_purchase = purchase_count / cart_count * 100 if cart_count > 0 else 0

    cluster_count = summary.get("clustering", {}).get("n_clusters", 0)
    silhouette = summary.get("clustering", {}).get("silhouette_score", 0)
    n_rules = len(rec_data.get("association_recommendations", []))
    n_hot = len(rec_data.get("hot_recommendations", []))
    n_cluster_recs = len(rec_data.get("cluster_recommendations", []))

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>电商数据分析仪表盘</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    padding: 20px;
  }}
  .container {{ max-width: 1400px; margin: 0 auto; }}
  h1 {{
    text-align: center; color: white; font-size: 2.2em;
    margin-bottom: 10px; text-shadow: 0 2px 4px rgba(0,0,0,0.2);
  }}
  .subtitle {{ text-align: center; color: rgba(255,255,255,0.8); margin-bottom: 30px; font-size: 1.1em; }}

  /* 指标卡片 */
  .kpi-grid {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 16px; margin-bottom: 30px;
  }}
  .kpi-card {{
    background: white; border-radius: 16px; padding: 24px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.1); text-align: center;
    transition: transform 0.2s;
  }}
  .kpi-card:hover {{ transform: translateY(-4px); }}
  .kpi-icon {{ font-size: 2em; margin-bottom: 8px; }}
  .kpi-value {{ font-size: 2em; font-weight: 700; color: #333; }}
  .kpi-label {{ font-size: 0.9em; color: #888; margin-top: 4px; }}
  .kpi-sub {{ font-size: 0.8em; color: #aaa; margin-top: 2px; }}

  /* 图表区 */
  .chart-section {{
    background: white; border-radius: 16px; padding: 24px;
    margin-bottom: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  }}
  .chart-section h2 {{
    font-size: 1.3em; color: #333; margin-bottom: 16px;
    padding-bottom: 8px; border-bottom: 2px solid #667eea;
  }}
  .chart-section img {{
    width: 100%; border-radius: 8px; display: block;
  }}

  .two-col {{
    display: grid; grid-template-columns: 1fr 1fr; gap: 24px;
  }}

  .footer {{
    text-align: center; color: rgba(255,255,255,0.6);
    margin-top: 40px; font-size: 0.85em;
  }}

  @media (max-width: 768px) {{
    .two-col {{ grid-template-columns: 1fr; }}
    .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }}
  }}
</style>
</head>
<body>
<div class="container">
  <h1>📊 电商智能分析仪表盘</h1>
  <p class="subtitle">用户行为分析 · 商品关联规则 · 智能推荐策略</p>

  <div class="kpi-grid">
    <div class="kpi-card">
      <div class="kpi-icon">👥</div>
      <div class="kpi-value">{total_users:,}</div>
      <div class="kpi-label">总用户数</div>
      <div class="kpi-sub">{total_sessions:,} 个会话</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-icon">👁️</div>
      <div class="kpi-value">{view_count:,}</div>
      <div class="kpi-label">总浏览</div>
      <div class="kpi-sub">浏览→加购 {view_to_cart:.2f}%</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-icon">🛒</div>
      <div class="kpi-value">{cart_count:,}</div>
      <div class="kpi-label">总加购</div>
      <div class="kpi-sub">加购→购买 {cart_to_purchase:.2f}%</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-icon">💳</div>
      <div class="kpi-value">{purchase_count:,}</div>
      <div class="kpi-label">总购买</div>
      <div class="kpi-sub">浏览→购买 {view_to_purchase:.2f}%</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-icon">🎯</div>
      <div class="kpi-value">{cluster_count}</div>
      <div class="kpi-label">用户分群</div>
      <div class="kpi-sub">轮廓系数 {silhouette:.4f}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-icon">🔗</div>
      <div class="kpi-value">{n_rules + n_hot + n_cluster_recs}</div>
      <div class="kpi-label">推荐策略条目</div>
      <div class="kpi-sub">{n_hot}热门 + {n_rules}关联 + {n_cluster_recs}群体</div>
    </div>
  </div>

  <div class="chart-section">
    <h2>📈 用户行为转化漏斗</h2>
    <img src="figures/step4_funnel.png" alt="行为转化漏斗" onerror="this.parentElement.innerHTML='<p style=color:#999>图表待生成：请运行 step4_visualization.py</p>'">
  </div>

  <div class="two-col">
    <div class="chart-section">
      <h2>🏷️ 品类热度 Top 15</h2>
      <img src="figures/step4_category_ranking.png" alt="品类热度" onerror="this.style.display='none'">
    </div>
    <div class="chart-section">
      <h2>🎯 用户分群雷达图</h2>
      <img src="figures/step4_cluster_radar.png" alt="雷达图" onerror="this.style.display='none'">
    </div>
  </div>

  <div class="two-col">
    <div class="chart-section">
      <h2>📍 用户分群 PCA 散点图</h2>
      <img src="figures/cluster_pca.png" alt="PCA 散点" onerror="this.style.display='none'">
    </div>
    <div class="chart-section">
      <h2>🕸️ 商品关联网络</h2>
      <img src="figures/association_network.png" alt="关联网络" onerror="this.style.display='none'">
    </div>
  </div>

  <div class="chart-section">
    <h2>💡 推荐策略效果对比</h2>
    <img src="figures/step4_recommendation_comparison.png" alt="推荐对比" onerror="this.parentElement.innerHTML='<p style=color:#999>图表待生成</p>'">
  </div>

  <div class="footer">
    <p>电商智能分析系统 · 自动生成于 {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")}</p>
  </div>
</div>
</body>
</html>"""

    path = PROJECT_ROOT / "result" / "dashboard.html"
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✓ Dashboard 已保存: {path}")


# ==================== 主流程 ====================
def main():
    print("=" * 60)
    print("第四步：数据可视化展示")
    print("=" * 60)

    ensure_dirs()

    # 1. 加载数据
    print("\n[1/3] 加载数据...")
    summary = load_json("analysis_summary.json")
    hot_df = load_csv("hot_products.csv")
    cluster_business = load_csv("cluster_profiles_business.csv")
    rec_data = load_json("recommendations.json")

    if not summary:
        print("[WARN] analysis_summary.json 未找到，KPI 数据将为空")
    if hot_df.empty:
        print("[WARN] hot_products.csv 为空，部分图表将跳过")

    # 2. 绘制各图表
    print("\n[2/3] 绘制可视化图表...")
    plot_behavior_funnel(summary)
    plot_category_ranking(hot_df)
    plot_cluster_radar(cluster_business)
    plot_cluster_pca()
    plot_association_network()
    plot_recommendation_comparison(rec_data)

    # 3. 生成 HTML Dashboard
    print("\n[3/3] 生成 HTML Dashboard...")
    generate_dashboard(summary, rec_data)

    print(f"\n{'=' * 60}")
    print("✅ 第四步可视化完成！")
    print(f"   Dashboard: {PROJECT_ROOT / 'result' / 'dashboard.html'}")
    print(f"   图表目录: {RESULT_FIGURES}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()