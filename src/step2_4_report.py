"""
子任务 2.4：结果整合与报告
整合三个分析的结果，生成综合报告 + JSON 摘要
输出：result/reports/step2_analysis_report.md, result/reports/analysis_summary.json
"""
import pandas as pd
import numpy as np
import pickle
import json
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 创建输出目录
os.makedirs('../result/reports', exist_ok=True)


def round_pct_sum_100(counts, total):
    """Round percentages to 1 decimal so they sum to exactly 100.0 (largest-remainder method)."""
    import math
    raw = [c / total * 100 for c in counts]
    floored = [math.floor(r * 10) / 10 for r in raw]
    remainder = round(100.0 - sum(floored), 1)
    n_to_bump = int(round(remainder * 10))
    remainders = [(raw[i] - floored[i], i) for i in range(len(raw))]
    remainders.sort(key=lambda x: x[0], reverse=True)
    result = list(floored)
    for j in range(n_to_bump):
        result[remainders[j][1]] = round(result[remainders[j][1]] + 0.1, 1)
    return result


def convert_numpy_types(obj):
    """递归将 numpy 类型转换为 Python 原生类型（供 JSON 序列化）"""
    if isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy_types(v) for v in obj]
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


# ==================== 1. 读取分析结果 ====================
print("=" * 50)
print("1. 读取分析结果")
print("=" * 50)

df = pd.read_csv('../Datasets/processed/preprocessed.csv')
print(f"预处理数据形状: {df.shape}")

date_min = str(pd.to_datetime(df['event_time']).min().date())
date_max = str(pd.to_datetime(df['event_time']).max().date())
date_range_str = f"{date_min} ~ {date_max}"

cluster_profiles = pd.read_csv('../result/models/cluster_profiles.csv', index_col=0)
print(f"聚类画像（训练特征）形状: {cluster_profiles.shape}")
print(f"聚类画像列名: {cluster_profiles.columns.tolist()}")

cluster_profiles_business = pd.read_csv('../result/models/cluster_profiles_business.csv', index_col=0)
print(f"聚类画像（业务特征）形状: {cluster_profiles_business.shape}")

association_rules = pd.read_csv('../result/models/association_rules.csv')
print(f"细粒度关联规则数量: {len(association_rules)}")

frequent_itemsets = pd.read_csv('../result/models/frequent_itemsets.csv')
print(f"频繁项集数量: {len(frequent_itemsets)}")

hot_products = pd.read_csv('../result/models/hot_products.csv')
print(f"热门商品数量: {len(hot_products)}")

cluster_category_prefs = pd.read_csv('../result/models/cluster_category_preferences.csv')
print(f"聚类品类偏好条目数: {len(cluster_category_prefs)}")

has_l1_rules = os.path.exists('../result/models/association_rules_l1.csv')
if has_l1_rules:
    association_rules_l1 = pd.read_csv('../result/models/association_rules_l1.csv')
    print(f"粗粒度关联规则数量: {len(association_rules_l1)}")
else:
    association_rules_l1 = pd.DataFrame()

# ==================== 1.5 计算行为分析统计 ====================
print("\n" + "=" * 50)
print("1.5 计算行为分析统计")
print("=" * 50)

event_counts = df['event_type'].value_counts()
view_count = int(event_counts.get('view', 0))
cart_count = int(event_counts.get('cart', 0))
purchase_count = int(event_counts.get('purchase', 0))
cart_rate = round(cart_count / view_count * 100, 2) if view_count > 0 else 0
purchase_rate = round(purchase_count / view_count * 100, 2) if view_count > 0 else 0
cart_to_purchase_rate = round(purchase_count / cart_count * 100, 2) if cart_count > 0 else 0

hourly_counts = df.groupby('Hour')['event_type'].count()
peak_hour = int(hourly_counts.idxmax())
peak_hour_count = int(hourly_counts.max())
low_hour = int(hourly_counts.idxmin())
low_hour_count = int(hourly_counts.min())

weekday_counts = df.groupby('Weekday')['event_type'].count().reindex(range(7), fill_value=0)
weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
most_active_day = weekday_names[int(weekday_counts.idxmax())]
most_active_day_count = int(weekday_counts.max())
least_active_day = weekday_names[int(weekday_counts.idxmin())]
least_active_day_count = int(weekday_counts.min())

weekend_counts = df.groupby('Is_Weekend')['event_type'].count()
weekday_total = int(weekend_counts.get(False, 0))
weekend_total = int(weekend_counts.get(True, 0))
total_events = weekday_total + weekend_total
weekday_pct = round(weekday_total / total_events * 100, 1)
weekend_pct = round(weekend_total / total_events * 100, 1)

df_with_category = df[df['category_code'].notna() & (df['category_code'] != '')]
view_by_cat = df_with_category[df_with_category['event_type'] == 'view']['category_code'].value_counts().head(5)
purchase_by_cat = df_with_category[df_with_category['event_type'] == 'purchase']['category_code'].value_counts().head(5)
purchase_df = df_with_category[df_with_category['event_type'] == 'purchase']
revenue_by_cat = purchase_df.groupby('category_code')['price'].sum().sort_values(ascending=False).head(5)

price_bins = [0, 50, 100, 200, 500, 1000, float('inf')]
price_labels = ['0-50', '50-100', '100-200', '200-500', '500-1000', '1000+']
df_price = df[['price', 'event_type']].copy()
df_price['price_range'] = pd.cut(df_price['price'], bins=price_bins, labels=price_labels, right=False)
price_funnel = df_price.groupby('price_range', observed=False)['event_type'].value_counts().unstack(fill_value=0)
price_funnel['conversion_rate'] = (price_funnel['purchase'] / price_funnel['view'].replace(0, np.nan) * 100).round(2)
cr_valid = price_funnel['conversion_rate'].dropna()
best_price_range = cr_valid.idxmax()
best_price_rate = cr_valid.max()
worst_price_range = cr_valid.idxmin()
worst_price_rate = cr_valid.min()

total_users = df['user_id'].nunique()
purchasing_users = df[df['event_type'] == 'purchase']['user_id'].nunique()
purchasing_user_rate = round(purchasing_users / total_users * 100, 2)
user_event_counts = df.groupby('user_id')['event_type'].value_counts().unstack(fill_value=0)
avg_views_per_user = round(user_event_counts.get('view', pd.Series(dtype=float)).mean(), 2) if len(user_event_counts) > 0 else 0
avg_purchases_per_user = round(user_event_counts.get('purchase', pd.Series(dtype=float)).mean(), 2) if len(user_event_counts) > 0 else 0
avg_sessions_per_user = round(df.groupby('user_id')['user_session'].nunique().mean(), 2)
purchase_amount_by_user = df[df['event_type'] == 'purchase'].groupby('user_id')['price'].sum()
avg_spend_per_user = round(purchase_amount_by_user.sum() / total_users, 2)

total_events_raw = len(df)
total_sessions = df['user_session'].nunique()
total_categories = df_with_category['category_code'].nunique()

trans_df = pd.read_csv('../Datasets/processed/transactions_for_apriori.csv')
trans_count = len(trans_df)
# 跨品类用户占比（相对于全部购买用户）
multi_cat_count = trans_count  # CSV 中已过滤为 2+ 品类用户
rule_cross_pct = round(multi_cat_count / purchasing_users * 100, 1) if purchasing_users > 0 else 0

