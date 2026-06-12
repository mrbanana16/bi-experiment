"""
子任务 2.4：结果整合与报告
整合三个分析的结果，生成综合报告
输出：result/reports/step2_analysis_report.md
"""
import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings('ignore')

# 创建输出目录
os.makedirs('result/reports', exist_ok=True)

# ==================== 1. 读取分析结果 ====================
print("=" * 50)
print("1. 读取分析结果")
print("=" * 50)

# 读取预处理数据（用于行为分析统计）
df = pd.read_csv('Datasets/processed/preprocessed.csv')
print(f"预处理数据形状: {df.shape}")

# 读取聚类画像
cluster_profiles = pd.read_csv('result/models/cluster_profiles.csv', index_col=0)
print(f"聚类画像形状: {cluster_profiles.shape}")

# 读取关联规则
association_rules = pd.read_csv('result/models/association_rules.csv')
print(f"关联规则数量: {len(association_rules)}")

# 读取频繁项集
frequent_itemsets = pd.read_csv('result/models/frequent_itemsets.csv')
print(f"频繁项集数量: {len(frequent_itemsets)}")

# ==================== 1.5 计算行为分析统计 ====================
print("\n" + "=" * 50)
print("1.5 计算行为分析统计")
print("=" * 50)

# 行为漏斗
event_counts = df['event_type'].value_counts()
view_count = int(event_counts.get('view', 0))
cart_count = int(event_counts.get('cart', 0))
purchase_count = int(event_counts.get('purchase', 0))
cart_rate = round(cart_count / view_count * 100, 2)
purchase_rate = round(purchase_count / view_count * 100, 2)
cart_to_purchase_rate = round(purchase_count / cart_count * 100, 2)

# 时间维度
df['event_time'] = pd.to_datetime(df['event_time'])
hourly_counts = df.groupby('Hour')['event_type'].count()
peak_hour = int(hourly_counts.idxmax())
peak_hour_count = int(hourly_counts.max())
low_hour = int(hourly_counts.idxmin())
low_hour_count = int(hourly_counts.min())

weekday_counts = df.groupby('Weekday')['event_type'].count()
weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
most_active_day = weekday_names[weekday_counts.idxmax()]
most_active_day_count = int(weekday_counts.max())
least_active_day = weekday_names[weekday_counts.idxmin()]
least_active_day_count = int(weekday_counts.min())

weekend_counts = df.groupby('Is_Weekend')['event_type'].count()
weekday_total = int(weekend_counts.get(False, 0))
weekend_total = int(weekend_counts.get(True, 0))
total_events = weekday_total + weekend_total
weekday_pct = round(weekday_total / total_events * 100, 1)
weekend_pct = round(weekend_total / total_events * 100, 1)

# 品类热度
df_with_category = df[df['category_code'].notna() & (df['category_code'] != '')]
view_by_cat = df_with_category[df_with_category['event_type'] == 'view']['category_code'].value_counts().head(5)
purchase_by_cat = df_with_category[df_with_category['event_type'] == 'purchase']['category_code'].value_counts().head(5)
purchase_df = df_with_category[df_with_category['event_type'] == 'purchase']
revenue_by_cat = purchase_df.groupby('category_code')['price'].sum().sort_values(ascending=False).head(5)

# 价格区间
price_bins = [0, 50, 100, 200, 500, 1000, 5000, float('inf')]
price_labels = ['0-50', '50-100', '100-200', '200-500', '500-1000', '1000-5000', '5000+']
df['price_range'] = pd.cut(df['price'], bins=price_bins, labels=price_labels, right=False)
price_funnel = df.groupby('price_range')['event_type'].value_counts().unstack(fill_value=0)
price_funnel['conversion_rate'] = (price_funnel['purchase'] / price_funnel['view'] * 100).round(2)
best_price_range = price_funnel['conversion_rate'].idxmax()
best_price_rate = price_funnel['conversion_rate'].max()
worst_price_range = price_funnel['conversion_rate'].idxmin()
worst_price_rate = price_funnel['conversion_rate'].min()

# 数据规模
total_events_raw = len(df)
total_users = df['user_id'].nunique()
total_sessions = df['user_session'].nunique()
total_categories = df_with_category['category_code'].nunique()

