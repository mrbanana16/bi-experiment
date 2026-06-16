# -*- coding: utf-8 -*-
"""
第三步：商品推荐策略设计
========================
基于第二步产出的分析结果，实现三种推荐策略：
  1. 热门商品推荐（基于 hot_products.csv）
  2. 关联商品推荐（基于 association_rules.csv）
  3. 用户群体偏好推荐（基于 cluster_profiles + cluster_category_preferences）

输入文件（来自 result/models/）：
  - hot_products.csv           商品级热度排行
  - association_rules.csv      关联规则结果
  - cluster_profiles.csv       聚类用户画像（训练特征）
  - cluster_profiles_business.csv  聚类用户画像（业务特征）
  - cluster_category_preferences.csv 各聚类偏好品类分布

输出文件：
  - result/models/recommendations.json  结构化推荐结果
"""

import json
import sys
from pathlib import Path

import pandas as pd

# ---------- 路径配置 ----------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULT_MODELS = PROJECT_ROOT / "result" / "models"
RESULT_REPORTS = PROJECT_ROOT / "result" / "reports"


def load_csv(filename):
    """读取 result/models 下的 CSV 文件，文件不存在则报错退出。"""
    path = RESULT_MODELS / filename
    if not path.exists():
        print(f"[ERROR] 文件不存在: {path}")
        sys.exit(1)
    return pd.read_csv(path)


# ==================== 策略一：热门商品推荐 ====================
def build_hot_recommendations(hot_df: pd.DataFrame, top_n: int = 20):
    """
    基于 hot_products.csv 生成热门商品推荐。
    按 purchase_count（购买次数）降序排序，取 Top N。
    同时按 revenue（销售金额）降序给出另一份排序。
    """
    # 确保必要列存在
    required_cols = ["product_id", "category_code", "brand", "price",
                     "view_count", "purchase_count", "revenue", "conversion_rate"]
    for col in required_cols:
        if col not in hot_df.columns:
            print(f"[WARN] 缺少列 {col}，跳过部分推荐逻辑")
            return []

    # 按购买次数排序
    by_purchase = hot_df.sort_values("purchase_count", ascending=False).head(top_n)
    # 按销售金额排序
    by_revenue = hot_df.sort_values("revenue", ascending=False).head(top_n)

    recommendations = []
    for _, row in by_purchase.iterrows():
        recommendations.append({
            "strategy": "hot_by_purchase",
            "product_id": int(row["product_id"]),
            "category_code": row["category_code"],
            "brand": row["brand"],
            "price": round(float(row["price"]), 2),
            "purchase_count": int(row["purchase_count"]),
            "revenue": round(float(row["revenue"]), 2),
            "conversion_rate": round(float(row["conversion_rate"]), 2),
        })

    for _, row in by_revenue.iterrows():
        rec = {
            "strategy": "hot_by_revenue",
            "product_id": int(row["product_id"]),
            "category_code": row["category_code"],
            "brand": row["brand"],
            "price": round(float(row["price"]), 2),
            "purchase_count": int(row["purchase_count"]),
            "revenue": round(float(row["revenue"]), 2),
            "conversion_rate": round(float(row["conversion_rate"]), 2),
        }
        # 去重：同一商品不重复出现
        if not any(r["product_id"] == rec["product_id"] and r["strategy"] == "hot_by_revenue" for r in recommendations):
            recommendations.append(rec)

    return recommendations


# ==================== 策略二：关联商品推荐 ====================
def build_association_recommendations(rules_df: pd.DataFrame):
    """
    基于 association_rules.csv 构建关联商品推荐。
    对每条规则，以 antecedents 为条件，推荐 consequents，
    并根据 lift / confidence 排序。
    """
    if rules_df.empty:
        return []

    required_cols = ["antecedents", "consequents", "support", "confidence", "lift",
                     "antecedents_str", "consequents_str"]
    for col in required_cols:
        if col not in rules_df.columns:
            print(f"[WARN] 缺少列 {col}，关联推荐将返回空")
            return []

    # 按提升度排序
    sorted_rules = rules_df.sort_values("lift", ascending=False)

    recommendations = []
    for _, row in sorted_rules.iterrows():
        recommendations.append({
            "strategy": "association",
            "antecedent": row.get("antecedents_str", str(row["antecedents"])),
            "consequent": row.get("consequents_str", str(row["consequents"])),
            "support": round(float(row["support"]), 6),
            "confidence": round(float(row["confidence"]), 4),
            "lift": round(float(row["lift"]), 4),
            "suggestion": (
                f"浏览/购买了「{row.get('antecedents_str', row['antecedents'])}」的用户，"
                f"同时推荐「{row.get('consequents_str', row['consequents'])}」"
                f"（提升度 {row['lift']:.2f}，支持度 {row['support']:.4f}）"
            ),
        })

    return recommendations