l1_transactions_path = '../Datasets/processed/transactions_l1_for_apriori.csv'
if os.path.exists(l1_transactions_path):
    trans_l1_df = pd.read_csv(l1_transactions_path)
    trans_l1_count = len(trans_l1_df)
    l1_rule_cross_pct = round(trans_l1_count / purchasing_users * 100, 1) if purchasing_users > 0 else 0
else:
    # 事务表不存在时，从原始数据计算
    df_l1 = df[(df['event_type'] == 'purchase') & df['category_code'].notna() & (df['category_code'] != '')].copy()
    df_l1['category_l1'] = df_l1['category_code'].str.split('.').str[0]
    multi_cat_l1 = df_l1.groupby('user_id')['category_l1'].apply(lambda x: len(set(x)) > 1).sum()
    trans_l1_count = int(multi_cat_l1)
    l1_rule_cross_pct = round(trans_l1_count / purchasing_users * 100, 1) if purchasing_users > 0 else 0

# 加载聚类模型
with open('../result/models/kmeans_model.pkl', 'rb') as _f:
    _model_data = pickle.load(_f)
max_sil = _model_data['metadata'].get('silhouette_score_pre_merge', 0)
sil_post_merge = _model_data['metadata'].get('silhouette_score_post_merge', max_sil)
cluster_merge_map = _model_data['metadata'].get('cluster_merge_map', {})
min_cluster_size = _model_data['metadata'].get('min_cluster_size', 10)
single_cluster_labels = _model_data['metadata'].get('single_cluster_labels', {0: '仅浏览型', 1: '加购未转化型', 2: '直接购买型'})
n_single_clusters = _model_data['metadata'].get('n_single_clusters', 3)
inertias = _model_data['metadata'].get('inertias', [])
sil_scores = _model_data['metadata'].get('sil_scores', [])
_labels = _model_data['final_labels']

cluster_sizes = pd.Series(_labels).value_counts().sort_index()
n_clusters = len(cluster_sizes)
single_event_pct = round(cluster_sizes.iloc[:n_single_clusters].sum() / len(_labels) * 100, 1)

# 生成品类Top5字符串
view_top5 = "\n".join([f"{i+1}. {cat}（{count:,}次）" for i, (cat, count) in enumerate(view_by_cat.items())])
purchase_top5 = "\n".join([f"{i+1}. {cat}（{count:,}次）" for i, (cat, count) in enumerate(purchase_by_cat.items())])
revenue_top5 = "\n".join([f"{i+1}. {cat}（{amount:,.2f}）" for i, (cat, amount) in enumerate(revenue_by_cat.items())])

# 品类转化率（Top15 by views，供报告使用）
cat_funnel = df_with_category[df_with_category['event_type'].isin(['view', 'cart', 'purchase'])].groupby('category_code')['event_type'].value_counts().unstack(fill_value=0)
if 'view' in cat_funnel.columns and 'purchase' in cat_funnel.columns:
    cat_funnel['conversion_rate'] = (cat_funnel['purchase'] / cat_funnel['view'].replace(0, np.nan) * 100).round(2)
top15_cats = cat_funnel.nlargest(15, 'view')

# 价格区间表格
price_table = ""
for label in price_labels:
    if label in price_funnel.index:
        row = price_funnel.loc[label]
        conversion_rate = row['conversion_rate']
        if pd.isna(conversion_rate) or row.get('view', 0) == 0:
            rate_str = "-"
        else:
            rate_str = f"{conversion_rate}%"
        price_table += f"| {label} | {int(row.get('view', 0)):,} | {int(row.get('purchase', 0)):,} | {rate_str} |\n"

# 关联规则（step2_3 已完成去重，直接使用）
rules_for_report = association_rules.copy()

print("行为分析统计计算完成")

# ==================== 2. 生成报告 ====================
print("\n" + "=" * 50)
print("2. 生成报告")
print("=" * 50)

# 构建聚类画像字符串（全量用户）
cluster_pcts = round_pct_sum_100([int(cluster_sizes.get(i, 0)) for i in range(n_clusters)], len(_labels))


def get_cluster_label(cid, biz):
    """根据聚类业务特征推断标签"""
    if cid < n_single_clusters:
        return single_cluster_labels.get(cid, f"单事件分群{cid}")
    # K-Means 聚类：根据业务特征推断
    if biz['purchase_count'] > 0.5:
        return "多事件购买型"
    elif biz['cart_count'] > 0.5 and biz['purchase_count'] < 0.1:
        return "多事件加购未转化型"
    elif biz['event_count'] >= 3:
        return "深度浏览型"
    else:
        return "多次浏览型"


cluster_profiles_section = ""
for i in range(n_clusters):
    biz = cluster_profiles_business.iloc[i]
    train = cluster_profiles.iloc[i]
    count = cluster_sizes.get(i, 0)
    pct = cluster_pcts[i]
    seg_label = get_cluster_label(i, biz)
    cluster_profiles_section += f"""
#### Cluster {i}（{seg_label}，{count:,} 个会话，占 {pct}%）

**业务特征**：
- 平均事件数：{biz['event_count']:.2f}
- 平均商品数：{biz['unique_products']:.2f}
- 平均加购数：{biz['cart_count']:.2f}
- 平均购买数：{biz['purchase_count']:.2f}
- 平均会话时长：{biz['session_duration_min']:.2f} 分钟
- 平均购买金额：{biz['purchase_amount']:.2f}
- 平均品类数：{biz['unique_categories']:.2f}

**训练特征**（聚类决策依据）：
- event_count: {train['event_count']:.2f}, cart_count: {train['cart_count']:.2f}, purchase_count: {train['purchase_count']:.2f}
- log_purchase_amount: {train['log_purchase_amount']:.4f}, has_purchase: {train['has_purchase']:.2f}, has_duration: {train['has_duration']:.2f}
"""

