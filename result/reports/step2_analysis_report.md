# 第二步：用户数据与商品关联规则分析报告

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
- 总事件数：92,793 条
- 用户数：81,103 个
- 会话数：88,070 个
- 商品类别数：123 个
- 数据时间范围：2019-10-01 ~ 2019-10-31

> **注意**：时间维度分析（高峰时段、最活跃星期等）仅反映 2019 年 10 月的特征，不一定适用于其他时间段。

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

| 时段 | 事件数 | 时段 | 事件数 |
|------|--------|------|--------|
| 0:00 | 3,627 | 12:00 | 3,992 |
| 1:00 | 3,580 | 13:00 | 3,960 |
| 2:00 | 3,734 | 14:00 | 3,931 |
| 3:00 | 3,785 | 15:00 | 3,920 |
| 4:00 | 3,885 | 16:00 | 3,830 |
| 5:00 | 3,924 | 17:00 | 3,852 |
| 6:00 | 3,980 | 18:00 | 3,761 |
| 7:00 | 3,962 | 19:00 | 3,833 |
| 8:00 | 3,984 | 20:00 | 3,840 |
| 9:00 | 3,933 | 21:00 | 3,936 |
| 10:00 | 3,943 | 22:00 | 3,891 |
| 11:00 | 3,982 | 23:00 | 3,728 |

**按星期分布**：
- 最活跃：周四（15,193次）
- 最不活跃：周六（11,938次）

| 星期 | 事件数 |
|------|--------|
| 周一 | 11,953 |
| 周二 | 14,666 |
| 周三 | 14,986 |
| 周四 | 15,193 |
| 周五 | 11,956 |
| 周六 | 11,938 |
| 周日 | 12,101 |

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

**品类转化率排行（Top15 by 浏览量）**：

| 品类 | 浏览量 | 购买量 | 转化率 |
|------|--------|--------|--------|
| electronics.smartphone | 37,102 | 1,130 | 3.05% |
| electronics.clocks | 4,095 | 61 | 1.49% |
| computers.notebook | 3,780 | 41 | 1.08% |
| electronics.audio.headphone | 3,619 | 122 | 3.37% |
| electronics.video.tv | 3,448 | 57 | 1.65% |
| appliances.kitchen.washer | 2,789 | 41 | 1.47% |
| appliances.environment.vacuum | 2,453 | 42 | 1.71% |
| appliances.kitchen.refrigerators | 2,264 | 38 | 1.68% |
| apparel.shoes | 2,115 | 9 | 0.43% |
| computers.desktop | 1,455 | 12 | 0.82% |
| apparel.shoes.keds | 1,271 | 14 | 1.1% |
| electronics.tablet | 1,079 | 17 | 1.58% |
| auto.accessories.player | 1,033 | 10 | 0.97% |
| electronics.audio.subwoofer | 900 | 3 | 0.33% |
| electronics.telephone | 857 | 9 | 1.05% |

### 3.4 价格区间分析

| 价格区间 | 浏览量 | 购买量 | 转化率 |
|---------|--------|--------|--------|
| 0-50 | 9,637 | 170 | 1.76% |
| 50-100 | 11,037 | 144 | 1.3% |
| 100-200 | 21,668 | 513 | 2.37% |
| 200-500 | 26,407 | 568 | 2.15% |
| 500-1000 | 12,705 | 285 | 2.24% |
| 1000+ | 6,939 | 149 | 2.15% |

**关键发现**：
- 100-200价格区间转化率最高（2.37%）
- 50-100价格区间转化率最低（1.3%）


### 3.5 用户级统计

| 指标 | 数值 |
|------|------|
| 总用户数 | 81,103 |
| 有浏览行为用户 | 77,528 |
| 有加购行为用户 | 2,515 |
| 有购买行为用户 | 1,801（2.22%） |
| 人均浏览次数 | 1.09 |
| 人均加购次数 | 0.03 |
| 人均购买次数 | 0.02 |
| 人均会话数 | 1.09 |
| 人均消费金额 | 8.26 |

