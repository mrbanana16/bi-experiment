import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
# ==================== 1. 读取数据 ====================
df = pd.read_csv("./Datasets/raw/Opt 1/ecommerce_customer_behavior_dataset.csv")
print("原始数据形状:", df.shape)
print("缺失值统计:\n", df.isnull().sum())

# ==================== 2. 日期处理 ====================
df['Date'] = pd.to_datetime(df['Date'])
df['Year'] = df['Date'].dt.year
df['Month'] = df['Date'].dt.month
df['Day'] = df['Date'].dt.day    
df['Weekday'] = df['Date'].dt.dayofweek  # 0-based，周一为0，周日为6
df['Is_Weekend'] = (df['Weekday'] >= 5).astype(int)

# ==================== 3. 年龄分箱 ====================
bins = [0, 18, 25, 35, 45, 60, 100]
labels = ['<18', '18-24', '25-34', '35-44', '45-59', '60+']
df['Age_Group'] = pd.cut(df['Age'], bins=bins, labels=labels, right=False)

# ==================== 4. 衍生指标 ====================
# 平均每件商品价格（总金额 / 数量）
df['Avg_Price_Per_Unit'] = df['Total_Amount'] / df['Quantity']

# 折扣率 = 折扣金额 / (单价 * 数量)，防止除零
df['Discount_Rate'] = df['Discount_Amount'] / (df['Unit_Price'] * df['Quantity'])
df['Discount_Rate'] = df['Discount_Rate'].fillna(0).clip(0, 1)  # 限制在0~1

# 每分钟浏览页数（效率指标）
df['Pages_Per_Minute'] = df['Pages_Viewed'] / df['Session_Duration_Minutes']
df['Pages_Per_Minute'] = df['Pages_Per_Minute'].replace([np.inf, -np.inf], 0).fillna(0)

# ==================== 5. 分类变量编码 ====================
# 5.1 Label Encoding（二分类或有序）
le_gender = LabelEncoder()
df['Gender_Code'] = le_gender.fit_transform(df['Gender'])  # Female=0, Male=1, Other=2 

le_return = LabelEncoder()
df['Returning_Code'] = le_return.fit_transform(df['Is_Returning_Customer'])  # True=1, False=0 回头客

le_device = LabelEncoder()
df['Device_Code'] = le_device.fit_transform(df['Device_Type'])

# 5.2 One‑Hot Encoding（支付方式）
df = pd.get_dummies(df, columns=['Payment_Method'], prefix='Payment')

# ==================== 6. 用户级别聚合（用于 K‑Means 分群） ====================
user_features = df.groupby('Customer_ID').agg({
    'Total_Amount': 'sum',                   # 总消费金额
    'Age': 'first',                          # 年龄
    'Gender_Code': 'first',                  # 性别编码
    'Session_Duration_Minutes': 'mean',      # 平均会话时长
    'Pages_Viewed': 'mean',                  # 平均浏览页数
    'Returning_Code': 'first',               # 是否回头客
    'Delivery_Time_Days': 'mean',            # 平均配送天数
    'Customer_Rating': 'mean',               # 平均评分
    'Discount_Rate': 'mean',                 # 平均折扣率
    'Pages_Per_Minute': 'mean',              # 平均浏览效率
    'Is_Weekend': 'mean'                     # 周末购买比例
})

# 以总消费额为准添加消费分层
user_features['Spending_Level'] = pd.qcut(user_features['Total_Amount'],
                                          q=4,
                                          labels=['Low', 'Medium', 'High', 'Very High'])

# 重置索引，将 Customer_ID 变为列
user_features.reset_index(inplace=True)

# ==================== 7. 关联规则预处理（事务格式） ====================
# 按订单聚合商品类别列表
transactions = df.groupby('Order_ID')['Product_Category'].apply(list).reset_index()
transactions.columns = ['Order_ID', 'Item_Category']

# ==================== 8. 保存预处理结果 ====================
df.to_csv('./Datasets/processed/data_preprocessed_full.csv', index=False)          # 增强后的原始数据
user_features.to_csv('./Datasets/processed/user_behavioral_features_for_clustering.csv', index=False)  # 用户特征表 用于clustering
transactions.to_csv('./Datasets/processed/transactions_for_apriori.csv', index=False)       # 事务表 用于asso

print("预处理完成！")
print(f"原始记录数: {len(df)}")
print(f"用户数: {len(user_features)}")
print(f"订单数: {len(transactions)}")