# 构建聚类解释字符串
# 注意 elif 顺序：先区分单事件/多事件，再区分购买/加购/浏览
# 避免单事件购买用户（event_count=1, purchase_count=1）被 "purchase_count > 0.5" 误判为"购买型"
cluster_interpretation = ""
for i in range(n_clusters):
    biz = cluster_profiles_business.iloc[i]
    count = cluster_sizes.get(i, 0)

    if biz['purchase_amount'] > 500 and biz['purchase_count'] > 0.5:
        user_type = "高价值用户"
        desc = f"购买金额高（均值 {biz['purchase_amount']:.0f}），有明确购买行为"
    elif biz['event_count'] <= 1.01 and biz['purchase_count'] > 0.5:
        user_type = "直接购买型用户"
        desc = f"仅 1 个事件即完成购买（占比 {count/len(_labels)*100:.1f}%），决策迅速"
    elif biz['event_count'] <= 1.01 and biz['cart_count'] > 0.5:
        user_type = "加购未转化用户"
        desc = f"仅 1 个事件为加购（占比 {count/len(_labels)*100:.1f}%），未完成购买"
    elif biz['purchase_count'] > 0.5:
        user_type = "购买型用户"
        desc = f"有购买行为（均值 {biz['purchase_count']:.1f} 次），购买金额 {biz['purchase_amount']:.0f}"
    elif biz['cart_count'] > 0.5 and biz['purchase_count'] < 0.1:
        user_type = "加购未转化用户"
        desc = f"有加购行为（均值 {biz['cart_count']:.1f} 次），但未完成购买"
    elif biz['session_duration_min'] > 120:
        user_type = "长时会话用户"
        desc = f"会话时长异常（均值 {biz['session_duration_min']:.0f} 分钟），可能为异常数据或深度浏览"
    elif biz['event_count'] >= 3 and biz['unique_categories'] > 1.15:
        user_type = "浏览探索型用户"
        desc = f"浏览较活跃（均值 {biz['event_count']:.1f} 次），跨 {biz['unique_categories']:.1f} 个品类探索"
    elif biz['event_count'] >= 3:
        user_type = "多事件浏览型用户"
        desc = f"多次浏览（均值 {biz['event_count']:.1f} 次），但无加购和购买转化"
    elif biz['event_count'] >= 2:
        user_type = "浏览型用户"
        desc = f"有浏览行为（均值 {biz['event_count']:.1f} 次），但无购买转化"
    else:
        user_type = "低活跃度用户"
        desc = f"仅 1 次浏览（占比 {count/len(_labels)*100:.1f}%），无后续行为"

    cluster_interpretation += f"- **Cluster {i}（{user_type}）**：{desc}\n"

# 构建关联规则表格
rules_table = ""
for i, (_, rule) in enumerate(rules_for_report.head(10).iterrows()):
    antecedent = rule['antecedents_str'] if 'antecedents_str' in rule.index else str(rule['antecedents'])
    consequent = rule['consequents_str'] if 'consequents_str' in rule.index else str(rule['consequents'])
    rules_table += f"| {i+1} | {antecedent} | {consequent} | {rule['support']:.4f} | {rule['confidence']:.4f} | {rule['lift']:.4f} |\n"

# 最强规则解读
if len(rules_for_report) > 0:
    top_rule = rules_for_report.iloc[0]
    top_antecedent = top_rule['antecedents_str'] if 'antecedents_str' in rules_for_report.columns else str(top_rule['antecedents'])
    top_consequent = top_rule['consequents_str'] if 'consequents_str' in rules_for_report.columns else str(top_rule['consequents'])
    strongest_rule_section = f"""
**最强关联规则**：
- **{top_antecedent}** → **{top_consequent}**
- 支持度：{top_rule['support']:.4f}（{top_rule['support']*100:.2f}%的购买用户同时购买了这两个品类）
- 置信度：{top_rule['confidence']:.4f}（购买{top_antecedent}的用户中，{top_rule['confidence']*100:.2f}%也会购买{top_consequent}）
- 提升度：{top_rule['lift']:.4f}（是随机购买的{top_rule['lift']:.1f}倍）
"""
else:
    strongest_rule_section = "无关联规则。"

# 粗粒度关联规则表格
l1_rules_section = ""
if has_l1_rules and len(association_rules_l1) > 0:
    l1_rules_table = ""
    for i, (_, rule) in enumerate(association_rules_l1.head(10).iterrows()):
        antecedent = rule['antecedents_str'] if 'antecedents_str' in rule.index else str(rule['antecedents'])
        consequent = rule['consequents_str'] if 'consequents_str' in rule.index else str(rule['consequents'])
        l1_rules_table += f"| {i+1} | {antecedent} | {consequent} | {rule['support']:.4f} | {rule['confidence']:.4f} | {rule['lift']:.4f} |\n"

    l1_rules_section = f"""
### 5.5 粗粒度关联规则（一级品类）

将品类聚合到一级（如 `electronics.smartphone` → `electronics`）。粗粒度覆盖率为 {l1_rule_cross_pct}%（细粒度为 {rule_cross_pct}%），
因多数跨品类购买用户在同一一级品类下购买，粗粒度覆盖率更低，但规则的业务泛化性更强。

**Top 10 粗粒度关联规则（按 Lift 排序）**：

| 排名 | 前项(Antecedent) | 后项(Consequent) | 支持度 | 置信度 | 提升度 |
|------|-----------------|-----------------|--------|--------|--------|
{l1_rules_table}
"""
else:
    # 有粗粒度频繁项集但无规则
    l1_fi_path = '../result/models/frequent_itemsets_l1.csv'
    if os.path.exists(l1_fi_path):
        l1_fi = pd.read_csv(l1_fi_path)
        l1_fi_table = ""
        for _, row in l1_fi.iterrows():
            l1_fi_table += f"| {row['itemsets']} | {row['support']:.4f} |\n"
        l1_rules_section = f"""
### 5.5 粗粒度关联规则（一级品类）

将品类聚合到一级（如 `electronics.smartphone` → `electronics`），粗粒度覆盖率为 {l1_rule_cross_pct}%（细粒度为 {rule_cross_pct}%）。

**粗粒度频繁项集**：

| 项集 | 支持度 |
|------|--------|
{l1_fi_table}
**粗粒度关联规则：0 条**

所有跨品类购买用户均在同一一级品类（`electronics` 和 `appliances`）下购买，无法生成跨一级品类的关联规则。
"""

# 用户级统计字符串
user_purchase_dist = user_event_counts.get('purchase', pd.Series(dtype=float)).value_counts().sort_index().head(10)
purchase_dist_rows = "\n".join([f"| {int(k)} 次 | {int(v):,} |" for k, v in user_purchase_dist.items()])
user_stats_section = f"""
### 3.5 用户级统计

| 指标 | 数值 |
|------|------|
| 总用户数 | {total_users:,} |
| 有浏览行为用户 | {int((user_event_counts.get('view', pd.Series(dtype=float)) > 0).sum()):,} |
| 有加购行为用户 | {int((user_event_counts.get('cart', pd.Series(dtype=float)) > 0).sum()):,} |
| 有购买行为用户 | {purchasing_users:,}（{purchasing_user_rate}%） |
| 人均浏览次数 | {avg_views_per_user} |
| 人均加购次数 | {round(user_event_counts.get('cart', pd.Series(dtype=float)).mean(), 2)} |
| 人均购买次数 | {avg_purchases_per_user} |
| 人均会话数 | {avg_sessions_per_user} |
| 人均消费金额 | {avg_spend_per_user} |

**用户购买次数分布**：

| 购买次数 | 用户数 |
|---------|--------|
{purchase_dist_rows}
"""

# 热门商品 Top20 表格
hot_products_table = ""
for rank, (_, row) in enumerate(hot_products.head(20).iterrows(), 1):
    hot_products_table += f"| {rank} | {row['product_id']} | {row['category_code']} | {row['brand']} | {row['price']:.2f} | {int(row['view_count']):,} | {int(row['purchase_count']):,} | {row['revenue']:,.2f} | {row['conversion_rate']:.2f}% |\n"