**用户购买次数分布**：

| 购买次数 | 用户数 |
|---------|--------|
| 0 次 | 79,302 |
| 1 次 | 1,776 |
| 2 次 | 22 |
| 3 次 | 3 |


### 3.6 热门商品 Top20

| 排名 | 商品ID | 品类 | 品牌 | 价格 | 浏览量 | 购买量 | 金额 | 转化率 |
|------|--------|------|------|------|--------|--------|------|--------|
| 1 | 1004856 | electronics.smartphone | samsung | 130.76 | 1,437 | 76 | 9,972.05 | 5.29% |
| 2 | 1004767 | electronics.smartphone | samsung | 254.82 | 1,312 | 65 | 16,181.63 | 4.95% |
| 3 | 1005115 | electronics.smartphone | apple | 975.57 | 1,213 | 35 | 34,499.06 | 2.89% |
| 4 | 1004249 | electronics.smartphone | apple | 739.81 | 737 | 31 | 22,896.59 | 4.21% |
| 5 | 1005105 | electronics.smartphone | apple | 1415.48 | 717 | 21 | 29,575.15 | 2.93% |
| 6 | 1004833 | electronics.smartphone | samsung | 174.76 | 683 | 37 | 6,371.56 | 5.42% |
| 7 | 1002544 | electronics.smartphone | apple | 464.13 | 646 | 35 | 16,128.06 | 5.42% |
| 8 | 1004870 | electronics.smartphone | samsung | 286.86 | 640 | 43 | 12,249.20 | 6.72% |
| 9 | 4804056 | electronics.audio.headphone | apple | 161.98 | 627 | 46 | 7,394.78 | 7.34% |
| 10 | 1004741 | electronics.smartphone | xiaomi | 185.71 | 522 | 23 | 4,392.20 | 4.41% |
| 11 | 1004873 | electronics.smartphone | samsung | 388.81 | 482 | 24 | 8,958.26 | 4.98% |
| 12 | 1004836 | electronics.smartphone | samsung | 241.19 | 468 | 17 | 3,923.97 | 3.63% |
| 13 | 1004739 | electronics.smartphone | xiaomi | 197.55 | 458 | 14 | 2,667.57 | 3.06% |
| 14 | 1005160 | electronics.smartphone | xiaomi | 231.41 | 435 | 17 | 3,746.93 | 3.91% |
| 15 | 1002524 | electronics.smartphone | apple | 515.67 | 409 | 30 | 15,860.88 | 7.33% |
| 16 | 1002633 | electronics.smartphone | apple | 360.08 | 408 | 24 | 8,604.20 | 5.88% |
| 17 | 1004785 | electronics.smartphone | huawei | 278.55 | 388 | 17 | 4,637.92 | 4.38% |
| 18 | 1005100 | electronics.smartphone | samsung | 154.42 | 378 | 12 | 1,719.04 | 3.17% |
| 19 | 4804295 | electronics.audio.headphone | xiaomi | 23.13 | 375 | 17 | 385.30 | 4.53% |
| 20 | 1004565 | electronics.smartphone | huawei | 177.47 | 368 | 20 | 3,372.11 | 5.43% |


---

## 四、用户分群分析

### 4.1 聚类方法
- 算法：规则分层（单事件会话）+ K-Means（多事件会话）
- 训练特征：event_count, cart_count, purchase_count, log_purchase_amount, has_purchase, has_duration
- 标准化：StandardScaler
- 最优K值选择（多事件会话，肘部法则 + 轮廓系数）：

| K | Inertia | 轮廓系数 |
|---|---------|---------|
| 2 | 12,675.20 | 0.9188 |
| 3 | 8,525.86 | 0.9201 |
| 4 | 5,089.29 | 0.8774 |
| 5 | 2,146.50 | 0.9461 |

