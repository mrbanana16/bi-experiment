"""
子任务 2.1：用户行为特征分析（描述性统计）
数据集：Datasets/processed/preprocessed.csv
输出：result/figures/ 下的各类图表
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
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

funnel_data = {
    '行为阶段': ['浏览(View)', '加购(Cart)', '购买(Purchase)'],
    '数量': [view_count, cart_count, purchase_count],
    '转化率': [
        100.0,
        round(cart_count / view_count * 100, 2) if view_count > 0 else 0,
        round(purchase_count / view_count * 100, 2) if view_count > 0 else 0
    ]
}
funnel_df = pd.DataFrame(funnel_data)
print(f"\n漏斗分析:\n{funnel_df}")

# 绘制漏斗图
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# 左图：柱状图
colors = ['#3498db', '#f39c12', '#e74c3c']
bars = axes[0].bar(funnel_data['行为阶段'], funnel_data['数量'], color=colors)
axes[0].set_title('用户行为漏斗 - 数量分布', fontsize=14, fontweight='bold')
axes[0].set_ylabel('数量')
for bar, count in zip(bars, funnel_data['数量']):
    axes[0].text(bar.get_x() + bar.get_width()/2., bar.get_height() + 1000,
                f'{count:,}', ha='center', va='bottom', fontsize=11)

# 右图：转化率
bars2 = axes[1].bar(funnel_data['行为阶段'], funnel_data['转化率'], color=colors)
axes[1].set_title('用户行为漏斗 - 转化率', fontsize=14, fontweight='bold')
axes[1].set_ylabel('转化率 (%)')
for bar, rate in zip(bars2, funnel_data['转化率']):
    axes[1].text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.5,
                f'{rate}%', ha='center', va='bottom', fontsize=11)

plt.tight_layout()
plt.savefig('result/figures/funnel_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print("\n[OK] funnel_analysis.png saved")

# ==================== 3. 时间维度分析 ====================
print("\n" + "=" * 50)
print("3. 时间维度分析")
print("=" * 50)

# 转换时间格式
df['event_time'] = pd.to_datetime(df['event_time'])

# 按小时分布
hourly_counts = df.groupby('Hour')['event_type'].count()
print(f"\n按小时分布（前5）:\n{hourly_counts.head()}")

# 按星期分布
weekday_counts = df.groupby('Weekday')['event_type'].count()
weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
print(f"\n按星期分布:\n{weekday_counts}")

# 工作日vs周末
weekend_counts = df.groupby('Is_Weekend')['event_type'].count()
print(f"\n工作日vs周末:\n{weekend_counts}")

# 绘制时间分布图
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 按小时分布
axes[0, 0].bar(hourly_counts.index, hourly_counts.values, color='#3498db', alpha=0.8)
axes[0, 0].set_title('按小时分布', fontsize=12, fontweight='bold')
axes[0, 0].set_xlabel('小时')
axes[0, 0].set_ylabel('事件数量')
axes[0, 0].set_xticks(range(0, 24))

# 按星期分布
axes[0, 1].bar(range(7), weekday_counts.values, color='#2ecc71', alpha=0.8)
axes[0, 1].set_title('按星期分布', fontsize=12, fontweight='bold')
axes[0, 1].set_xlabel('星期')
axes[0, 1].set_ylabel('事件数量')
axes[0, 1].set_xticks(range(7))
axes[0, 1].set_xticklabels(weekday_names)

# 工作日vs周末
axes[1, 0].bar(['工作日', '周末'], weekend_counts.values, color=['#9b59b6', '#e74c3c'], alpha=0.8)
axes[1, 0].set_title('工作日vs周末', fontsize=12, fontweight='bold')
axes[1, 0].set_ylabel('事件数量')

# 按小时+行为类型分布
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

# 过滤掉空值
df_with_category = df[df['category_code'].notna() & (df['category_code'] != '')]

# 各品类浏览量
view_by_category = df_with_category[df_with_category['event_type'] == 'view']['category_code'].value_counts().head(15)
print(f"\n浏览量Top15品类:\n{view_by_category}")

# 各品类购买量
purchase_by_category = df_with_category[df_with_category['event_type'] == 'purchase']['category_code'].value_counts().head(15)
print(f"\n购买量Top15品类:\n{purchase_by_category}")

# 各品类购买金额
purchase_df = df_with_category[df_with_category['event_type'] == 'purchase']
revenue_by_category = purchase_df.groupby('category_code')['price'].sum().sort_values(ascending=False).head(15)
print(f"\n购买金额Top15品类:\n{revenue_by_category}")

# 绘制品类热度图
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# 浏览量Top15
view_by_category.plot(kind='barh', ax=axes[0, 0], color='#3498db', alpha=0.8)
axes[0, 0].set_title('浏览量Top15品类', fontsize=12, fontweight='bold')
axes[0, 0].set_xlabel('浏览量')
axes[0, 0].invert_yaxis()

# 购买量Top15
purchase_by_category.plot(kind='barh', ax=axes[0, 1], color='#e74c3c', alpha=0.8)
axes[0, 1].set_title('购买量Top15品类', fontsize=12, fontweight='bold')
axes[0, 1].set_xlabel('购买量')
axes[0, 1].invert_yaxis()

# 购买金额Top15
revenue_by_category.plot(kind='barh', ax=axes[1, 0], color='#f39c12', alpha=0.8)
axes[1, 0].set_title('购买金额Top15品类', fontsize=12, fontweight='bold')
axes[1, 0].set_xlabel('购买金额')
axes[1, 0].invert_yaxis()

# 品类转化率（购买/浏览）
category_funnel = df_with_category.groupby('category_code')['event_type'].value_counts().unstack(fill_value=0)
if 'view' in category_funnel.columns and 'purchase' in category_funnel.columns:
    category_funnel['conversion_rate'] = (category_funnel['purchase'] / category_funnel['view'] * 100).round(2)
    top_categories = category_funnel.nlargest(15, 'view')
    top_categories['conversion_rate'].plot(kind='barh', ax=axes[1, 1], color='#2ecc71', alpha=0.8)
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

# 创建价格区间
price_bins = [0, 50, 100, 200, 500, 1000, 5000, float('inf')]
price_labels = ['0-50', '50-100', '100-200', '200-500', '500-1000', '1000-5000', '5000+']
df['price_range'] = pd.cut(df['price'], bins=price_bins, labels=price_labels, right=False)

# 各价格区间的事件数量
price_range_counts = df.groupby('price_range')['event_type'].count()
print(f"\n各价格区间事件数量:\n{price_range_counts}")

# 各价格区间的转化率
price_funnel = df.groupby('price_range')['event_type'].value_counts().unstack(fill_value=0)
if 'view' in price_funnel.columns and 'purchase' in price_funnel.columns:
    price_funnel['conversion_rate'] = (price_funnel['purchase'] / price_funnel['view'] * 100).round(2)
    print(f"\n各价格区间转化率:\n{price_funnel[['view', 'purchase', 'conversion_rate']]}")

# 绘制价格区间分析图
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# 左图：各价格区间事件数量
price_range_counts.plot(kind='bar', ax=axes[0], color='#3498db', alpha=0.8)
axes[0].set_title('各价格区间事件数量', fontsize=12, fontweight='bold')
axes[0].set_xlabel('价格区间')
axes[0].set_ylabel('事件数量')
axes[0].tick_params(axis='x', rotation=45)

# 右图：各价格区间转化率
if 'conversion_rate' in price_funnel.columns:
    price_funnel['conversion_rate'].plot(kind='bar', ax=axes[1], color='#e74c3c', alpha=0.8)
    axes[1].set_title('各价格区间转化率', fontsize=12, fontweight='bold')
    axes[1].set_xlabel('价格区间')
    axes[1].set_ylabel('转化率 (%)')
    axes[1].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig('result/figures/price_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print("\n[OK] price_analysis.png saved")

# ==================== 6. 汇总统计 ====================
print("\n" + "=" * 50)
print("6. 汇总统计")
print("=" * 50)

print(f"""
【用户行为特征分析汇总】

1. 数据概况：
   - 总事件数：{len(df):,}
   - 用户数：{df['user_id'].nunique():,}
   - 会话数：{df['user_session'].nunique():,}
   - 品类数：{df_with_category['category_code'].nunique():,}

2. 行为漏斗：
   - 浏览(View)：{view_count:,} ({100}%)
   - 加购(Cart)：{cart_count:,} ({round(cart_count/view_count*100, 2)}%)
   - 购买(Purchase)：{purchase_count:,} ({round(purchase_count/view_count*100, 2)}%)

3. 时间特征：
   - 高峰时段：{hourly_counts.idxmax()}时（{hourly_counts.max():,}次）
   - 低谷时段：{hourly_counts.idxmin()}时（{hourly_counts.min():,}次）

4. 品类热度：
   - 浏览量最高：{view_by_category.index[0]}（{view_by_category.values[0]:,}次）
   - 购买量最高：{purchase_by_category.index[0]}（{purchase_by_category.values[0]:,}次）
   - 购买金额最高：{revenue_by_category.index[0]}（{revenue_by_category.values[0]:,.2f}）
""")

print("\n" + "=" * 50)
print("子任务 2.1 完成！")
print("=" * 50)