# 各聚类品类偏好
cluster_category_section = ""
for cid in range(n_clusters):
    biz = cluster_profiles_business.iloc[cid]
    label = get_cluster_label(cid, biz)
    cluster_category_section += f"\n**Cluster {cid}（{label}）**：\n\n"
    for behavior, behavior_label in [('view', '浏览'), ('cart', '加购'), ('purchase', '购买')]:
        prefs = cluster_category_prefs[(cluster_category_prefs['cluster'] == cid) & (cluster_category_prefs['behavior'] == behavior)]
        if len(prefs) > 0:
            cluster_category_section += f"| {behavior_label}排名 | 品类 | 数量 |\n|--------|------|------|\n"
            for _, r in prefs.head(5).iterrows():
                cluster_category_section += f"| {int(r['rank'])} | {r['category']} | {int(r['count']):,} |\n"
            cluster_category_section += "\n"

# ==================== 2.5 覆盖率分析 ====================
cluster_0_pct = round(cluster_sizes.iloc[0] / len(_labels) * 100, 1)
coverage_section = f"""
### 4.4 全量用户覆盖率

本次分群覆盖全部 {len(_labels):,} 个会话（过滤异常后），包括：

| 分群方式 | 会话数 | 占比 | 说明 |
|---------|--------|------|------|
| 规则分群（单事件） | {cluster_sizes.iloc[0] + cluster_sizes.iloc[1] + cluster_sizes.iloc[2]:,} | {round((cluster_sizes.iloc[0] + cluster_sizes.iloc[1] + cluster_sizes.iloc[2]) / len(_labels) * 100, 1)}% | event_count=1，用规则分为浏览/加购/购买三类 |
| K-Means 聚类（多事件） | {sum(cluster_sizes.iloc[n_single_clusters:]):,} | {round(sum(cluster_sizes.iloc[n_single_clusters:]) / len(_labels) * 100, 1)}% | event_count>1，用 K-Means 聚类 |

**购买用户覆盖率**：规则分群中的"直接购买型"包含 {cluster_sizes.iloc[2]:,} 个购买会话，
K-Means 聚类中的购买用户分布在多个聚类中，合计覆盖全部购买行为。
"""