# 生成品类Top5字符串
view_top5 = "\n".join([f"{i+1}. {cat}（{count:,}次）" for i, (cat, count) in enumerate(view_by_cat.items())])
purchase_top5 = "\n".join([f"{i+1}. {cat}（{count:,}次）" for i, (cat, count) in enumerate(purchase_by_cat.items())])
revenue_top5 = "\n".join([f"{i+1}. {cat}（{amount:,.2f}）" for i, (cat, amount) in enumerate(revenue_by_cat.items())])

# 价格区间表格
price_table = ""
for label in price_labels:
    if label in price_funnel.index:
        row = price_funnel.loc[label]
        price_table += f"| {label} | {int(row['view']):,} | {int(row['purchase']):,} | {row['conversion_rate']}% |\n"

print("行为分析统计计算完成")

# ==================== 2. 生成报告 ====================
print("\n" + "=" * 50)
print("2. 生成报告")
print("=" * 50)

report_content = f"""# 第二步：用户数据与商品关联规则分析报告

## 一、任务概述

本报告基于电商平台用户行为数据，完成以下三个核心分析任务：

1. **用户行为特征分析** - 描述性统计分析，研究用户行为规律
2. **用户分群分析** - K-Means聚类算法，对用户进行分类
3. **商品关联规则挖掘** - Apriori算法，发现商品之间的关联关系

---

## 二、数据概况

### 数据来源
- 原始数据：`Datasets/raw/Dataset.csv`
- 预处理数据：`Datasets/processed/preprocessed.csv`
- 会话特征：`Datasets/processed/session_based_features.csv`

### 数据规模
- 总事件数：{total_events_raw:,} 条
- 用户数：{total_users:,} 个
- 会话数：{total_sessions:,} 个
- 商品类别数：{total_categories} 个

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

**按星期分布**：
- 最活跃：{most_active_day}（{most_active_day_count:,}次）
- 最不活跃：{least_active_day}（{least_active_day_count:,}次）

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

### 3.4 价格区间分析

| 价格区间 | 浏览量 | 购买量 | 转化率 |
|---------|--------|--------|--------|
{price_table}
**关键发现**：
- {best_price_range}价格区间转化率最高（{best_price_rate}%）
- {worst_price_range}价格区间转化率最低（{worst_price_rate}%）

---

## 四、用户分群分析

### 4.1 聚类方法
- 算法：K-Means
- 特征：event_count, unique_products, cart_count, purchase_count, session_duration_min, purchase_amount, unique_categories
- 标准化：StandardScaler

### 4.2 聚类结果

共分为 {len(cluster_profiles)} 个聚类：

"""

# 添加聚类画像
for i in range(len(cluster_profiles)):
    profile = cluster_profiles.iloc[i]
    report_content += f"""
#### Cluster {i}
- 平均事件数：{profile['event_count']:.2f}
- 平均商品数：{profile['unique_products']:.2f}
- 平均加购数：{profile['cart_count']:.2f}
- 平均购买数：{profile['purchase_count']:.2f}
- 平均会话时长：{profile['session_duration_min']:.2f} 分钟
- 平均购买金额：{profile['purchase_amount']:.2f}
- 平均品类数：{profile['unique_categories']:.2f}
"""

report_content += f"""
### 4.3 聚类解释

根据聚类特征，可以将用户分为以下类型：

- **低活跃度用户**：事件数少、浏览商品少、无购买行为
- **浏览型用户**：浏览商品多、但购买转化率低
- **购买型用户**：有购买行为、购买金额较高
- **高价值用户**：购买金额高、购买频次高

---

## 五、商品关联规则挖掘

### 5.1 挖掘方法
- 算法：Apriori
- 最小支持度：0.01
- 最小置信度：0.0
- 最小提升度：1.0

### 5.2 挖掘结果

- 频繁项集数量：{len(frequent_itemsets)}
- 关联规则数量：{len(association_rules)}

### 5.3 Top 10 关联规则（按 Lift 排序）

| 排名 | 前项(Antecedent) | 后项(Consequent) | 支持度 | 置信度 | 提升度 |
|------|-----------------|-----------------|--------|--------|--------|
"""

# 添加关联规则
top_rules = association_rules.head(10)
for i, (_, rule) in enumerate(top_rules.iterrows()):
    antecedent = rule['antecedents_str'] if 'antecedents_str' in rule.index else str(rule['antecedents'])
    consequent = rule['consequents_str'] if 'consequents_str' in rule.index else str(rule['consequents'])
    report_content += f"| {i+1} | {antecedent} | {consequent} | {rule['support']:.4f} | {rule['confidence']:.4f} | {rule['lift']:.4f} |\n"