> 选择 K=5，轮廓系数最高（0.9461）。
- 数据预处理：
  - 移除 session_duration_min > 1440 分钟的异常会话
  - 单事件会话（event_count=1）用规则分为浏览/加购/购买三类
  - 多事件会话（event_count>1）用 K-Means 聚类
  - has_purchase、has_duration 为二值特征
  - purchase_amount 使用 log1p 变换处理右偏

### 4.2 聚类结果

共分为 7 个聚类（规则分群 3 + K-Means 聚类 4，已自动合并小于 10 个样本的小聚类）：


#### Cluster 0（仅浏览型，79,863 个会话，占 90.7%）

**业务特征**：
- 平均事件数：1.00
- 平均商品数：1.00
- 平均加购数：0.00
- 平均购买数：0.00
- 平均会话时长：0.00 分钟
- 平均购买金额：0.00
- 平均品类数：1.00

**训练特征**（聚类决策依据）：
- event_count: 1.00, cart_count: 0.00, purchase_count: 0.00
- log_purchase_amount: 0.0000, has_purchase: 0.00, has_duration: 0.00

#### Cluster 1（加购未转化型，2,340 个会话，占 2.6%）

**业务特征**：
- 平均事件数：1.00
- 平均商品数：1.00
- 平均加购数：1.00
- 平均购买数：0.00
- 平均会话时长：0.00 分钟
- 平均购买金额：0.00
- 平均品类数：1.00

**训练特征**（聚类决策依据）：
- event_count: 1.00, cart_count: 1.00, purchase_count: 0.00
- log_purchase_amount: 0.0000, has_purchase: 0.00, has_duration: 0.00

#### Cluster 2（直接购买型，1,730 个会话，占 2.0%）

**业务特征**：
- 平均事件数：1.00
- 平均商品数：1.00
- 平均加购数：0.00
- 平均购买数：1.00
- 平均会话时长：0.00 分钟
- 平均购买金额：365.59
- 平均品类数：1.00

**训练特征**（聚类决策依据）：
- event_count: 1.00, cart_count: 0.00, purchase_count: 1.00
- log_purchase_amount: 5.4292, has_purchase: 1.00, has_duration: 0.00

#### Cluster 3（多次浏览型，3,437 个会话，占 3.9%）

**业务特征**：
- 平均事件数：2.00
- 平均商品数：1.85
- 平均加购数：0.00
- 平均购买数：0.00
- 平均会话时长：7.08 分钟
- 平均购买金额：0.00
- 平均品类数：1.13

**训练特征**（聚类决策依据）：
- event_count: 2.00, cart_count: 0.00, purchase_count: 0.00
- log_purchase_amount: 0.0000, has_purchase: 0.00, has_duration: 1.00

#### Cluster 4（多事件购买型，95 个会话，占 0.1%）

**业务特征**：
- 平均事件数：2.13
- 平均商品数：1.44
- 平均加购数：0.21
- 平均购买数：1.04
- 平均会话时长：6.27 分钟
- 平均购买金额：397.93
- 平均品类数：1.12

**训练特征**（聚类决策依据）：
- event_count: 2.13, cart_count: 0.21, purchase_count: 1.04
- log_purchase_amount: 5.5164, has_purchase: 1.00, has_duration: 1.00

#### Cluster 5（多事件加购未转化型，182 个会话，占 0.2%）

**业务特征**：
- 平均事件数：2.14
- 平均商品数：1.46
- 平均加购数：1.16
- 平均购买数：0.00
- 平均会话时长：4.21 分钟
- 平均购买金额：0.00
- 平均品类数：1.08

**训练特征**（聚类决策依据）：
- event_count: 2.14, cart_count: 1.16, purchase_count: 0.00
- log_purchase_amount: 0.0000, has_purchase: 0.00, has_duration: 0.99

#### Cluster 6（深度浏览型，422 个会话，占 0.5%）

**业务特征**：
- 平均事件数：3.30
- 平均商品数：2.97
- 平均加购数：0.00
- 平均购买数：0.00
- 平均会话时长：18.81 分钟
- 平均购买金额：0.00
- 平均品类数：1.22