report_content = f"""# 第二步：用户数据与商品关联规则分析报告

## 一、任务概述

本报告基于电商平台用户行为数据，完成以下三个核心分析任务：

1. **用户行为特征分析** - 描述性统计分析，研究用户行为规律
2. **用户分群分析** - 规则分层 + K-Means 聚类，对全量用户进行分类
3. **商品关联规则挖掘** - Apriori算法，发现商品之间的关联关系

---

## 二、数据概况

### 数据来源
- 预处理数据（行为分析 & 关联规则）：`Datasets/processed/preprocessed.csv`
- 会话特征（用户分群）：`Datasets/processed/session_based_features.csv`
- 事务表（关联规则）：`Datasets/processed/transactions_for_apriori.csv`
- 粗粒度事务表（关联规则）：`Datasets/processed/transactions_l1_for_apriori.csv`

### 数据规模
- 总事件数：{total_events_raw:,} 条
- 用户数：{total_users:,} 个
- 会话数：{total_sessions:,} 个
- 商品类别数：{total_categories} 个
- 数据时间范围：{date_range_str}

> **注意**：时间维度分析（高峰时段、最活跃星期等）仅反映 2019 年 10 月的特征，不一定适用于其他时间段。

---

## 三、用户行为特征分析

### 3.1 行为漏斗分析

| 行为阶段 | 数量 | 转化率 |
|---------|------|--------|
| 浏览(View) | {view_count:,} | 100% |
| 加购(Cart) | {cart_count:,} | {cart_rate}% |
| 购买(Purchase) | {purchase_count:,} | {purchase_rate}% |

**关键发现**：
- 浏览到加购的转化率为 {cart_rate}%
- 浏览到购买的转化率为 {purchase_rate}%
- 加购到购买的转化率为 {cart_to_purchase_rate}%（{purchase_count:,}/{cart_count:,}）

### 3.2 时间维度分析

**按小时分布**：
- 高峰时段：{peak_hour}时（{peak_hour_count:,}次）
- 低谷时段：{low_hour}时（{low_hour_count:,}次）

| 时段 | 事件数 | 时段 | 事件数 |
|------|--------|------|--------|
{''.join([f"| {h}:00 | {int(hourly_counts.get(h, 0)):,} | {h+12}:00 | {int(hourly_counts.get(h+12, 0)):,} |" + chr(10) for h in range(12)])}
**按星期分布**：
- 最活跃：{most_active_day}（{most_active_day_count:,}次）
- 最不活跃：{least_active_day}（{least_active_day_count:,}次）

| 星期 | 事件数 |
|------|--------|
{''.join([f"| {weekday_names[i]} | {int(weekday_counts.get(i, 0)):,} |" + chr(10) for i in range(7)])}
**工作日vs周末**：
- 工作日：{weekday_total:,}次（{weekday_pct}%）
- 周末：{weekend_total:,}次（{weekend_pct}%）

### 3.3 品类热度分析

**浏览量Top5品类**：
{view_top5}

**购买量Top5品类**：
{purchase_top5}

**购买金额Top5品类**：
{revenue_top5}

**品类转化率排行（Top15 by 浏览量）**：

| 品类 | 浏览量 | 购买量 | 转化率 |
|------|--------|--------|--------|
{''.join([f"| {cat} | {int(cat_funnel.loc[cat, 'view']):,} | {int(cat_funnel.loc[cat, 'purchase']):,} | {cat_funnel.loc[cat, 'conversion_rate']}% |" + chr(10) for cat in top15_cats.index if not pd.isna(cat_funnel.loc[cat, 'conversion_rate'])])}
### 3.4 价格区间分析

| 价格区间 | 浏览量 | 购买量 | 转化率 |
|---------|--------|--------|--------|
{price_table}
**关键发现**：
- {best_price_range}价格区间转化率最高（{best_price_rate}%）
- {worst_price_range}价格区间转化率最低（{worst_price_rate}%）

{user_stats_section}

### 3.6 热门商品 Top20

| 排名 | 商品ID | 品类 | 品牌 | 价格 | 浏览量 | 购买量 | 金额 | 转化率 |
|------|--------|------|------|------|--------|--------|------|--------|
{hot_products_table}

---

## 四、用户分群分析

### 4.1 聚类方法
- 算法：规则分层（单事件会话）+ K-Means（多事件会话）
- 训练特征：{', '.join(cluster_profiles.columns.tolist())}
- 标准化：StandardScaler
- 最优K值选择（多事件会话，肘部法则 + 轮廓系数）：

| K | Inertia | 轮廓系数 |
|---|---------|---------|
{''.join([f"| {k} | {inertias[i]:,.2f} | {sil_scores[i]:.4f} |" + chr(10) for i, k in enumerate(_model_data['metadata'].get('k_range', range(2, 6)))])}
> 选择 K={_model_data['metadata'].get('k_range', range(2, 6))[np.argmax(_model_data['metadata'].get('sil_scores', [0]))]}，轮廓系数最高（{max(_model_data['metadata'].get('sil_scores', [0])):.4f}）。
- 数据预处理：
  - 移除 session_duration_min > 1440 分钟的异常会话
  - 单事件会话（event_count=1）用规则分为浏览/加购/购买三类
  - 多事件会话（event_count>1）用 K-Means 聚类
  - has_purchase、has_duration 为二值特征
  - purchase_amount 使用 log1p 变换处理右偏

### 4.2 聚类结果

共分为 {n_clusters} 个聚类（规则分群 {n_single_clusters} + K-Means 聚类 {n_clusters - n_single_clusters}，已自动合并小于 {min_cluster_size} 个样本的小聚类）：

{cluster_profiles_section}

### 4.2a 各聚类品类偏好

各聚类的浏览和购买 Top5 品类分布如下：

{cluster_category_section}

### 4.3 聚类解释

根据各聚类的业务特征画像，自动归类如下：

{cluster_interpretation}

{coverage_section}

### 4.5 聚类局限性说明

> **数据预处理说明**：原始数据 {single_event_pct}% 的会话仅有 1 个事件。本次分析采用分层策略：
> - 单事件会话用规则分群（浏览/加购/购买），覆盖 {cluster_sizes.iloc[0] + cluster_sizes.iloc[1] + cluster_sizes.iloc[2]:,} 个会话
> - 多事件会话用 K-Means 聚类，覆盖 {sum(cluster_sizes.iloc[n_single_clusters:]):,} 个会话
> - 合计覆盖全部 {len(_labels):,} 个会话
>
> **轮廓系数说明**：多事件会话的轮廓系数为 {max_sil:.4f}（合并前）/ {sil_post_merge:.4f}（合并后），
> 数值较高，但这主要源于数据的高度同质性。评估聚类质量时应重点关注各聚类的业务特征差异。
>
> **建议**：对各 Cluster 的细分用户制定差异化运营策略。

---

## 五、商品关联规则挖掘

### 5.1 挖掘方法
- 算法：Apriori
- 事务表：以用户为单位，聚合购买记录（仅 purchase 事件），过滤单品类用户后构建共购事务表
- 最小支持度：0.1
- 最小提升度：>1.0（排除独立规则）

### 5.2 挖掘结果

**细粒度分析（category_code）**：
- 购买用户总数：{purchasing_users:,}
- 跨品类用户：{multi_cat_count}（{rule_cross_pct}%）
- 频繁项集数量：{len(frequent_itemsets)}
- 关联规则数量（去重）：{len(rules_for_report)}

### 5.3 Top 10 细粒度关联规则（按 Lift 排序）

| 排名 | 前项(Antecedent) | 后项(Consequent) | 支持度 | 置信度 | 提升度 |
|------|-----------------|-----------------|--------|--------|--------|
{rules_table}
{strongest_rule_section}

**关联网络**：

关联规则形成了包含 {len(set([r['antecedents_str'] if 'antecedents_str' in r.index else str(r['antecedents']) for _, r in rules_for_report.iterrows()] + [r['consequents_str'] if 'consequents_str' in r.index else str(r['consequents']) for _, r in rules_for_report.iterrows()]))} 个品类节点、{len(rules_for_report)} 条有向边的关联网络。主要关联路径：

{''.join([f"- **{r['antecedents_str'] if 'antecedents_str' in rules_for_report.columns else str(r['antecedents'])}** → **{r['consequents_str'] if 'consequents_str' in rules_for_report.columns else str(r['consequents'])}**（提升度 {r['lift']}）" + chr(10) for _, r in rules_for_report.iterrows()])}
**业务建议**：
1. 可以将关联性强的商品进行捆绑销售
2. 在商品详情页推荐关联商品
3. 针对购买了A商品的用户，推送B商品的优惠券

### 5.4 关联规则局限性说明

> **数据规模限制**：单月数据中仅 {rule_cross_pct}% 的购买用户（{multi_cat_count} 人）涉及 2 个以上品类，
> 绝大多数用户仅购买单一品类。关联规则基于用户级共购行为挖掘，反映了真实的购买组合模式，
> 但跨品类样本量有限，规则的泛化能力受限。
>
> **建议**：扩大时间窗口（如 3-6 个月）以获取更多跨品类共购样本，提升规则的可信度和覆盖率。

{l1_rules_section}

---

## 六、输出文件清单

### 6.1 图表文件（result/figures/）

| 文件名 | 说明 |
|--------|------|
| funnel_analysis.png | 行为漏斗分析图 |
| time_distribution.png | 时间维度分析图 |
| category_ranking.png | 品类热度分析图 |
| price_analysis.png | 价格区间分析图 |
| user_statistics.png | 用户级统计图 |
| elbow_silhouette.png | 肘部法则和轮廓系数图 |
| cluster_radar.png | 聚类雷达图 |
| cluster_pca.png | 聚类PCA散点图 |
| cluster_comparison.png | 聚类特征对比图 |
| association_scatter.png | 关联规则散点图 |
| association_network.png | 关联规则网络图 |
| association_top10.png | Top10关联规则柱状图 |

### 6.2 模型文件（result/models/）

| 文件名 | 说明 |
|--------|------|
| kmeans_model.pkl | 聚类模型（含规则分群+K-Means，含scaler和特征列名） |
| cluster_profiles.csv | 聚类用户画像（训练特征） |
| cluster_profiles_business.csv | 聚类用户画像（业务展示特征） |
| frequent_itemsets.csv | 频繁项集 |
| association_rules.csv | 关联规则结果（细粒度） |
| frequent_itemsets_l1.csv | 粗粒度频繁项集 |
| hot_products.csv | 商品级热度排行（product_id 级，含浏览量/购买量/金额/转化率） |
| cluster_category_preferences.csv | 各聚类偏好品类分布（每个 Cluster 的浏览/购买 Top5 品类） |

### 6.3 数据文件（Datasets/）

| 文件名 | 说明 |
|--------|------|
| transactions_for_apriori.csv | Apriori事务表（按用户聚合的购买品类列表） |
| transactions_l1_for_apriori.csv | 粗粒度Apriori事务表（一级品类） |

### 6.4 结构化数据（result/reports/）

| 文件名 | 说明 |
|--------|------|
| analysis_summary.json | 全量分析结果的 JSON 摘要（供 AI 模块和可视化模块消费） |

---

## 七、后续任务使用指南

### 7.1 如何加载聚类模型

```python
import pickle
import numpy as np

with open('../result/models/kmeans_model.pkl', 'rb') as f:
    model_data = pickle.load(f)

kmeans = model_data['model']
scaler = model_data['scaler']
feature_cols = model_data['feature_cols']
renumber_map = model_data.get('renumber_map', dict())
n_single_clusters = model_data['metadata'].get('n_single_clusters', 3)
```

### 7.2 如何读取关联规则结果

```python
import pandas as pd
import os

rules = pd.read_csv('../result/models/association_rules.csv')

# 粗粒度规则（仅在存在时读取）
l1_path = '../result/models/association_rules_l1.csv'
rules_l1 = pd.read_csv(l1_path) if os.path.exists(l1_path) else pd.DataFrame()
```

### 7.3 如何使用聚类画像

```python
import pandas as pd

profiles = pd.read_csv('../result/models/cluster_profiles_business.csv', index_col=0)
print(profiles)
```

---

## 八、总结

本分析完成了第二步的三个核心任务：

1. **用户行为特征分析**：揭示了用户行为的漏斗转化率、时间分布规律、品类热度和价格区间转化率，并增加了用户级统计分析。

2. **用户分群分析**：采用规则分层 + K-Means 混合策略，覆盖全量 {len(_labels):,} 个会话。单事件会话用规则分为浏览/加购/购买三类，多事件会话用 K-Means 聚类。

3. **商品关联规则挖掘**：发现了商品之间的关联关系。同时提供细粒度（category_code）和粗粒度（一级品类）两套分析结果。

这些分析结果可以为后续的**商品推荐策略设计**和**数据可视化展示**提供数据支持和业务洞察。

---

*报告生成时间：{datetime.now().strftime('%Y-%m-%d')}*
*分析脚本：src/step2_1_behavior_analysis.py, src/step2_2_clustering.py, src/step2_3_association_rules.py, src/step2_4_report.py*
"""

