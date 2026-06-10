
---

# 电商用户行为数据预处理说明

本项目针对电商订单数据进行预处理，生成三个核心文件，分别用于**描述性统计分析**、**用户分群（K-Means）** 和**关联规则挖掘（Apriori/FP-Growth）**。

## 文件清单

| 文件名 | 用途 |
|--------|------|
| `data_preprocessed_full.csv` | 增强后的原始数据，含原始字段 + 衍生特征 + 编码字段 |
| `user_behavioral_features_for_clustering.csv` | 用户级聚合特征表，每用户一行，用于 K-Means 聚类 |
| `transactions_for_apriori.csv` | 事务表，每订单一行，按订单聚合商品类别列表，用于关联规则挖掘 |

---

## 1. data_preprocessed_full.csv

### 字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| `Order_ID` | string | 订单唯一标识 |
| `Customer_ID` | string | 客户唯一标识 |
| `Date` | datetime | 交易日期 |
| `Age` | int | 客户年龄 |
| `Gender` | string | 性别（Female / Male / Other） |
| `City` | string | 客户所在城市 |
| `Product_Category` | string | 商品类别（如 Electronics, Fashion） |
| `Unit_Price` | float | 商品单价 |
| `Quantity` | int | 购买数量 |
| `Discount_Amount` | float | 折扣金额 |
| `Total_Amount` | float | 实际支付金额 |
| `Device_Type` | string | 设备类型（Mobile / Desktop / Tablet） |
| `Session_Duration_Minutes` | int | 会话时长（分钟） |
| `Pages_Viewed` | int | 浏览页面数 |
| `Is_Returning_Customer` | bool | 是否为回头客（True/False） |
| `Delivery_Time_Days` | int | 配送天数 |
| `Customer_Rating` | int | 客户评分（1-5） |

**衍生字段（预处理新增）**

| 字段名 | 类型 | 描述 |
|--------|------|------|
| `Year` | int | 年份 |
| `Month` | int | 月份 |
| `Day` | int | 日 |
| `Weekday` | int | 星期几（0=周一，6=周日） |
| `Is_Weekend` | int | 是否周末（1=周末，0=工作日） |
| `Age_Group` | string | 年龄分组：<18, 18-24, 25-34, 35-44, 45-59, 60+ |
| `Avg_Price_Per_Unit` | float | 平均每件商品价格 = `Total_Amount / Quantity` |
| `Discount_Rate` | float | 折扣率 = `Discount_Amount / (Unit_Price * Quantity)`，限制 [0,1] |
| `Pages_Per_Minute` | float | 每分钟浏览页数 = `Pages_Viewed / Session_Duration_Minutes`，无穷值/缺失值处理为 0 |
| `Gender_Code` | int | 性别编码（0=Female, 1=Male, 2=Other） |
| `Returning_Code` | int | 回头客编码（1=True, 0=False） |
| `Device_Code` | int | 设备编码（0=Desktop, 1=Mobile, 2=Tablet） |
| `Payment_Bank Transfer` | bool | 支付方式：银行转账 |
| `Payment_Cash on Delivery` | bool | 支付方式：货到付款 |
| `Payment_Credit Card` | bool | 支付方式：信用卡 |
| `Payment_Debit Card` | bool | 支付方式：借记卡 |
| `Payment_Digital Wallet` | bool | 支付方式：数字钱包 |

> 注：支付方式为 One‑Hot 编码，每列取值为 True/False。

---

## 2. user_behavioral_features_for_clustering.csv

以 `Customer_ID` 为分组键，对每个用户的行为数据进行聚合，生成用户级特征表，用于聚类分析。

### 字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| `Customer_ID` | string | 客户唯一标识 |
| `Total_Amount` | float | 总消费金额（该用户所有订单金额之和） |
| `Age` | int | 用户年龄（取第一次出现值） |
| `Gender_Code` | int | 性别编码（0=Female, 1=Male, 2=Other） |
| `Session_Duration_Minutes` | float | 平均会话时长（分钟） |
| `Pages_Viewed` | float | 平均浏览页数 |
| `Returning_Code` | int | 是否回头客（1=True, 0=False） |
| `Delivery_Time_Days` | float | 平均配送天数 |
| `Customer_Rating` | float | 平均评分 |
| `Discount_Rate` | float | 平均折扣率 |
| `Pages_Per_Minute` | float | 平均每分钟浏览页数（浏览效率） |
| `Is_Weekend` | float | 周末购买比例（0~1） |
| `Spending_Level` | string | 消费分层：按 `Total_Amount` 四分位数划分为 `Low`, `Medium`, `High`, `Very High` |

> 注：除明确标注 `first` 的字段外，其余数值型字段均为订单级别的简单平均。

---

## 3. transactions_for_apriori.csv

按订单聚合商品类别列表，每个订单对应一行，格式符合关联规则挖掘库（如 `mlxtend`、`efficient_apriori`）的输入要求。

### 字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| `Order_ID` | string | 订单唯一标识 |
| `Item_Category` | string | 该订单购买的商品类别列表（Python 列表的字符串表示，如 `"['Electronics','Toys']"`） |

> 读取时建议使用 `import ast; df['Item_Category'] = df['Item_Category'].apply(ast.literal_eval)` 转换为原生列表。

---

## 预处理脚本摘要

```python
# 主要预处理步骤
1. 日期解析 → 提取年、月、日、星期、是否周末
2. 年龄分箱 → Age_Group
3. 计算衍生指标：Avg_Price_Per_Unit, Discount_Rate, Pages_Per_Minute
4. 分类变量编码：
   - Label Encoding：Gender_Code, Returning_Code, Device_Code
   - One‑Hot Encoding：Payment_Method
5. 用户级别聚合 → user_features（含 Spending_Level 分层）
6. 事务数据构造 → transactions（Order_ID → list of Product_Category）
```