**训练特征**（聚类决策依据）：
- event_count: 3.30, cart_count: 0.00, purchase_count: 0.00
- log_purchase_amount: 0.0000, has_purchase: 0.00, has_duration: 1.00


### 4.2a 各聚类品类偏好

各聚类的浏览和购买 Top5 品类分布如下：


**Cluster 0（仅浏览型）**：

| 浏览排名 | 品类 | 数量 |
|--------|------|------|
| 1 | electronics.smartphone | 33,985 |
| 2 | electronics.clocks | 3,657 |
| 3 | electronics.audio.headphone | 3,308 |
| 4 | computers.notebook | 3,280 |
| 5 | electronics.video.tv | 3,131 |

| 加购排名 | 品类 | 数量 |
|--------|------|------|
| 1 | electronics.smartphone | 1,610 |
| 2 | electronics.audio.headphone | 178 |
| 3 | electronics.video.tv | 78 |
| 4 | electronics.clocks | 66 |
| 5 | appliances.kitchen.washer | 57 |


**Cluster 1（加购未转化型）**：

| 浏览排名 | 品类 | 数量 |
|--------|------|------|
| 1 | electronics.smartphone | 995 |
| 2 | computers.notebook | 121 |
| 3 | electronics.clocks | 103 |
| 4 | electronics.video.tv | 92 |
| 5 | electronics.audio.headphone | 82 |

| 加购排名 | 品类 | 数量 |
|--------|------|------|
| 1 | electronics.smartphone | 57 |
| 2 | electronics.audio.headphone | 4 |
| 3 | electronics.video.tv | 3 |
| 4 | auto.accessories.alarm | 2 |
| 5 | appliances.environment.vacuum | 1 |

| 购买排名 | 品类 | 数量 |
|--------|------|------|
| 1 | electronics.smartphone | 26 |
| 2 | appliances.environment.vacuum | 2 |
| 3 | kids.toys | 1 |
| 4 | electronics.video.tv | 1 |
| 5 | apparel.shoes.keds | 1 |


**Cluster 2（直接购买型）**：

| 加购排名 | 品类 | 数量 |
|--------|------|------|
| 1 | electronics.smartphone | 30 |
| 2 | electronics.video.tv | 4 |
| 3 | appliances.environment.vacuum | 2 |
| 4 | electronics.telephone | 2 |
| 5 | auto.accessories.alarm | 1 |

| 购买排名 | 品类 | 数量 |
|--------|------|------|
| 1 | electronics.smartphone | 1,067 |
| 2 | electronics.audio.headphone | 111 |
| 3 | electronics.clocks | 59 |
| 4 | electronics.video.tv | 55 |
| 5 | appliances.environment.vacuum | 40 |


**Cluster 3（多次浏览型）**：

| 浏览排名 | 品类 | 数量 |
|--------|------|------|
| 1 | electronics.smartphone | 2,450 |
| 2 | computers.notebook | 396 |
| 3 | electronics.clocks | 373 |
| 4 | electronics.audio.headphone | 261 |
| 5 | electronics.video.tv | 251 |

| 加购排名 | 品类 | 数量 |
|--------|------|------|
| 1 | electronics.smartphone | 65 |
| 2 | electronics.audio.headphone | 6 |
| 3 | electronics.video.tv | 3 |
| 4 | electronics.clocks | 2 |
| 5 | appliances.kitchen.refrigerators | 2 |


**Cluster 4（多事件购买型）**：

| 浏览排名 | 品类 | 数量 |
|--------|------|------|
| 1 | electronics.smartphone | 50 |
| 2 | electronics.audio.headphone | 8 |
| 3 | appliances.sewing_machine | 3 |
| 4 | electronics.video.tv | 3 |
| 5 | computers.notebook | 2 |

| 加购排名 | 品类 | 数量 |
|--------|------|------|
| 1 | electronics.smartphone | 1 |
| 2 | electronics.audio.headphone | 1 |