# 保存报告
report_path = '../result/reports/step2_analysis_report.md'
with open(report_path, 'w', encoding='utf-8') as f:
    f.write(report_content)
print(f"[OK] 报告已保存: {report_path}")

# ==================== 3. 生成 JSON 摘要 ====================
print("\n" + "=" * 50)
print("3. 生成 JSON 摘要")
print("=" * 50)

# 聚类画像 JSON
cluster_profiles_json = []
for i in range(n_clusters):
    biz = cluster_profiles_business.iloc[i]
    train = cluster_profiles.iloc[i]
    count = int(cluster_sizes.get(i, 0))
    pct = cluster_pcts[i]
    seg_label = get_cluster_label(i, biz)
    cluster_profiles_json.append({
        'cluster_id': i,
        'label': seg_label,
        'count': count,
        'percentage': pct,
        'top_categories': {
            'view': [
                {'rank': int(row['rank']), 'category': row['category'], 'count': int(row['count'])}
                for _, row in cluster_category_prefs[
                    (cluster_category_prefs['cluster'] == i) & (cluster_category_prefs['behavior'] == 'view')
                ].head(5).iterrows()
            ],
            'cart': [
                {'rank': int(row['rank']), 'category': row['category'], 'count': int(row['count'])}
                for _, row in cluster_category_prefs[
                    (cluster_category_prefs['cluster'] == i) & (cluster_category_prefs['behavior'] == 'cart')
                ].head(5).iterrows()
            ],
            'purchase': [
                {'rank': int(row['rank']), 'category': row['category'], 'count': int(row['count'])}
                for _, row in cluster_category_prefs[
                    (cluster_category_prefs['cluster'] == i) & (cluster_category_prefs['behavior'] == 'purchase')
                ].head(5).iterrows()
            ],
        },
        'business_features': {
            'event_count': round(float(biz['event_count']), 2),
            'unique_products': round(float(biz['unique_products']), 2),
            'cart_count': round(float(biz['cart_count']), 2),
            'purchase_count': round(float(biz['purchase_count']), 2),
            'session_duration_min': round(float(biz['session_duration_min']), 2),
            'purchase_amount': round(float(biz['purchase_amount']), 2),
            'unique_categories': round(float(biz['unique_categories']), 2),
        },
        'training_features': {
            'event_count': round(float(train['event_count']), 4),
            'cart_count': round(float(train['cart_count']), 4),
            'purchase_count': round(float(train['purchase_count']), 4),
            'log_purchase_amount': round(float(train['log_purchase_amount']), 4),
            'has_purchase': round(float(train['has_purchase']), 4),
            'has_duration': round(float(train['has_duration']), 4),
        }
    })

# 关联规则 JSON（全量指标）
RULE_EXTRA_COLS = ['leverage', 'conviction', 'zhangs_metric', 'jaccard', 'certainty', 'kulczynski']

rules_json = []
for _, rule in rules_for_report.head(20).iterrows():
    antecedent = rule['antecedents_str'] if 'antecedents_str' in rules_for_report.columns else str(rule['antecedents'])
    consequent = rule['consequents_str'] if 'consequents_str' in rules_for_report.columns else str(rule['consequents'])
    entry = {
        'antecedent': antecedent,
        'consequent': consequent,
        'antecedent_support': round(float(rule['antecedent support']), 4) if 'antecedent support' in rule.index else None,
        'consequent_support': round(float(rule['consequent support']), 4) if 'consequent support' in rule.index else None,
        'support': round(float(rule['support']), 4),
        'confidence': round(float(rule['confidence']), 4),
        'lift': round(float(rule['lift']), 4),
        'representativity': round(float(rule['representativity']), 4) if 'representativity' in rule.index else None,
    }
    for col in RULE_EXTRA_COLS:
        if col in rule.index:
            val = rule[col]
            if pd.isna(val):
                entry[col] = None
            elif val == float('inf') or val == float('-inf'):
                entry[col] = None  # inf 视为无定义
            else:
                entry[col] = round(float(val), 4)
    rules_json.append(entry)

# 粗粒度规则 JSON（全量指标）
rules_l1_json = []
if has_l1_rules and len(association_rules_l1) > 0:
    for _, rule in association_rules_l1.head(20).iterrows():
        antecedent = rule['antecedents_str'] if 'antecedents_str' in association_rules_l1.columns else str(rule['antecedents'])
        consequent = rule['consequents_str'] if 'consequents_str' in association_rules_l1.columns else str(rule['consequents'])
        entry = {
            'antecedent': antecedent,
            'consequent': consequent,
            'antecedent_support': round(float(rule['antecedent support']), 4) if 'antecedent support' in rule.index else None,
            'consequent_support': round(float(rule['consequent support']), 4) if 'consequent support' in rule.index else None,
            'support': round(float(rule['support']), 4),
            'confidence': round(float(rule['confidence']), 4),
            'lift': round(float(rule['lift']), 4),
            'representativity': round(float(rule['representativity']), 4) if 'representativity' in rule.index else None,
        }
        for col in RULE_EXTRA_COLS:
            if col in rule.index:
                val = rule[col]
                if pd.isna(val):
                    entry[col] = None
                elif val == float('inf') or val == float('-inf'):
                    entry[col] = None
                else:
                    entry[col] = round(float(val), 4)
        rules_l1_json.append(entry)

# 频繁项集 JSON
frequent_itemsets_json = []
for _, row in frequent_itemsets.iterrows():
    frequent_itemsets_json.append({
        'itemsets': str(row['itemsets']),
        'support': round(float(row['support']), 4),
    })

# 粗粒度频繁项集 JSON
frequent_itemsets_l1_json = []
if os.path.exists('../result/models/frequent_itemsets_l1.csv'):
    _fi_l1 = pd.read_csv('../result/models/frequent_itemsets_l1.csv')
    for _, row in _fi_l1.iterrows():
        frequent_itemsets_l1_json.append({
            'itemsets': str(row['itemsets']),
            'support': round(float(row['support']), 4),
        })

# 热门品类 JSON
view_by_cat_15 = df_with_category[df_with_category['event_type'] == 'view']['category_code'].value_counts().head(15)
purchase_by_cat_15 = df_with_category[df_with_category['event_type'] == 'purchase']['category_code'].value_counts().head(15)
revenue_by_cat_15 = purchase_df.groupby('category_code')['price'].sum().sort_values(ascending=False).head(15)

