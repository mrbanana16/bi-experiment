import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# 读取数据（如果已在前面读取过，可复用 df）
# 但为了独立运行，重新读取
df = pd.read_csv('../result/models/hot_products.csv')

# 提取大类
df['main_category'] = df['category_code'].str.split('.').str[0]

# 按大类分组，聚合总浏览量和总购买量
category_stats = df.groupby('main_category').agg({
    'view_count': 'sum',
    'purchase_count': 'sum'
}).reset_index()

# 计算总购买量占比（可选）
category_stats['purchase_rate'] = category_stats['purchase_count'] / category_stats['view_count'] * 100

# 按总浏览量排序
category_stats = category_stats.sort_values('view_count', ascending=False)

print("各大类统计信息：")
print(category_stats)
print("\n" + "=" * 60)


# ==================== 合并双柱状图 ====================
fig, axes = plt.subplots(1, 2, figsize=(18, 7))

width = 0.35

# 左图：所有大类
ax1 = axes[0]
x1 = np.arange(len(category_stats))
bars1_view = ax1.bar(x1 - width/2, category_stats['view_count'], width,
                     label='总浏览量', color='steelblue', edgecolor='black')
bars1_purc = ax1.bar(x1 + width/2, category_stats['purchase_count'], width,
                      label='总购买量', color='coral', edgecolor='black')
ax1.set_xlabel('商品大类', fontsize=12, fontweight=400)
ax1.set_ylabel('数量', fontsize=12, fontweight=400)
ax1.set_title('各大类商品浏览量与购买量对比', fontsize=14, fontweight=400)
ax1.set_xticks(x1)
ax1.set_xticklabels(category_stats['main_category'], rotation=45, ha='right')
ax1.legend()

# 右图：排除 electronics
other_categories = category_stats[category_stats['main_category'] != 'electronics']
ax2 = axes[1]
x2 = np.arange(len(other_categories))
bars2_view = ax2.bar(x2 - width/2, other_categories['view_count'], width,
                     label='总浏览量', color='steelblue', edgecolor='black')
bars2_purc = ax2.bar(x2 + width/2, other_categories['purchase_count'], width,
                      label='总购买量', color='coral', edgecolor='black')
ax2.set_xlabel('商品大类', fontsize=12, fontweight=400)
ax2.set_ylabel('数量', fontsize=12, fontweight=400)
ax2.set_title('各大类商品浏览量与购买量对比（除 Electronics 外）', fontsize=14, fontweight=400)
ax2.set_xticks(x2)
ax2.set_xticklabels(other_categories['main_category'], rotation=45, ha='right')
ax2.legend()

# ---------- 添加数值标签 ----------
# 偏移量设为纵轴最大值的2%，避免标签重叠
offset1 = max(category_stats['view_count']) * 0.02
offset2 = max(other_categories['view_count']) * 0.02 if not other_categories.empty else 0

# 左图标签
for bar, val in zip(bars1_view, category_stats['view_count']):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + offset1,
             f'{int(val)}', ha='center', va='bottom', fontsize=8, color='navy')
for bar, val in zip(bars1_purc, category_stats['purchase_count']):
    if val > 0:
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + offset1,
                 f'{int(val)}', ha='center', va='bottom', fontsize=8, color='darkred')

# 右图标签
for bar, val in zip(bars2_view, other_categories['view_count']):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + offset2,
             f'{int(val)}', ha='center', va='bottom', fontsize=8, color='navy')
for bar, val in zip(bars2_purc, other_categories['purchase_count']):
    if val > 0:
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + offset2,
                 f'{int(val)}', ha='center', va='bottom', fontsize=8, color='darkred')

plt.tight_layout()
plt.savefig('../result/figures/hot_products_dual_bar_combined.png', dpi=150, bbox_inches='tight')

# ==================== 2D热力图 ====================
# 提取大类和小类
df['main_category'] = df['category_code'].str.split('.').str[0]
df['sub_category'] = df['category_code'].str.split('.').str[1]

# 按大类和小类分组，统计总浏览量
category_sub_view = df.groupby(['main_category', 'sub_category'])['view_count'].sum().reset_index()

# 过滤掉小类为空的记录
category_sub_view = category_sub_view[category_sub_view['sub_category'].notna()]

print("\n" + "="*60)
print("热力图数据统计：")
print(f"共有 {len(category_sub_view)} 个大类-小类组合")

# 创建透视表
pivot_table = category_sub_view.pivot_table(
    index='main_category',
    columns='sub_category',
    values='view_count',
    fill_value=0
)

print(f"透视表形状: {pivot_table.shape}")
print(f"大类数量: {len(pivot_table.index)}")
print(f"二级类型数量: {len(pivot_table.columns)}")

# 筛选：保留浏览量较高的数据，避免图表过于拥挤
total_view = pivot_table.sum().sum()
row_sum = pivot_table.sum(axis=1)
col_sum = pivot_table.sum(axis=0)

# 筛选大类：保留总浏览量 > 总浏览量1%的大类
main_filter = row_sum[row_sum > total_view * 0.01].index
# 筛选二级类型：保留总浏览量 > 总浏览量0.5%的二级类型
sub_filter = col_sum[col_sum > total_view * 0.005].index

pivot_filtered = pivot_table.loc[main_filter, sub_filter]

print(f"\n筛选后:")
print(f"  - 筛选条件: 大类浏览量 > {total_view * 0.01:.0f}, 二级类型浏览量 > {total_view * 0.005:.0f}")
print(f"  - 大类数量: {len(pivot_filtered.index)}")
print(f"  - 二级类型数量: {len(pivot_filtered.columns)}")

# 绘制热力图
fig_heatmap, ax_heatmap = plt.subplots(figsize=(18, 10))

# 使用颜色映射，对数尺度可以更好展示差异
im = ax_heatmap.imshow(pivot_filtered.values, cmap='YlOrRd', aspect='auto', norm='log')

# 设置坐标轴
ax_heatmap.set_xticks(range(len(pivot_filtered.columns)))
ax_heatmap.set_xticklabels(pivot_filtered.columns, rotation=90, fontsize=8)
ax_heatmap.set_yticks(range(len(pivot_filtered.index)))
ax_heatmap.set_yticklabels(pivot_filtered.index, fontsize=10)
ax_heatmap.set_xlabel('二级商品类型', fontsize=12, fontweight=400)
ax_heatmap.set_ylabel('商品大类', fontsize=12, fontweight=400)
ax_heatmap.set_title('各大类-二级类型商品浏览量热力图\n（对数尺度，颜色越深浏览量越高）', fontsize=14, fontweight=400)

# 添加颜色条
cbar = plt.colorbar(im, ax=ax_heatmap)
cbar.set_label('浏览量（对数尺度）', fontsize=10)

# 在每个格子中添加数值（可选，如果格子太多可以注释掉）
# 只显示浏览量大于0的格子
for i in range(len(pivot_filtered.index)):
    for j in range(len(pivot_filtered.columns)):
        val = pivot_filtered.values[i, j]
        if val > 0:
            # 根据数值大小决定文字颜色
            text_color = 'white' if val > pivot_filtered.values.max() * 0.3 else 'black'
            ax_heatmap.text(j, i, f'{int(val):,}',
                           ha='center', va='center',
                           fontsize=6, color=text_color, rotation=45)

plt.tight_layout()
plt.savefig('../result/figures/hot_products_heatmap_full.png', dpi=150, bbox_inches='tight')