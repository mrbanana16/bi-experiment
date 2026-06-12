# 第二步：用户数据与商品关联规则分析报告

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
- 总事件数：92,793 条
- 用户数：81,103 个
- 会话数：88,070 个
- 商品类别数：123 个

---

## 三、用户行为特征分析

### 3.1 行为漏斗分析

| 行为阶段 | 数量 | 转化率 |
|---------|------|--------|
| 浏览(View) | 88,393 | 100% |
| 加购(Cart) | 2,571 | 2.91% |
| 购买(Purchase) | 1,829 | 2.07% |

**关键发现**：
- 浏览到加购的转化率为 2.91%
- 浏览到购买的转化率为 2.07%
- 加购到购买的转化率为 71.14%（1,829/2,571）

### 3.2 时间维度分析

**按小时分布**：
- 高峰时段：12时（3,992次）
- 低谷时段：1时（3,580次）

**按星期分布**：
- 最活跃：周四（15,193次）
- 最不活跃：周六（11,938次）

**工作日vs周末**：
- 工作日：68,754次（74.1%）
- 周末：24,039次（25.9%）

### 3.3 品类热度分析

**浏览量Top5品类**：
1. electronics.smartphone（37,102次）
2. electronics.clocks（4,095次）
3. computers.notebook（3,780次）
4. electronics.audio.headphone（3,619次）
5. electronics.video.tv（3,448次）

**购买量Top5品类**：
1. electronics.smartphone（1,130次）
2. electronics.audio.headphone（122次）
3. electronics.clocks（61次）
4. electronics.video.tv（57次）
5. appliances.environment.vacuum（42次）

**购买金额Top5品类**：
1. electronics.smartphone（528,089.79）
2. computers.notebook（23,519.92）
3. electronics.video.tv（20,090.76）
4. electronics.clocks（15,363.82）
5. appliances.kitchen.refrigerators（14,112.92）

### 3.4 价格区间分析

| 价格区间 | 浏览量 | 购买量 | 转化率 |
|---------|--------|--------|--------|
| 0-50 | 9,637 | 170 | 1.76% |
| 50-100 | 11,037 | 144 | 1.3% |
| 100-200 | 21,668 | 513 | 2.37% |
| 200-500 | 26,407 | 568 | 2.15% |
| 500-1000 | 12,705 | 285 | 2.24% |
| 1000-5000 | 6,939 | 149 | 2.15% |

**关键发现**：
- 100-200价格区间转化率最高（2.37%）
- 50-100价格区间转化率最低（1.3%）

---

## 四、用户分群分析

### 4.1 聚类方法
- 算法：K-Means
- 特征：event_count, unique_products, cart_count, purchase_count, session_duration_min, purchase_amount, unique_categories
- 标准化：StandardScaler

### 4.2 聚类结果

共分为 10 个聚类：


#### Cluster 0
- 平均事件数：1.00
- 平均商品数：1.00
- 平均加购数：0.00
- 平均购买数：0.00
- 平均会话时长：0.00 分钟
- 平均购买金额：0.00
- 平均品类数：1.00

#### Cluster 1
- 平均事件数：1.04
- 平均商品数：1.01
- 平均加购数：0.01
- 平均购买数：1.00
- 平均会话时长：0.19 分钟
- 平均购买金额：159.83
- 平均品类数：1.00

#### Cluster 2
- 平均事件数：2.17
- 平均商品数：2.16
- 平均加购数：0.03
- 平均购买数：0.01
- 平均会话时长：13.54 分钟
- 平均购买金额：3.95
- 平均品类数：2.03

#### Cluster 3
- 平均事件数：2.02
- 平均商品数：2.00
- 平均加购数：0.00
- 平均购买数：0.00
- 平均会话时长：6.38 分钟
- 平均购买金额：0.10
- 平均品类数：1.00

#### Cluster 4
- 平均事件数：4.00
- 平均商品数：4.00
- 平均加购数：0.00
- 平均购买数：0.00
- 平均会话时长：4880.82 分钟
- 平均购买金额：0.00
- 平均品类数：2.00

#### Cluster 5
- 平均事件数：1.06
- 平均商品数：1.02
- 平均加购数：1.01
- 平均购买数：0.00
- 平均会话时长：0.18 分钟
- 平均购买金额：0.00
- 平均品类数：1.00

#### Cluster 6
- 平均事件数：1.07
- 平均商品数：1.04
- 平均加购数：0.01
- 平均购买数：1.01
- 平均会话时长：0.37 分钟
- 平均购买金额：1194.12
- 平均品类数：1.00

#### Cluster 7
- 平均事件数：1.05
- 平均商品数：1.00
- 平均加购数：0.01
- 平均购买数：1.00
- 平均会话时长：0.36 分钟
- 平均购买金额：537.63
- 平均品类数：1.00

#### Cluster 8
- 平均事件数：3.40
- 平均商品数：3.20
- 平均加购数：0.03
- 平均购买数：0.01
- 平均会话时长：26.37 分钟
- 平均购买金额：0.76
- 平均品类数：1.01

#### Cluster 9
- 平均事件数：2.03
- 平均商品数：1.00
- 平均加购数：0.01
- 平均购买数：0.00
- 平均会话时长：2.91 分钟
- 平均购买金额：0.00
- 平均品类数：1.00

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

- 频繁项集数量：67
- 关联规则数量：30

### 5.3 Top 10 关联规则（按 Lift 排序）

| 排名 | 前项(Antecedent) | 后项(Consequent) | 支持度 | 置信度 | 提升度 |
|------|-----------------|-----------------|--------|--------|--------|
| 1 | construction.tools.drill | construction.tools.saw | 0.0115 | 0.5714 | 36.0519 |
| 2 | construction.tools.saw | construction.tools.drill | 0.0115 | 0.7273 | 36.0519 |
| 3 | furniture.bedroom.bed | furniture.living_room.cabinet | 0.0144 | 0.5263 | 14.6105 |
| 4 | furniture.living_room.cabinet | furniture.bedroom.bed | 0.0144 | 0.4000 | 14.6105 |
| 5 | auto.accessories.alarm | auto.accessories.videoregister | 0.0130 | 0.4500 | 14.1955 |
| 6 | auto.accessories.videoregister | auto.accessories.alarm | 0.0130 | 0.4091 | 14.1955 |
| 7 | auto.accessories.player | electronics.audio.subwoofer | 0.0317 | 0.5366 | 11.2846 |
| 8 | electronics.audio.subwoofer | auto.accessories.player | 0.0317 | 0.6667 | 11.2846 |
| 9 | apparel.shoes | apparel.shoes.keds | 0.0389 | 0.4737 | 5.9770 |
| 10 | apparel.shoes.keds | apparel.shoes | 0.0389 | 0.4909 | 5.9770 |

### 5.4 关联规则解读

**最强关联规则**：

- **construction.tools.drill** → **construction.tools.saw**
- 支持度：0.0115（1.15%的会话同时包含这两个品类）
- 置信度：0.5714（购买construction.tools.drill的用户中，57.14%也会购买construction.tools.saw）
- 提升度：36.0519（是随机购买的36.1倍）

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