hot_categories_json = {
    'top5_by_views': [{'category': cat, 'count': int(count)} for cat, count in view_by_cat.items()],
    'top5_by_purchases': [{'category': cat, 'count': int(count)} for cat, count in purchase_by_cat.items()],
    'top5_by_revenue': [{'category': cat, 'amount': round(float(amount), 2)} for cat, amount in revenue_by_cat.items()],
    'top15_by_views': [{'category': cat, 'count': int(count)} for cat, count in view_by_cat_15.items()],
    'top15_by_purchases': [{'category': cat, 'count': int(count)} for cat, count in purchase_by_cat_15.items()],
    'top15_by_revenue': [{'category': cat, 'amount': round(float(amount), 2)} for cat, amount in revenue_by_cat_15.items()],
    'category_conversion_rates': [
        {
            'category': str(cat),
            'views': int(cat_funnel.loc[cat, 'view']) if 'view' in cat_funnel.columns else 0,
            'purchases': int(cat_funnel.loc[cat, 'purchase']) if 'purchase' in cat_funnel.columns else 0,
            'conversion_rate': float(cat_funnel.loc[cat, 'conversion_rate']) if not pd.isna(cat_funnel.loc[cat, 'conversion_rate']) else None
        }
        for cat in top15_cats.index
    ],
}

# 为 time_analysis 补充完整小时/星期数据
weekday_counts_full = df.groupby('Weekday')['event_type'].count().reindex(range(7), fill_value=0)
hourly_by_type_dict = {}
for event_type in ['view', 'cart', 'purchase']:
    hourly_by_type_dict[event_type] = df[df['event_type'] == event_type].groupby('Hour').size()

summary = {
    'data_overview': {
        'total_events': total_events_raw,
        'total_users': total_users,
        'total_sessions': total_sessions,
        'sessions_after_outlier_filter': len(_labels),
        'outlier_sessions_removed': total_sessions - len(_labels),
        'total_categories': total_categories,
        'date_range': date_range_str,
    },
    'behavior_funnel': {
        'view_count': view_count,
        'cart_count': cart_count,
        'purchase_count': purchase_count,
        'cart_rate': cart_rate,
        'purchase_rate': purchase_rate,
        'cart_to_purchase_rate': cart_to_purchase_rate,
    },
    'time_analysis': {
        'peak_hour': peak_hour,
        'peak_hour_count': peak_hour_count,
        'low_hour': low_hour,
        'low_hour_count': low_hour_count,
        'most_active_day': most_active_day,
        'least_active_day': least_active_day,
        'weekday_pct': weekday_pct,
        'weekend_pct': weekend_pct,
        'hourly_counts': {str(h): int(hourly_counts.get(h, 0)) for h in range(24)},
        'weekday_counts': {weekday_names[i]: int(weekday_counts.get(i, 0)) for i in range(7)},
        'hourly_by_type': {
            event_type: {str(h): int(hourly_by_type_series.get(h, 0)) for h in range(24)}
            for event_type, hourly_by_type_series in hourly_by_type_dict.items()
        },
    },
    'user_statistics': {
        'total_users': total_users,
        'purchasing_users': purchasing_users,
        'purchasing_user_rate': purchasing_user_rate,
        'avg_views_per_user': avg_views_per_user,
        'avg_purchases_per_user': avg_purchases_per_user,
        'avg_sessions_per_user': avg_sessions_per_user,
        'avg_spend_per_user': avg_spend_per_user,
        'users_with_views': int((user_event_counts.get('view', pd.Series(dtype=float)) > 0).sum()) if len(user_event_counts) > 0 else 0,
        'users_with_carts': int((user_event_counts.get('cart', pd.Series(dtype=float)) > 0).sum()) if len(user_event_counts) > 0 else 0,
        'avg_carts_per_user': round(user_event_counts.get('cart', pd.Series(dtype=float)).mean(), 2) if len(user_event_counts) > 0 else 0,
        'purchase_count_distribution': {
            str(int(k)): int(v) for k, v in user_event_counts.get('purchase', pd.Series(dtype=float)).value_counts().sort_index().head(10).items()
        } if len(user_event_counts) > 0 else {},
    },
    'hot_categories': hot_categories_json,
    'hot_products_total_count': len(hot_products),
    'hot_products': [
        {
            'rank': i + 1,
            'product_id': str(row['product_id']),
            'category': row['category_code'],
            'brand': row['brand'],
            'price': round(float(row['price']), 2),
            'view_count': int(row['view_count']),
            'purchase_count': int(row['purchase_count']),
            'revenue': round(float(row['revenue']), 2),
            'conversion_rate': round(float(row['conversion_rate']), 2),
        }
        for i, (_, row) in enumerate(hot_products.head(20).iterrows())
    ],
    'price_analysis': {
        'best_range': str(best_price_range),
        'best_rate': float(best_price_rate),
        'worst_range': str(worst_price_range),
        'worst_rate': float(worst_price_rate),
        'ranges': [
            {
                'range': label,
                'event_count': int(price_funnel.loc[label, 'view'] + price_funnel.loc[label].get('cart', 0) + price_funnel.loc[label].get('purchase', 0)) if label in price_funnel.index else 0,
                'view_count': int(price_funnel.loc[label, 'view']) if label in price_funnel.index and 'view' in price_funnel.columns else 0,
                'purchase_count': int(price_funnel.loc[label, 'purchase']) if label in price_funnel.index and 'purchase' in price_funnel.columns else 0,
                'conversion_rate': float(price_funnel.loc[label, 'conversion_rate']) if label in price_funnel.index and not pd.isna(price_funnel.loc[label, 'conversion_rate']) else None
            }
            for label in price_labels
        ],
    },
    'clustering': {
        'method': '规则分层（单事件）+ K-Means（多事件）',
        'n_clusters': n_clusters,
        'n_single_clusters': n_single_clusters,
        'n_multi_clusters': n_clusters - n_single_clusters,
        'silhouette_score': round(float(sil_post_merge), 4),
        'profiles': cluster_profiles_json,
        'elbow_silhouette': {
            'k_range': list(_model_data['metadata'].get('k_range', range(2, 6))),
            'inertias': [round(float(v), 2) for v in _model_data['metadata'].get('inertias', [])],
            'silhouette_scores': [round(float(v), 4) for v in _model_data['metadata'].get('sil_scores', [])],
        },
    },
    'association_rules': {
        'method': 'Apriori',
        'min_support': 0.1,
        'n_frequent_itemsets': len(frequent_itemsets),
        'frequent_itemsets': frequent_itemsets_json,
        'n_frequent_itemsets_l1': len(frequent_itemsets_l1_json),
        'frequent_itemsets_l1': frequent_itemsets_l1_json,
        'n_rules_fine': len(rules_for_report),
        'n_rules_coarse': len(rules_l1_json),
        'coverage_fine_pct': rule_cross_pct,
        'coverage_coarse_pct': l1_rule_cross_pct,
        'rules_fine': rules_json,
        'rules_coarse': rules_l1_json,
        'network': {
            'nodes': list(set(
                [r['antecedent'] for r in rules_json] + [r['consequent'] for r in rules_json]
            )),
            'edges': [
                {'source': r['antecedent'], 'target': r['consequent'], 'lift': r['lift']}
                for r in rules_json
            ],
        },
    },
}

summary = convert_numpy_types(summary)

json_path = '../result/reports/analysis_summary.json'
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print(f"[OK] JSON 摘要已保存: {json_path}")

