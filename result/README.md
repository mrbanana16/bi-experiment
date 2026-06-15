# Result 目录说明

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

- **行为漏斗**：浏览(88,393) → 加购(2,571) → 购买(1,829)
  - 浏览→加购转化率：2.91%
  - 浏览→购买转化率：2.07%
  - 加购→购买转化率：71.14%

- **用户级统计**：
  - 总用户数：81,103
  - 有购买行为用户：1,801（2.22%）
  - 人均浏览：1.09 次
  - 人均购买：0.02 次

- **品类热度**：
  - 浏览最高：electronics.smartphone（37,102次）
  - 购买最高：electronics.smartphone（1,130次）
  - 金额最高：electronics.smartphone（528,089.79）

### 2. 用户分群

- 聚类数量：7个（规则分群 3 + K-Means 4）
- 训练特征：event_count, cart_count, purchase_count, log_purchase_amount, has_purchase, has_duration
- 轮廓系数（多事件会话）：0.9425
- 覆盖率：全量 88,069 个会话

**聚类分布**：
  - Cluster 0（仅浏览型）: 79,863 个会话（90.7%）| 均事件 1.0 | 均购买 0.00
  - Cluster 1（加购未转化型）: 2,340 个会话（2.6%）| 均事件 1.0 | 均购买 0.00
  - Cluster 2（直接购买型）: 1,730 个会话（2.0%）| 均事件 1.0 | 均购买 1.00
  - Cluster 3（多次浏览型）: 3,437 个会话（3.9%）| 均事件 2.0 | 均购买 0.00
  - Cluster 4（多事件购买型）: 95 个会话（0.1%）| 均事件 2.1 | 均购买 1.04
  - Cluster 5（多事件加购未转化型）: 182 个会话（0.2%）| 均事件 2.1 | 均购买 0.00
  - Cluster 6（深度浏览型）: 422 个会话（0.5%）| 均事件 3.3 | 均购买 0.00


### 3. 商品关联规则

- **细粒度**（category_code）：9 个购买用户事务，13 个频繁项集，4 条去重规则，跨品类率 0.5%
- **粗粒度**（一级品类）：4 个事务，0 条去重规则，跨品类率 0.2%
- 最强规则：appliances.kitchen.coffee_machine ↔ electronics.clocks（Lift=4.50）

**Top 5 细粒度关联规则**：

| 排名 | 规则 | 支持度 | 置信度 | 提升度 |
|------|------|--------|--------|--------|
| 1 | coffee_machine → clocks | 0.1111 | 1.0000 | 4.5000 |
| 2 | tv → washer | 0.1111 | 1.0000 | 4.5000 |
| 3 | oven → smartphone | 0.1111 | 1.0000 | 1.5000 |
| 4 | headphone → smartphone | 0.4444 | 0.8000 | 1.2000 |

## 分析脚本

| 脚本 | 功能 | 输入数据 | 输出文件 |
|------|------|---------|---------|
| step2_1_behavior_analysis.py | 用户行为特征分析 | preprocessed.csv | figures/funnel_*.png, time_*.png, category_*.png, price_*.png, user_*.png, models/hot_products.csv |
| step2_2_clustering.py | 用户分群分析 | session_based_features.csv | models/kmeans_model.pkl, models/cluster_profiles*.csv, models/cluster_category_preferences.csv, figures/cluster_*.png |
| step2_3_association_rules.py | 商品关联规则挖掘 | preprocessed.csv | models/frequent_itemsets*.csv, models/association_rules*.csv, figures/association_*.png |
| step2_4_report.py | 结果整合与报告 | 所有分析结果 | reports/step2_analysis_report.md, reports/analysis_summary.json |

---

*README 生成时间：2026-06-15*
