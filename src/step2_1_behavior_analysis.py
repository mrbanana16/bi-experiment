"""
子任务 2.1：用户行为特征分析（描述性统计）
数据集：Datasets/processed/preprocessed.csv
输出：result/figures/ 下的各类图表
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体（Windows）
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 创建输出目录
os.makedirs('result/figures', exist_ok=True)

# ==================== 1. 读取数据 ====================
print("=" * 50)
print("1. 读取数据")
print("=" * 50)

df = pd.read_csv("Datasets/processed/preprocessed.csv")
print(f"数据形状: {df.shape}")
print(f"列名: {df.columns.tolist()}")
print(f"\n数据类型:\n{df.dtypes}")
print(f"\n缺失值统计:\n{df.isnull().sum()}")

# ==================== 2. 行为漏斗分析 ====================
print("\n" + "=" * 50)
print("2. 行为漏斗分析")
print("=" * 50)

# 统计各行为类型的数量
event_counts = df['event_type'].value_counts()
print(f"\n各行为类型数量:\n{event_counts}")

# 计算转化率
view_count = event_counts.get('view', 0)
cart_count = event_counts.get('cart', 0)
purchase_count = event_counts.get('purchase', 0)

# 防止除零
cart_rate = round(cart_count / view_count * 100, 2) if view_count > 0 else 0
purchase_rate = round(purchase_count / view_count * 100, 2) if view_count > 0 else 0

funnel_data = {
    '行为阶段': ['浏览(View)', '加购(Cart)', '购买(Purchase)'],
    '数量': [view_count, cart_count, purchase_count],
    '转化率': [100.0, cart_rate, purchase_rate]
}
funnel_df = pd.DataFrame(funnel_data)
print(f"\n漏斗分析:\n{funnel_df}")

# 绘制漏斗图
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

colors = ['#3498db', '#f39c12', '#e74c3c']
bars = axes[0].bar(funnel_data['行为阶段'], funnel_data['数量'], color=colors)
axes[0].set_title('用户行为漏斗 - 数量分布', fontsize=14, fontweight='bold')
axes[0].set_ylabel('数量')
y_offset = max(funnel_data['数量']) * 0.01
for bar, count in zip(bars, funnel_data['数量']):
    axes[0].text(bar.get_x() + bar.get_width()/2., bar.get_height() + y_offset,
                f'{count:,}', ha='center', va='bottom', fontsize=11)

bars2 = axes[1].bar(funnel_data['行为阶段'], funnel_data['转化率'], color=colors)
axes[1].set_title('用户行为漏斗 - 转化率', fontsize=14, fontweight='bold')
axes[1].set_ylabel('转化率 (%)')
cr_offset = max(funnel_data['转化率']) * 0.01
for bar, rate in zip(bars2, funnel_data['转化率']):
    axes[1].text(bar.get_x() + bar.get_width()/2., bar.get_height() + cr_offset,
                f'{rate}%', ha='center', va='bottom', fontsize=11)

plt.tight_layout()
plt.savefig('result/figures/funnel_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print("\n[OK] funnel_analysis.png saved")

# ==================== 3. 时间维度分析 ====================
print("\n" + "=" * 50)
print("3. 时间维度分析")
print("=" * 50)

# 防御性检查：确认时间相关列存在
required_time_cols = ['Hour', 'Weekday', 'Is_Weekend']
missing_cols = [c for c in required_time_cols if c not in df.columns]
if missing_cols:
    raise ValueError(f"预处理数据缺少时间列: {missing_cols}，请检查预处理步骤")

hourly_counts = df.groupby('Hour')['event_type'].count()
print(f"\n按小时分布（前5）:\n{hourly_counts.head()}")

weekday_counts = df.groupby('Weekday')['event_type'].count().reindex(range(7), fill_value=0)
weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
print(f"\n按星期分布:\n{weekday_counts}")

weekend_counts = df.groupby('Is_Weekend')['event_type'].count()
print(f"\n工作日vs周末:\n{weekend_counts}")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

axes[0, 0].bar(hourly_counts.index, hourly_counts.values, color='#3498db', alpha=0.8)
axes[0, 0].set_title('按小时分布', fontsize=12, fontweight='bold')
axes[0, 0].set_xlabel('小时')
axes[0, 0].set_ylabel('事件数量')
axes[0, 0].set_xticks(range(0, 24))

axes[0, 1].bar(range(7), weekday_counts.values, color='#2ecc71', alpha=0.8)
axes[0, 1].set_title('按星期分布', fontsize=12, fontweight='bold')
axes[0, 1].set_xlabel('星期')
axes[0, 1].set_ylabel('事件数量')
axes[0, 1].set_xticks(range(7))
axes[0, 1].set_xticklabels(weekday_names)

axes[1, 0].bar(['工作日', '周末'],
               [int(weekend_counts.get(False, 0)), int(weekend_counts.get(True, 0))],
               color=['#9b59b6', '#e74c3c'], alpha=0.8)
axes[1, 0].set_title('工作日vs周末', fontsize=12, fontweight='bold')
axes[1, 0].set_ylabel('事件数量')

for event_type in ['view', 'cart', 'purchase']:
    hourly_by_type = df[df['event_type'] == event_type].groupby('Hour').size()
    axes[1, 1].plot(hourly_by_type.index, hourly_by_type.values, marker='o', label=event_type)
axes[1, 1].set_title('按小时+行为类型分布', fontsize=12, fontweight='bold')
axes[1, 1].set_xlabel('小时')
axes[1, 1].set_ylabel('事件数量')
axes[1, 1].legend()
axes[1, 1].set_xticks(range(0, 24))

plt.tight_layout()
plt.savefig('result/figures/time_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print("\n[OK] time_distribution.png saved")

# ==================== 4. 品类热度分析 ====================
print("\n" + "=" * 50)
print("4. 品类热度分析")
print("=" * 50)

df_with_category = df[df['category_code'].notna() & (df['category_code'] != '')]

view_by_category = df_with_category[df_with_category['event_type'] == 'view']['category_code'].value_counts().head(15)
print(f"\n浏览量Top15品类:\n{view_by_category}")

purchase_by_category = df_with_category[df_with_category['event_type'] == 'purchase']['category_code'].value_counts().head(15)
print(f"\n购买量Top15品类:\n{purchase_by_category}")

purchase_df = df_with_category[df_with_category['event_type'] == 'purchase']
revenue_by_category = purchase_df.groupby('category_code')['price'].sum().sort_values(ascending=False).head(15)
print(f"\n购买金额Top15品类:\n{revenue_by_category}")

fig, axes = plt.subplots(2, 2, figsize=(16, 12))

view_by_category.plot(kind='barh', ax=axes[0, 0], color='#3498db', alpha=0.8)
axes[0, 0].set_title('浏览量Top15品类', fontsize=12, fontweight='bold')
axes[0, 0].set_xlabel('浏览量')
axes[0, 0].invert_yaxis()

purchase_by_category.plot(kind='barh', ax=axes[0, 1], color='#e74c3c', alpha=0.8)
axes[0, 1].set_title('购买量Top15品类', fontsize=12, fontweight='bold')
axes[0, 1].set_xlabel('购买量')
axes[0, 1].invert_yaxis()

revenue_by_category.plot(kind='barh', ax=axes[1, 0], color='#f39c12', alpha=0.8)
axes[1, 0].set_title('购买金额Top15品类', fontsize=12, fontweight='bold')
axes[1, 0].set_xlabel('购买金额')
axes[1, 0].invert_yaxis()

category_funnel = df_with_category[df_with_category['event_type'].isin(['view', 'cart', 'purchase'])].groupby('category_code')['event_type'].value_counts().unstack(fill_value=0)
if 'view' in category_funnel.columns and 'purchase' in category_funnel.columns:
    category_funnel['conversion_rate'] = (category_funnel['purchase'] / category_funnel['view'].replace(0, np.nan) * 100).round(2)
    top_categories = category_funnel.nlargest(15, 'view')
    top_categories['conversion_rate'].dropna().plot(kind='barh', ax=axes[1, 1], color='#2ecc71', alpha=0.8)
    axes[1, 1].set_title('Top15品类转化率', fontsize=12, fontweight='bold')
    axes[1, 1].set_xlabel('转化率 (%)')
    axes[1, 1].invert_yaxis()

plt.tight_layout()
plt.savefig('result/figures/category_ranking.png', dpi=150, bbox_inches='tight')
plt.close()
print("\n[OK] category_ranking.png saved")

# ==================== 5. 价格区间分析 ====================
print("\n" + "=" * 50)
print("5. 价格区间分析")
print("=" * 50)

price_bins = [0, 50, 100, 200, 500, 1000, float('inf')]
price_labels = ['0-50', '50-100', '100-200', '200-500', '500-1000', '1000+']
df_price = df[['price', 'event_type']].copy()
df_price['price_range'] = pd.cut(df_price['price'], bins=price_bins, labels=price_labels, right=False)

price_range_counts = df_price.groupby('price_range', observed=False)['event_type'].count()
print(f"\n各价格区间事件数量:\n{price_range_counts}")

price_funnel = df_price.groupby('price_range', observed=False)['event_type'].value_counts().unstack(fill_value=0)
if 'view' in price_funnel.columns and 'purchase' in price_funnel.columns:
    price_funnel['conversion_rate'] = (price_funnel['purchase'] / price_funnel['view'].replace(0, np.nan) * 100).round(2)
    print(f"\n各价格区间转化率:\n{price_funnel[['view', 'purchase', 'conversion_rate']]}")

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

price_range_counts.plot(kind='bar', ax=axes[0], color='#3498db', alpha=0.8)
axes[0].set_title('各价格区间事件数量', fontsize=12, fontweight='bold')
axes[0].set_xlabel('价格区间')
axes[0].set_ylabel('事件数量')
axes[0].tick_params(axis='x', rotation=45)

if 'conversion_rate' in price_funnel.columns:
    cr = price_funnel['conversion_rate'].dropna()
    cr.plot(kind='bar', ax=axes[1], color='#e74c3c', alpha=0.8)
    axes[1].set_title('各价格区间转化率（排除无数据区间）', fontsize=12, fontweight='bold')
    axes[1].set_xlabel('价格区间')
    axes[1].set_ylabel('转化率 (%)')
    axes[1].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig('result/figures/price_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print("\n[OK] price_analysis.png saved")

# ==================== 6. 用户级统计分析 ====================
print("\n" + "=" * 50)
print("6. 用户级统计分析")
print("=" * 50)

# 按用户聚合
user_stats = df.groupby('user_id').agg(
    total_events=('event_type', 'count'),
    view_count=('event_type', lambda x: (x == 'view').sum()),
    cart_count=('event_type', lambda x: (x == 'cart').sum()),
    purchase_count=('event_type', lambda x: (x == 'purchase').sum()),
    sessions=('user_session', 'nunique'),
    categories=('category_code', 'nunique'),
).reset_index()

# 计算用户级购买金额
purchase_events = df[df['event_type'] == 'purchase']
user_spend = purchase_events.groupby('user_id')['price'].sum().reset_index()
user_spend.columns = ['user_id', 'total_spend']
user_stats = user_stats.merge(user_spend, on='user_id', how='left')
user_stats['total_spend'] = user_stats['total_spend'].fillna(0)

# 用户级指标
total_users = len(user_stats)
purchasing_users = (user_stats['purchase_count'] > 0).sum()
purchasing_user_rate = round(purchasing_users / total_users * 100, 2)
avg_views_per_user = user_stats['view_count'].mean()
avg_carts_per_user = user_stats['cart_count'].mean()
avg_purchases_per_user = user_stats['purchase_count'].mean()
avg_spend_per_user = user_stats['total_spend'].mean()
avg_sessions_per_user = user_stats['sessions'].mean()

print(f"""
用户级统计：
- 总用户数：{total_users:,}
- 有购买行为的用户：{purchasing_users:,}（{purchasing_user_rate}%）
- 人均浏览次数：{avg_views_per_user:.2f}
- 人均加购次数：{avg_carts_per_user:.2f}
- 人均购买次数：{avg_purchases_per_user:.2f}
- 人均消费金额：{avg_spend_per_user:.2f}
- 人均会话数：{avg_sessions_per_user:.2f}
""")

# 用户购买次数分布
purchase_dist = user_stats['purchase_count'].value_counts().sort_index()
print(f"用户购买次数分布:\n{purchase_dist.head(10)}")

# 绘制用户级统计图
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# 左图：用户级漏斗
user_funnel_data = {
    '阶段': ['全部用户', '有浏览', '有加购', '有购买'],
    '用户数': [
        total_users,
        (user_stats['view_count'] > 0).sum(),
        (user_stats['cart_count'] > 0).sum(),
        purchasing_users
    ]
}
bars = axes[0].bar(user_funnel_data['阶段'], user_funnel_data['用户数'],
                   color=['#3498db', '#2ecc71', '#f39c12', '#e74c3c'], alpha=0.8)
axes[0].set_title('用户级漏斗', fontsize=12, fontweight='bold')
axes[0].set_ylabel('用户数')
for bar, count in zip(bars, user_funnel_data['用户数']):
    axes[0].text(bar.get_x() + bar.get_width()/2., bar.get_height() + total_users*0.01,
                f'{count:,}', ha='center', va='bottom', fontsize=9)

# 中图：人均行为次数
avg_metrics = ['人均浏览', '人均加购', '人均购买']
avg_values = [avg_views_per_user, avg_carts_per_user, avg_purchases_per_user]
bars = axes[1].bar(avg_metrics, avg_values, color=['#3498db', '#f39c12', '#e74c3c'], alpha=0.8)
axes[1].set_title('人均行为次数', fontsize=12, fontweight='bold')
axes[1].set_ylabel('次数')
for bar, val in zip(bars, avg_values):
    axes[1].text(bar.get_x() + bar.get_width()/2., bar.get_height() + max(avg_values)*0.01,
                f'{val:.2f}', ha='center', va='bottom', fontsize=10)

# 右图：购买次数分布（限制0-10次，其余归为"10+"）
purchase_dist_clipped = user_stats['purchase_count'].clip(upper=10)
purchase_hist = purchase_dist_clipped.value_counts().sort_index()
labels = [str(int(x)) if x < 10 else '10+' for x in purchase_hist.index]
axes[2].bar(labels, purchase_hist.values, color='#9b59b6', alpha=0.8)
axes[2].set_title('用户购买次数分布', fontsize=12, fontweight='bold')
axes[2].set_xlabel('购买次数')
axes[2].set_ylabel('用户数')

plt.tight_layout()
plt.savefig('result/figures/user_statistics.png', dpi=150, bbox_inches='tight')
plt.close()
print("[OK] user_statistics.png saved")

# ==================== 7. 商品级热度排行 ====================
print("\n" + "=" * 50)
print("7. 商品级热度排行")
print("=" * 50)

# 按 product_id 统计浏览量、购买量、购买金额
product_views = df[df['event_type'] == 'view'].groupby('product_id').size().rename('view_count')
product_purchases = df[df['event_type'] == 'purchase'].groupby('product_id').size().rename('purchase_count')
product_revenue = df[df['event_type'] == 'purchase'].groupby('product_id')['price'].sum().rename('revenue')

# 获取商品的品类和品牌信息
product_info = df.drop_duplicates('product_id')[['product_id', 'category_code', 'brand', 'price']]

# 合并
hot_products = product_info.set_index('product_id')
hot_products = hot_products.join(product_views, how='left')
hot_products = hot_products.join(product_purchases, how='left')
hot_products = hot_products.join(product_revenue, how='left')
hot_products = hot_products.fillna(0)
hot_products['view_count'] = hot_products['view_count'].astype(int)
hot_products['purchase_count'] = hot_products['purchase_count'].astype(int)

# 计算转化率
hot_products['conversion_rate'] = round(
    hot_products['purchase_count'] / hot_products['view_count'].replace(0, np.nan) * 100, 2
)

# 按浏览量排序
hot_products = hot_products.sort_values('view_count', ascending=False)

os.makedirs('result/models', exist_ok=True)
hot_products_path = 'result/models/hot_products.csv'
hot_products.to_csv(hot_products_path)
print(f"[OK] 商品热度排行已保存: {hot_products_path}")
print(f"  - 商品总数: {len(hot_products):,}")
print(f"  - Top 5 浏览量商品:")
for pid, row in hot_products.head(5).iterrows():
    print(f"    {pid} ({row['category_code']}, {row['brand']}): 浏览 {row['view_count']:,}, 购买 {row['purchase_count']:,}, 金额 {row['revenue']:,.2f}")

# ==================== 8. 汇总统计 ====================
print("\n" + "=" * 50)
print("8. 汇总统计")
print("=" * 50)

print(f"""
【用户行为特征分析汇总】