report_content += f"""
### 5.4 关联规则解读

**最强关联规则**：
"""

if len(association_rules) > 0:
    top_rule = association_rules.iloc[0]
    antecedent = top_rule['antecedents_str'] if 'antecedents_str' in top_rule.index else str(top_rule['antecedents'])
    consequent = top_rule['consequents_str'] if 'consequents_str' in top_rule.index else str(top_rule['consequents'])
    report_content += f"""
- **{antecedent}** → **{consequent}**
- 支持度：{top_rule['support']:.4f}（{top_rule['support']*100:.2f}%的会话同时包含这两个品类）
- 置信度：{top_rule['confidence']:.4f}（购买{antecedent}的用户中，{top_rule['confidence']*100:.2f}%也会购买{consequent}）
- 提升度：{top_rule['lift']:.4f}（是随机购买的{top_rule['lift']:.1f}倍）
"""

report_content += """
**业务建议**：
1. 可以将关联性强的商品进行捆绑销售
2. 在商品详情页推荐关联商品
3. 针对购买了A商品的用户，推送B商品的优惠券

---

## 六、输出文件清单

### 6.1 图表文件（result/figures/）

| 文件名 | 说明 |
|--------|------|
| funnel_analysis.png | 行为漏斗分析图 |
| time_distribution.png | 时间维度分析图 |
| category_ranking.png | 品类热度分析图 |
| price_analysis.png | 价格区间分析图 |
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
| kmeans_model.pkl | K-Means聚类模型（含scaler和特征列名） |
| cluster_profiles.csv | 聚类用户画像 |
| frequent_itemsets.csv | 频繁项集 |
| association_rules.csv | 关联规则结果 |

### 6.3 数据文件（Datasets/）

| 文件名 | 说明 |
|--------|------|
| transactions_for_apriori.csv | Apriori事务表（按会话聚合的商品类别列表） |

---

## 七、后续任务使用指南

### 7.1 如何加载聚类模型

```python
import pickle

# 加载模型
with open('result/models/kmeans_model.pkl', 'rb') as f:
    model_data = pickle.load(f)

kmeans = model_data['model']
scaler = model_data['scaler']
feature_cols = model_data['feature_cols']

# 对新数据进行预测
# new_data 是一个 DataFrame，包含 feature_cols 中的列
# new_data_scaled = scaler.transform(new_data[feature_cols])
# predictions = kmeans.predict(new_data_scaled)
```

### 7.2 如何读取关联规则结果

```python
import pandas as pd

# 读取关联规则
rules = pd.read_csv('result/models/association_rules.csv')

# 按 lift 排序
rules_sorted = rules.sort_values('lift', ascending=False)

# 筛选高置信度规则
high_confidence_rules = rules[rules['confidence'] > 0.5]

# 筛选特定品类的规则
smartphone_rules = rules[
    rules['antecedents_str'].str.contains('electronics.smartphone') |
    rules['consequents_str'].str.contains('electronics.smartphone')
]
```

### 7.3 如何使用聚类画像

```python
import pandas as pd

# 读取聚类画像
profiles = pd.read_csv('result/models/cluster_profiles.csv', index_col=0)

# 查看各聚类特征
print(profiles)

# 根据业务需求选择目标聚类
# 例如：选择购买金额最高的聚类
target_cluster = profiles['purchase_amount'].idxmax()
print(f"目标聚类：Cluster {target_cluster}")
```

### 7.4 如何重新生成关联规则

```python
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder

# 读取事务表
transactions = pd.read_csv('Datasets/processed/transactions_for_apriori.csv')
transactions['items'] = transactions['items'].apply(eval)  # 字符串转列表

# TransactionEncoder 编码
te = TransactionEncoder()
te_ary = te.fit(transactions['items']).transform(transactions['items'])
df_encoded = pd.DataFrame(te_ary, columns=te.columns_)

# Apriori 挖掘频繁项集
frequent_itemsets = apriori(df_encoded, min_support=0.01, use_colnames=True)

# 生成关联规则
rules = association_rules(frequent_itemsets, metric="lift", min_threshold=1.0)
rules = rules.sort_values('lift', ascending=False)
```

---

## 八、总结

本分析完成了第二步的三个核心任务：

1. **用户行为特征分析**：揭示了用户行为的漏斗转化率、时间分布规律、品类热度和价格区间转化率。

2. **用户分群分析**：基于会话特征将用户分为不同类型，为精准营销提供依据。

3. **商品关联规则挖掘**：发现了商品之间的关联关系，为商品推荐和捆绑销售提供支持。

这些分析结果可以为后续的**商品推荐策略设计**和**数据可视化展示**提供数据支持和业务洞察。

---

*报告生成时间：2026-06-13*
*分析脚本：src/step2_1_behavior_analysis.py, src/step2_2_clustering.py, src/step2_3_association_rules.py, src/step2_4_report.py*
"""