| 购买排名 | 品类 | 数量 |
|--------|------|------|
| 1 | electronics.smartphone | 63 |
| 2 | electronics.audio.headphone | 11 |
| 3 | computers.notebook | 4 |
| 4 | electronics.tablet | 2 |
| 5 | electronics.clocks | 2 |


**Cluster 5（多事件加购未转化型）**：

| 浏览排名 | 品类 | 数量 |
|--------|------|------|
| 1 | electronics.smartphone | 120 |
| 2 | electronics.video.tv | 11 |
| 3 | electronics.clocks | 7 |
| 4 | electronics.audio.headphone | 7 |
| 5 | appliances.kitchen.blender | 7 |

| 加购排名 | 品类 | 数量 |
|--------|------|------|
| 1 | electronics.audio.headphone | 2 |
| 2 | electronics.smartphone | 1 |


**Cluster 6（深度浏览型）**：

| 浏览排名 | 品类 | 数量 |
|--------|------|------|
| 1 | electronics.smartphone | 496 |
| 2 | computers.notebook | 96 |
| 3 | electronics.clocks | 56 |
| 4 | appliances.kitchen.washer | 53 |
| 5 | electronics.video.tv | 52 |

| 加购排名 | 品类 | 数量 |
|--------|------|------|
| 1 | electronics.smartphone | 11 |
| 2 | electronics.audio.headphone | 2 |
| 3 | electronics.video.tv | 1 |
| 4 | computers.notebook | 1 |
| 5 | appliances.environment.vacuum | 1 |



### 4.3 聚类解释

根据各聚类的业务特征画像，自动归类如下：

- **Cluster 0（低活跃度用户）**：仅 1 次浏览（占比 90.7%），无后续行为
- **Cluster 1（加购未转化用户）**：仅 1 个事件为加购（占比 2.7%），未完成购买
- **Cluster 2（直接购买型用户）**：仅 1 个事件即完成购买（占比 2.0%），决策迅速
- **Cluster 3（浏览型用户）**：有浏览行为（均值 2.0 次），但无购买转化
- **Cluster 4（购买型用户）**：有购买行为（均值 1.0 次），购买金额 398
- **Cluster 5（加购未转化用户）**：有加购行为（均值 1.2 次），但未完成购买
- **Cluster 6（浏览探索型用户）**：浏览较活跃（均值 3.3 次），跨 1.2 个品类探索



### 4.4 全量用户覆盖率

本次分群覆盖全部 88,069 个会话（过滤异常后），包括：

| 分群方式 | 会话数 | 占比 | 说明 |
|---------|--------|------|------|
| 规则分群（单事件） | 83,933 | 95.3% | event_count=1，用规则分为浏览/加购/购买三类 |
| K-Means 聚类（多事件） | 4,136 | 4.7% | event_count>1，用 K-Means 聚类 |

**购买用户覆盖率**：规则分群中的"直接购买型"包含 1,730 个购买会话，
K-Means 聚类中的购买用户分布在多个聚类中，合计覆盖全部购买行为。


### 4.5 聚类局限性说明

> **数据预处理说明**：原始数据 95.3% 的会话仅有 1 个事件。本次分析采用分层策略：
> - 单事件会话用规则分群（浏览/加购/购买），覆盖 83,933 个会话
> - 多事件会话用 K-Means 聚类，覆盖 4,136 个会话
> - 合计覆盖全部 88,069 个会话
>
> **轮廓系数说明**：多事件会话的轮廓系数为 0.9461（合并前）/ 0.9425（合并后），
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
- 购买用户总数：1,801
- 跨品类用户：9（0.5%）
- 频繁项集数量：13
- 关联规则数量（去重）：4

### 5.3 Top 10 细粒度关联规则（按 Lift 排序）