# ==================== 4. 生成 README.md ====================
print("\n" + "=" * 50)
print("4. 生成 README.md")
print("=" * 50)

if len(rules_for_report) > 0:
    top_rule = rules_for_report.iloc[0]
    top_antecedent = top_rule['antecedents_str'] if 'antecedents_str' in rules_for_report.columns else str(top_rule['antecedents'])
    top_consequent = top_rule['consequents_str'] if 'consequents_str' in rules_for_report.columns else str(top_rule['consequents'])
    top_lift = top_rule['lift']
    strongest_rule_text = f"{top_antecedent} ↔ {top_consequent}（Lift={top_lift:.2f}）"

    top5_rules_lines = []
    for i, (_, rule) in enumerate(rules_for_report.head(5).iterrows()):
        ant = rule['antecedents_str'] if 'antecedents_str' in rules_for_report.columns else str(rule['antecedents'])
        con = rule['consequents_str'] if 'consequents_str' in rules_for_report.columns else str(rule['consequents'])
        ant_short = ant.split('.')[-1] if '.' in ant else ant
        con_short = con.split('.')[-1] if '.' in con else con
        top5_rules_lines.append(f"| {i+1} | {ant_short} → {con_short} | {rule['support']:.4f} | {rule['confidence']:.4f} | {rule['lift']:.4f} |")
    top5_rules_table = "\n".join(top5_rules_lines)
else:
    strongest_rule_text = "无"
    top5_rules_table = "| - | 无关联规则 | - | - | - |"

cluster_size_summary = ""
for i in range(n_clusters):
    count = cluster_sizes.get(i, 0)
    pct = cluster_pcts[i]
    biz = cluster_profiles_business.iloc[i]
    label = get_cluster_label(i, biz)
    cluster_size_summary += f"  - Cluster {i}（{label}）: {count:,} 个会话（{pct}%）| 均事件 {biz['event_count']:.1f} | 均购买 {biz['purchase_count']:.2f}\n"

readme_content = f"""# Result 目录说明

本目录包含第二步"用户数据与商品关联规则分析"的所有输出结果。

## 目录结构

```
result/
├── figures/                        # 可视化图表
│   ├── funnel_analysis.png         # 行为漏斗分析图
│   ├── time_distribution.png       # 时间维度分析图
│   ├── category_ranking.png        # 品类热度分析图
│   ├── price_analysis.png          # 价格区间分析图
│   ├── user_statistics.png         # 用户级统计图
│   ├── elbow_silhouette.png        # 肘部法则和轮廓系数图
│   ├── cluster_radar.png           # 聚类雷达图
│   ├── cluster_pca.png             # 聚类PCA散点图
│   ├── cluster_comparison.png      # 聚类特征对比图
│   ├── association_scatter.png     # 关联规则散点图
│   ├── association_network.png     # 关联规则网络图
│   ├── association_top10.png       # Top10关联规则柱状图
│   └── association_top10_l1.png    # Top10粗粒度关联规则柱状图（若有粗粒度规则）
│
├── models/                         # 模型结果
│   ├── kmeans_model.pkl            # 聚类模型（规则分群+K-Means）
│   ├── cluster_profiles.csv        # 聚类用户画像（训练特征）
│   ├── cluster_profiles_business.csv # 聚类用户画像（业务特征）
│   ├── frequent_itemsets.csv       # 频繁项集
│   ├── association_rules.csv       # 关联规则结果
│   ├── frequent_itemsets_l1.csv    # 粗粒度频繁项集
│   ├── association_rules_l1.csv    # 粗粒度关联规则结果（若有粗粒度规则）
│   ├── hot_products.csv            # 商品级热度排行（product_id 级）
│   └── cluster_category_preferences.csv # 各聚类偏好品类分布
│
└── reports/                        # 分析报告
    ├── step2_analysis_report.md    # 第二步综合分析报告
    └── analysis_summary.json       # 全量分析结果 JSON 摘要
```

## 关键发现摘要

### 1. 用户行为特征

- **行为漏斗**：浏览({view_count:,}) → 加购({cart_count:,}) → 购买({purchase_count:,})
  - 浏览→加购转化率：{cart_rate}%
  - 浏览→购买转化率：{purchase_rate}%
  - 加购→购买转化率：{cart_to_purchase_rate}%

- **用户级统计**：
  - 总用户数：{total_users:,}
  - 有购买行为用户：{purchasing_users:,}（{purchasing_user_rate}%）
  - 人均浏览：{avg_views_per_user} 次
  - 人均购买：{avg_purchases_per_user} 次

- **品类热度**：
  - 浏览最高：{view_by_cat.index[0]}（{view_by_cat.values[0]:,}次）
  - 购买最高：{purchase_by_cat.index[0]}（{purchase_by_cat.values[0]:,}次）
  - 金额最高：{revenue_by_cat.index[0]}（{revenue_by_cat.values[0]:,.2f}）

### 2. 用户分群

- 聚类数量：{n_clusters}个（规则分群 {n_single_clusters} + K-Means {n_clusters - n_single_clusters}）
- 训练特征：{', '.join(cluster_profiles.columns.tolist())}
- 轮廓系数（多事件会话）：{sil_post_merge:.4f}
- 覆盖率：全量 {len(_labels):,} 个会话

**聚类分布**：
{cluster_size_summary}

### 3. 商品关联规则

- **细粒度**（category_code）：{trans_count} 个购买用户事务，{len(frequent_itemsets)} 个频繁项集，{len(rules_for_report)} 条去重规则，跨品类率 {rule_cross_pct}%
- **粗粒度**（一级品类）：{trans_l1_count} 个事务，{len(rules_l1_json)} 条去重规则，跨品类率 {l1_rule_cross_pct}%
- 最强规则：{strongest_rule_text}

**Top 5 细粒度关联规则**：

| 排名 | 规则 | 支持度 | 置信度 | 提升度 |
|------|------|--------|--------|--------|
{top5_rules_table}

## 分析脚本

| 脚本 | 功能 | 输入数据 | 输出文件 |
|------|------|---------|---------|
| step2_1_behavior_analysis.py | 用户行为特征分析 | preprocessed.csv | figures/funnel_*.png, time_*.png, category_*.png, price_*.png, user_*.png, models/hot_products.csv |
| step2_2_clustering.py | 用户分群分析 | session_based_features.csv | models/kmeans_model.pkl, models/cluster_profiles*.csv, models/cluster_category_preferences.csv, figures/cluster_*.png |
| step2_3_association_rules.py | 商品关联规则挖掘 | preprocessed.csv | models/frequent_itemsets*.csv, models/association_rules*.csv, figures/association_*.png |
| step2_4_report.py | 结果整合与报告 | 所有分析结果 | reports/step2_analysis_report.md, reports/analysis_summary.json |

---

*README 生成时间：{datetime.now().strftime('%Y-%m-%d')}*
"""

readme_path = '../result/README.md'
with open(readme_path, 'w', encoding='utf-8') as f:
    f.write(readme_content)
print(f"[OK] README 已保存: {readme_path}")

print("\n" + "=" * 50)
print("子任务 2.4 完成！（含 JSON 摘要）")
print("=" * 50)
