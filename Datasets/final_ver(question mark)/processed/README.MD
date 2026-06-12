# 电商用户行为数据集说明

本数据集来源于公开电商平台用户行为记录，经过抽样、清洗和特征工程后，形成两个核心数据文件：

1. **事件级数据集** (`Dataset.csv`)：每一行代表用户的一次行为（浏览、加购、购买等），包含原始字段及衍生时间特征。
2. **会话级特征数据集** (`session_features.csv`)：每一行代表一个用户会话（`user_session`），聚合了会话内的行为统计特征，用于用户分群、漏斗分析和推荐策略评估。

以下分别介绍两个文件的结构、字段含义及典型用途。

---

## 一、事件级数据集 (`Dataset.csv`)

### 文件描述
- 行数：约 9.3 万行（经缺失值删除和去重后）
- 每行：一次用户事件（`event_type`）
- 数据来源：原始数据集抽样后，经清洗、时间字段提取生成

### 字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| `event_time` | datetime | 事件发生时间（UTC），已去除 "UTC" 后缀，格式 `YYYY-MM-DD HH:MM:SS` |
| `event_type` | str | 事件类型，包括 `view`（浏览）、`cart`（加入购物车）、`purchase`（购买）、`remove`（移除）等 |
| `product_id` | int | 商品唯一标识 |
| `category_id` | int | 商品类别唯一标识（数字型层级代码） |
| `category_code` | str | 商品类别的英文路径，例如 `electronics.smartphone`，缺失值已填充为 `"unknown"` |
| `brand` | str | 商品品牌，缺失值已填充为 `"unknown"` |
| `price` | float | 商品价格（美元） |
| `user_id` | int | 用户唯一标识 |
| `user_session` | str | 会话唯一标识（UUID 格式），一次会话代表用户从进入平台到离开或超时的一段连续行为 |
| **以下为新增时间特征** | | |
| `Day` | int | 事件发生日期的“日”部分（1‑31） |
| `Hour` | int | 事件发生的小时（0‑23） |
| `Weekday` | int | 星期几，周一为 0，周日为 6 |
| `Is_Weekend` | bool | 是否为周末（`True` 表示周六或周日） |
| `At_night` | bool | 是否为夜间时段（小时 ≤ 6 或 ≥ 17） |
| `During_the_day` | bool | 是否为白天时段（6 < 小时 < 17） |

### 典型用途
- 用户行为路径分析（按时间排序查看会话内事件序列）
- 时段活跃度分析（按小时/星期/周末分组统计事件量）
- 转化漏斗构建（`view` → `cart` → `purchase`）
- 商品热度与价格分布可视化

---

## 二、会话级特征数据集 (`session_features.csv`)

### 文件描述
- 形状：(88070, 10)
- 每行：一次用户会话的聚合统计特征
- 生成方式：基于事件级数据集按 `user_session` 分组聚合

### 字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| `user_session` | str | 会话唯一标识，与事件级数据集中的 `user_session` 对应 |
| `event_count` | int | 该会话内事件总次数（所有行为类型的计数） |
| `unique_products` | int | 会话内浏览/购买的不同商品数量 |
| `has_purchase` | bool | 会话是否包含至少一次购买事件 |
| `cart_count` | int | 会话内添加购物车的次数（`event_type = 'cart'`） |
| `purchase_count` | int | 会话内购买次数（`event_type = 'purchase'`） |
| `session_duration_min` | float | 会话时长（分钟），即会话内最大时间与最小时间的差值 |
| `purchase_amount` | float | 会话内购买总金额（若无购买则为 0） |
| `cart_to_purchase` | bool | 会话内是否存在 **先加购后购买** 的行为序列（按时间顺序，至少一次 `cart` 发生在第一次 `purchase` 之前） |
| `unique_categories` | int | 会话内涉及的不同商品类别数（基于 `category_code` 去重计数） |

### 典型用途
- 用户分群（K‑Means 聚类）：输入 `event_count`、`session_duration_min`、`purchase_amount` 等特征，识别高价值用户、浏览型用户等
- 转化漏斗分析：计算购买会话占比（`has_purchase` 的均值）、加购转化率（`cart_count > 0` 的会话中 `has_purchase` 的比例）
- 购物篮分析准备：筛选 `has_purchase = True` 且 `purchase_count >= 1` 的会话，提取购买商品集合用于关联规则挖掘
- 异常检测：例如 `event_count` 极大但 `session_duration_min` 极短的会话可能为爬虫行为
- 可视化 KPI：会话总数、平均会话时长、平均客单价、加购后购买比例等

---

## 三、文件关系与使用建议

- **主外键关联**：通过 `user_session` 字段可以关联两个文件。例如，从会话级特征中筛选出高价值会话，然后回到事件级数据中查看该会话的详细行为路径。
- **时间特征补充**：会话级特征没有直接包含时间属性，但可以通过事件级数据提取会话的开始时间（`min(event_time)`）、结束时间、所属星期等，按需二次聚合。
- **推荐分析流程**：
  1. 事件级数据 → 行为路径分析、时段热力图
  2. 会话级数据 → 用户分群、转化漏斗、关联规则事务准备
  3. 用户级数据（可基于 `user_id` 进一步聚合会话级特征） → RFM 分析、用户画像

---

## 四、数据质量说明

- 缺失值处理：`category_code` 和 `brand` 中有缺失的行以全部删除。
- 重复值处理：已删除完全重复的事件记录。
- 时间字段：`event_time` 已统一为 datetime 类型，并去除了原始字符串中的 "UTC" 字样。
- 抽样：原始数据经过按天+按小时分层抽样，保证了时间维度的均匀性。

---

## 五、文件版本与维护

- 创建日期：2026‑06‑12
- 最后更新：2026‑06‑12
- 文件编码：UTF‑8
- 以上全是AI生成
- 经过验证 session_based_features表除了会话ID（第一列）其他列均为unique，即值不单一