| 排名 | 前项(Antecedent) | 后项(Consequent) | 支持度 | 置信度 | 提升度 |
|------|-----------------|-----------------|--------|--------|--------|
| 1 | appliances.kitchen.coffee_machine | electronics.clocks | 0.1111 | 1.0000 | 4.5000 |
| 2 | electronics.video.tv | appliances.kitchen.washer | 0.1111 | 1.0000 | 4.5000 |
| 3 | appliances.kitchen.oven | electronics.smartphone | 0.1111 | 1.0000 | 1.5000 |
| 4 | electronics.audio.headphone | electronics.smartphone | 0.4444 | 0.8000 | 1.2000 |


**最强关联规则**：
- **appliances.kitchen.coffee_machine** → **electronics.clocks**
- 支持度：0.1111（11.11%的购买用户同时购买了这两个品类）
- 置信度：1.0000（购买appliances.kitchen.coffee_machine的用户中，100.00%也会购买electronics.clocks）
- 提升度：4.5000（是随机购买的4.5倍）


**关联网络**：

关联规则形成了包含 7 个品类节点、4 条有向边的关联网络。主要关联路径：

- **appliances.kitchen.coffee_machine** → **electronics.clocks**（提升度 4.5）
- **electronics.video.tv** → **appliances.kitchen.washer**（提升度 4.5）
- **appliances.kitchen.oven** → **electronics.smartphone**（提升度 1.5）
- **electronics.audio.headphone** → **electronics.smartphone**（提升度 1.2）

**业务建议**：
1. 可以将关联性强的商品进行捆绑销售
2. 在商品详情页推荐关联商品
3. 针对购买了A商品的用户，推送B商品的优惠券

### 5.4 关联规则局限性说明

> **数据规模限制**：单月数据中仅 0.5% 的购买用户（9 人）涉及 2 个以上品类，
> 绝大多数用户仅购买单一品类。关联规则基于用户级共购行为挖掘，反映了真实的购买组合模式，
> 但跨品类样本量有限，规则的泛化能力受限。
>
> **建议**：扩大时间窗口（如 3-6 个月）以获取更多跨品类共购样本，提升规则的可信度和覆盖率。


### 5.5 粗粒度关联规则（一级品类）

将品类聚合到一级（如 `electronics.smartphone` → `electronics`），粗粒度覆盖率为 0.2%（细粒度为 0.5%）。

**粗粒度频繁项集**：

| 项集 | 支持度 |
|------|--------|
| appliances | 1.0000 |
| electronics | 1.0000 |
| appliances, electronics | 1.0000 |

**粗粒度关联规则：0 条**

所有跨品类购买用户均在同一一级品类（`electronics` 和 `appliances`）下购买，无法生成跨一级品类的关联规则。


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

with open('result/models/kmeans_model.pkl', 'rb') as f:
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

rules = pd.read_csv('result/models/association_rules.csv')

# 粗粒度规则（仅在存在时读取）
l1_path = 'result/models/association_rules_l1.csv'
rules_l1 = pd.read_csv(l1_path) if os.path.exists(l1_path) else pd.DataFrame()
```

### 7.3 如何使用聚类画像

```python
import pandas as pd

profiles = pd.read_csv('result/models/cluster_profiles_business.csv', index_col=0)
print(profiles)
```

---

## 八、总结

本分析完成了第二步的三个核心任务：

1. **用户行为特征分析**：揭示了用户行为的漏斗转化率、时间分布规律、品类热度和价格区间转化率，并增加了用户级统计分析。

2. **用户分群分析**：采用规则分层 + K-Means 混合策略，覆盖全量 88,069 个会话。单事件会话用规则分为浏览/加购/购买三类，多事件会话用 K-Means 聚类。

3. **商品关联规则挖掘**：发现了商品之间的关联关系。同时提供细粒度（category_code）和粗粒度（一级品类）两套分析结果。

这些分析结果可以为后续的**商品推荐策略设计**和**数据可视化展示**提供数据支持和业务洞察。

---

*报告生成时间：2026-06-15*
*分析脚本：src/step2_1_behavior_analysis.py, src/step2_2_clustering.py, src/step2_3_association_rules.py, src/step2_4_report.py*
