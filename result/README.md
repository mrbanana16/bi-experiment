# Result 目录说明

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

- **行为漏斗**：浏览(88,393) → 加购(2,571) → 购买(1,829)
  - 浏览→加购转化率：2.91%
  - 浏览→购买转化率：2.07%
  - 加购→购买转化率：71.14%

- **时间规律**：
  - 高峰时段：12时
  - 最活跃日：周四
  - 工作日占比：74.1%

- **品类热度**：
  - 浏览最高：electronics.smartphone（37,102次）
  - 购买最高：electronics.smartphone（1,130次）
  - 金额最高：electronics.smartphone（528,089.79）

- **价格区间**：
  - 100-200区间转化率最高（2.37%）
  - 50-100区间转化率最低（1.3%）

### 2. 用户分群

- 聚类数量：10个（根据轮廓系数自动确定）
- 聚类特征：event_count, unique_products, cart_count, purchase_count, session_duration_min, purchase_amount, unique_categories
- 聚类画像：详见 `result/models/cluster_profiles.csv`

### 3. 商品关联规则

- 频繁项集：67个
- 关联规则：30条
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
4. **时间营销**：在高峰时段（12时）和活跃日（周四）加大营销力度

---

*README 生成时间：2026-06-13*
