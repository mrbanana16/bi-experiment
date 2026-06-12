# 电商用户行为数据集说明

本数据集来源于公开电商平台用户行为记录，经过清洗和特征工程后，形成以下核心数据文件：

1. **事件级数据集** (`preprocessed.csv`)：每一行代表用户的一次行为（浏览、加购、购买等），包含原始字段及衍生时间特征。
2. **会话级特征数据集** (`session_based_features.csv`)：每一行代表一个用户会话（`user_session`），聚合了会话内的行为统计特征，用于用户分群、漏斗分析和推荐策略评估。
3. **Apriori 事务表** (`transactions_for_apriori.csv`)：每一行代表一个包含 2+ 品类的用户会话，用于关联规则挖掘。

---

## 一、事件级数据集 (`preprocessed.csv`)

### 文件描述
- 行数：92,793 行（经缺失值删除和去重后）
- 每行：一次用户事件（`event_type`）
- 数据来源：`raw/Dataset.csv` 经清洗、时间字段提取生成

### 字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| `event_time` | datetime | 事件发生时间（UTC），已去除 "UTC" 后缀，格式 `YYYY-MM-DD HH:MM:SS` |
| `event_type` | str | 事件类型：`view`（浏览）、`cart`（加入购物车）、`purchase`（购买） |
| `product_id` | int | 商品唯一标识 |
| `category_id` | int | 商品类别唯一标识（数字型层级代码） |
| `category_code` | str | 商品类别的英文路径，例如 `electronics.smartphone` |
| `brand` | str | 商品品牌 |
| `price` | float | 商品价格（美元） |
| `user_id` | int | 用户唯一标识 |
| `user_session` | str | 会话唯一标识（UUID 格式） |
| `Day` | int | 事件发生日期的"日"部分（1‑31） |
| `Hour` | int | 事件发生的小时（0‑23） |
| `Weekday` | int | 星期几，周一为 0，周日为 6 |
| `Is_Weekend` | bool | 是否为周末（`True` 表示周六或周日） |
| `At_night` | bool | 是否为夜间时段（小时 ≤ 6 或 ≥ 17） |
| `During_the_day` | bool | 是否为白天时段（6 < 小时 < 17） |

---

## 二、会话级特征数据集 (`session_based_features.csv`)

### 文件描述
- 形状：(88,070, 10)
- 每行：一个用户会话的聚合统计特征
- 生成方式：基于事件级数据集按 `user_session` 分组聚合

### 字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| `user_session` | str | 会话唯一标识 |
| `event_count` | int | 该会话内事件总次数 |
| `unique_products` | int | 会话内浏览/购买的不同商品数量 |
| `has_purchase` | bool | 会话是否包含至少一次购买事件 |
| `cart_count` | int | 会话内添加购物车的次数 |
| `purchase_count` | int | 会话内购买次数 |
| `session_duration_min` | float | 会话时长（分钟） |
| `purchase_amount` | float | 会话内购买总金额（若无购买则为 0） |
| `cart_to_purchase` | bool | 会话内是否存在先加购后购买的行为序列 |
| `unique_categories` | int | 会话内涉及的不同商品类别数 |

---

## 三、Apriori 事务表 (`transactions_for_apriori.csv`)

### 文件描述
- 每行：一个包含 2+ 商品类别的用户会话
- 用途：直接用于 Apriori 算法的关联规则挖掘

### 字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| `user_session` | str | 会话唯一标识 |
| `items` | str | 商品类别列表（Python 列表格式字符串，可用 `eval()` 转换） |

---

## 四、数据质量说明

- 缺失值处理：`category_code` 和 `brand` 中有缺失的行已全部删除
- 重复值处理：已删除完全重复的事件记录
- 时间字段：`event_time` 已统一为 datetime 类型，并去除了原始字符串中的 "UTC" 字样

---

## 五、文件版本与维护

- 创建日期：2026‑06‑12
- 最后更新：2026‑06‑13
- 文件编码：UTF‑8