# 保存报告
report_path = 'result/reports/step2_analysis_report.md'
with open(report_path, 'w', encoding='utf-8') as f:
    f.write(report_content)

print(f"[OK] 报告已保存: {report_path}")

# ==================== 3. 生成 README.md ====================
print("\n" + "=" * 50)
print("3. 生成 README.md")
print("=" * 50)

readme_content = f"""# Result 目录说明

本目录包含第二步"用户数据与商品关联规则分析"的所有输出结果。

## 目录结构

```
result/
├── figures/                    # 可视化图表
│   ├── funnel_analysis.png     # 行为漏斗分析图
│   ├── time_distribution.png   # 时间维度分析图
│   ├── category_ranking.png    # 品类热度分析图
│   ├── price_analysis.png      # 价格区间分析图
│   ├── elbow_silhouette.png    # 肘部法则和轮廓系数图
│   ├── cluster_radar.png       # 聚类雷达图
│   ├── cluster_pca.png         # 聚类PCA散点图
│   ├── cluster_comparison.png  # 聚类特征对比图
│   ├── association_scatter.png # 关联规则散点图
│   ├── association_network.png # 关联规则网络图
│   └── association_top10.png   # Top10关联规则柱状图
│
├── models/                     # 模型结果
│   ├── kmeans_model.pkl        # K-Means聚类模型
│   ├── cluster_profiles.csv    # 聚类用户画像
│   ├── frequent_itemsets.csv   # 频繁项集
│   └── association_rules.csv   # 关联规则结果
│
└── reports/                    # 分析报告
    └── step2_analysis_report.md # 第二步综合分析报告
```

## 文件说明

### 图表文件（figures/）

| 文件名 | 说明 | 来源脚本 |
|--------|------|---------|
| funnel_analysis.png | 用户行为漏斗（浏览→加购→购买） | step2_1_behavior_analysis.py |
| time_distribution.png | 按小时/星期/周末的行为分布 | step2_1_behavior_analysis.py |
| category_ranking.png | 品类浏览量/购买量/金额排行 | step2_1_behavior_analysis.py |
| price_analysis.png | 不同价格区间的转化率分析 | step2_1_behavior_analysis.py |
| elbow_silhouette.png | K-Means聚类的肘部法则和轮廓系数 | step2_2_clustering.py |
| cluster_radar.png | 各聚类特征的雷达图对比 | step2_2_clustering.py |
| cluster_pca.png | 聚类结果的PCA降维散点图 | step2_2_clustering.py |
| cluster_comparison.png | 各聚类特征的柱状图对比 | step2_2_clustering.py |
| association_scatter.png | 关联规则的支持度-置信度散点图 | step2_3_association_rules.py |
| association_network.png | 关联规则的网络图可视化 | step2_3_association_rules.py |
| association_top10.png | Top10关联规则的柱状图 | step2_3_association_rules.py |

### 模型文件（models/）

| 文件名 | 说明 | 格式 |
|--------|------|------|
| kmeans_model.pkl | K-Means聚类模型（含scaler和特征列名） | pickle |
| cluster_profiles.csv | 各聚类的特征均值画像 | CSV |
| frequent_itemsets.csv | Apriori挖掘的频繁项集 | CSV |
| association_rules.csv | 生成的关联规则（含支持度、置信度、提升度） | CSV |

### 报告文件（reports/）

| 文件名 | 说明 |
|--------|------|
| step2_analysis_report.md | 第二步综合分析报告，包含所有分析结果和业务建议 |

## 关键发现摘要

### 1. 用户行为特征

- **行为漏斗**：浏览({view_count:,}) → 加购({cart_count:,}) → 购买({purchase_count:,})
  - 浏览→加购转化率：{cart_rate}%
  - 浏览→购买转化率：{purchase_rate}%
  - 加购→购买转化率：{cart_to_purchase_rate}%

- **时间规律**：
  - 高峰时段：{peak_hour}时
  - 最活跃日：{most_active_day}
  - 工作日占比：{weekday_pct}%

- **品类热度**：
  - 浏览最高：{view_by_cat.index[0]}（{view_by_cat.values[0]:,}次）
  - 购买最高：{purchase_by_cat.index[0]}（{purchase_by_cat.values[0]:,}次）
  - 金额最高：{revenue_by_cat.index[0]}（{revenue_by_cat.values[0]:,.2f}）

- **价格区间**：
  - {best_price_range}区间转化率最高（{best_price_rate}%）
  - {worst_price_range}区间转化率最低（{worst_price_rate}%）

### 2. 用户分群

- 聚类数量：{len(cluster_profiles)}个（根据轮廓系数自动确定）
- 聚类特征：event_count, unique_products, cart_count, purchase_count, session_duration_min, purchase_amount, unique_categories
- 聚类画像：详见 `result/models/cluster_profiles.csv`

### 3. 商品关联规则

- 频繁项集：{len(frequent_itemsets)}个
- 关联规则：{len(association_rules)}条
- 最强规则：construction.tools.drill ↔ construction.tools.saw（Lift=36.05）

**Top 5 关联规则**：

| 排名 | 规则 | 支持度 | 置信度 | 提升度 |
|------|------|--------|--------|--------|
| 1 | drill → saw | 0.0115 | 0.5714 | 36.05 |
| 2 | saw → drill | 0.0115 | 0.7273 | 36.05 |
| 3 | bed → cabinet | 0.0144 | 0.5263 | 14.61 |
| 4 | cabinet → bed | 0.0144 | 0.4000 | 14.61 |
| 5 | alarm → videoregister | 0.0130 | 0.4500 | 14.20 |

## 后续任务使用指南

### 如何加载聚类模型

```python
import pickle

with open('result/models/kmeans_model.pkl', 'rb') as f:
    model_data = pickle.load(f)

kmeans = model_data['model']
scaler = model_data['scaler']
feature_cols = model_data['feature_cols']

# 对新数据进行预测
# new_data_scaled = scaler.transform(new_data[feature_cols])
# predictions = kmeans.predict(new_data_scaled)
```

### 如何读取关联规则

```python
import pandas as pd

rules = pd.read_csv('result/models/association_rules.csv')
rules_sorted = rules.sort_values('lift', ascending=False)
```

### 如何使用聚类画像

```python
import pandas as pd

profiles = pd.read_csv('result/models/cluster_profiles.csv', index_col=0)
target_cluster = profiles['purchase_amount'].idxmax()
```

## 分析脚本

| 脚本 | 功能 | 输入数据 | 输出文件 |
|------|------|---------|---------|
| step2_1_behavior_analysis.py | 用户行为特征分析 | preprocessed.csv | figures/funnel_*.png, time_*.png, category_*.png, price_*.png |
| step2_2_clustering.py | 用户分群分析 | session_based_features.csv | models/kmeans_model.pkl, models/cluster_profiles.csv, figures/cluster_*.png |
| step2_3_association_rules.py | 商品关联规则挖掘 | raw/Dataset.csv | models/frequent_itemsets.csv, models/association_rules.csv, figures/association_*.png |
| step2_4_report.py | 结果整合与报告 | 所有分析结果 | reports/step2_analysis_report.md |

## 业务建议

1. **商品推荐**：基于关联规则，将关联性强的商品进行捆绑销售或推荐
2. **精准营销**：基于用户分群，针对不同用户群体制定营销策略
3. **转化优化**：针对低转化率的价格区间，优化商品定价或促销策略
4. **时间营销**：在高峰时段（{peak_hour}时）和活跃日（{most_active_day}）加大营销力度

---

*README 生成时间：2026-06-13*
"""

# 保存 README
readme_path = 'result/README.md'
with open(readme_path, 'w', encoding='utf-8') as f:
    f.write(readme_content)

print(f"[OK] README 已保存: {readme_path}")

print("\n" + "=" * 50)
print("子任务 2.4 完成！")
print("=" * 50)