1. 数据概况：
   - 总事件数：{len(df):,}
   - 用户数：{total_users:,}
   - 会话数：{df['user_session'].nunique():,}
   - 品类数：{df_with_category['category_code'].nunique():,}

2. 行为漏斗（事件级）：
   - 浏览(View)：{view_count:,} (100%)
   - 加购(Cart)：{cart_count:,} ({cart_rate}%)
   - 购买(Purchase)：{purchase_count:,} ({purchase_rate}%)

3. 用户级统计：
   - 有购买行为用户：{purchasing_users:,}（{purchasing_user_rate}%）
   - 人均浏览：{avg_views_per_user:.2f} 次
   - 人均加购：{avg_carts_per_user:.2f} 次
   - 人均购买：{avg_purchases_per_user:.2f} 次
   - 人均消费：{avg_spend_per_user:.2f}
   - 人均会话：{avg_sessions_per_user:.2f} 个

4. 时间特征：
   - 高峰时段：{hourly_counts.idxmax()}时（{hourly_counts.max():,}次）
   - 低谷时段：{hourly_counts.idxmin()}时（{hourly_counts.min():,}次）

5. 品类热度：
   - 浏览量最高：{view_by_category.index[0]}（{view_by_category.values[0]:,}次）
   - 购买量最高：{purchase_by_category.index[0]}（{purchase_by_category.values[0]:,}次）
   - 购买金额最高：{revenue_by_category.index[0]}（{revenue_by_category.values[0]:,.2f}）
""")

print("\n" + "=" * 50)
print("子任务 2.1 完成！")
print("=" * 50)