# ==================== 策略三：用户群体偏好推荐 ====================
def build_cluster_recommendations(
    cluster_profiles_business: pd.DataFrame,
    cluster_category_prefs: pd.DataFrame,
    hot_df: pd.DataFrame,
):
    """
    基于用户分群结果和品类偏好，为每个聚类群体推荐其偏好品类的热门商品。
    """
    if cluster_category_prefs.empty or hot_df.empty:
        return []

    # 为每个 cluster 取 purchase 行为下 top 品类（在 cluster_category_preferences 中 behavior 可能为 purchase/view/cart）
    # 优先用 purchase，其次 cart
    prefs = cluster_category_prefs.copy()
    behavior_order = {"purchase": 0, "cart": 1, "view": 2}
    prefs["behavior_rank"] = prefs["behavior"].map(behavior_order).fillna(99)
    # 每个 cluster 先按 behavior 优先级，再按 count 降序
    top_categories = (
        prefs.sort_values(["cluster", "behavior_rank", "count"], ascending=[True, True, False])
        .groupby("cluster")
        .first()
        .reset_index()
    )

    # 加载业务画像
    profiles = cluster_profiles_business.set_index("cluster") if not cluster_profiles_business.empty else pd.DataFrame()

    recommendations = []
    for _, row in top_categories.iterrows():
        cluster_id = int(row["cluster"])
        preferred_category = row["category"]  # 该聚类 top1 品类

        # 从 hot_products 中筛选该品类下按 purchase_count 排序 top 5
        matched = hot_df[hot_df["category_code"] == preferred_category].sort_values(
            "purchase_count", ascending=False
        ).head(5)

        cluster_desc = ""
        if cluster_id in profiles.index:
            p = profiles.loc[cluster_id]
            cluster_desc = (
                f"Cluster {cluster_id}: 均事件 {p.get('event_count', '?')} 次, "
                f"均购买 {p.get('purchase_count', '?')} 次, "
                f"均金额 {p.get('purchase_amount', '?')}"
            )

        cluster_rec = {
            "strategy": "cluster_preference",
            "cluster_id": cluster_id,
            "cluster_description": cluster_desc,
            "preferred_category": preferred_category,
            "preferred_behavior": row["behavior"],
            "hot_products_in_category": [],
        }

        for _, p_row in matched.iterrows():
            cluster_rec["hot_products_in_category"].append({
                "product_id": int(p_row["product_id"]),
                "brand": p_row["brand"],
                "price": round(float(p_row["price"]), 2),
                "purchase_count": int(p_row["purchase_count"]),
                "revenue": round(float(p_row["revenue"]), 2),
            })

        recommendations.append(cluster_rec)

    return recommendations


# ==================== 主流程 ====================
def main():
    print("=" * 60)
    print("第三步：商品推荐策略设计")
    print("=" * 60)

    # 1. 加载数据
    print("\n[1/4] 加载第二步产出数据...")
    hot_df = load_csv("hot_products.csv")
    rules_df = load_csv("association_rules.csv")
    cluster_profiles_business = load_csv("cluster_profiles_business.csv")
    cluster_category_prefs = load_csv("cluster_category_preferences.csv")

    print(f"  ✓ hot_products: {len(hot_df)} 条")
    print(f"  ✓ association_rules: {len(rules_df)} 条")
    print(f"  ✓ cluster_profiles_business: {len(cluster_profiles_business)} 条")
    print(f"  ✓ cluster_category_preferences: {len(cluster_category_prefs)} 条")

    # 2. 热门商品推荐
    print("\n[2/4] 生成热门商品推荐...")
    hot_recs = build_hot_recommendations(hot_df, top_n=20)
    print(f"  ✓ 热门推荐: {len(hot_recs)} 条")

    # 3. 关联商品推荐
    print("\n[3/4] 生成关联商品推荐...")
    assoc_recs = build_association_recommendations(rules_df)
    print(f"  ✓ 关联推荐: {len(assoc_recs)} 条")

    # 4. 用户群体偏好推荐
    print("\n[4/4] 生成用户群体偏好推荐...")
    cluster_recs = build_cluster_recommendations(
        cluster_profiles_business, cluster_category_prefs, hot_df
    )
    print(f"  ✓ 群体偏好推荐: {len(cluster_recs)} 个聚类")

    # 5. 整合输出
    all_recommendations = {
        "meta": {
            "description": "电商商品推荐策略结果",
            "strategies": ["hot_by_purchase", "hot_by_revenue", "association", "cluster_preference"],
            "total_recommendations": len(hot_recs) + len(assoc_recs) + sum(
                len(c.get("hot_products_in_category", [])) for c in cluster_recs
            ),
        },
        "hot_recommendations": hot_recs,
        "association_recommendations": assoc_recs,
        "cluster_recommendations": cluster_recs,
    }

    # 确保输出目录存在
    RESULT_MODELS.mkdir(parents=True, exist_ok=True)

    output_path = RESULT_MODELS / "recommendations.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_recommendations, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 60}")
    print(f"✅ 推荐结果已保存至: {output_path}")
    print(f"   总推荐条数: {all_recommendations['meta']['total_recommendations']}")
    print(f"{'=' * 60}")

    # 打印摘要
    print("\n📊 推荐结果摘要：")
    print(f"  - 热门商品（按购买次数 Top 20）: {len([r for r in hot_recs if r['strategy'] == 'hot_by_purchase'])} 个")
    print(f"  - 热门商品（按销售金额 Top 20）: {len([r for r in hot_recs if r['strategy'] == 'hot_by_revenue'])} 个")
    print(f"  - 关联规则推荐: {len(assoc_recs)} 组")
    print(f"  - 用户群体偏好推荐: {len(cluster_recs)} 个聚类群体")

    if hot_recs:
        top = hot_recs[0]
        print(f"\n  🏆 购买量最高: #{top['product_id']} {top['brand']} ({top['category_code']}), "
              f"购买 {top['purchase_count']} 次, 金额 ¥{top['revenue']:,.2f}")

    if assoc_recs:
        top_rule = assoc_recs[0]
        print(f"  🔗 最强关联: {top_rule['antecedent']} → {top_rule['consequent']} "
              f"(Lift={top_rule['lift']:.2f})")


if __name__ == "__main__":
    main()