import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.font_manager as fm


# ========== 中文字体设置 ==========
# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 12

# ========== 读取数据 ==========
df = pd.read_csv('../result/models/cluster_category_preferences.csv')

# 确保数据按 cluster, behavior, rank 排序
df = df.sort_values(['cluster', 'behavior', 'rank'])

print("数据概览:")
print(df.head())
print("\n唯一簇:", sorted(df['cluster'].unique()))
print("唯一行为:", df['behavior'].unique())
print("唯一品类数:", df['category'].nunique())

# ========== 1. 热力图：每个行为下簇 vs 品类 ==========
# 对每种行为，构建 pivot 表 (cluster × category)，填充 count，缺失补0
behaviors = df['behavior'].unique()
all_categories = df['category'].unique()
all_clusters = sorted(df['cluster'].unique())

for behavior in behaviors:
    # 筛选当前行为
    sub = df[df['behavior'] == behavior]
    # pivot
    pivot = sub.pivot(index='cluster', columns='category', values='count').fillna(0)
    # 确保所有簇和品类都存在（如果某些簇没有该行为，则全部为0）
    pivot = pivot.reindex(index=all_clusters, columns=all_categories, fill_value=0)

    # 绘制热力图
    fig, ax = plt.subplots(figsize=(14, max(6, len(all_clusters) * 0.8)))
    im = ax.imshow(pivot.values, cmap='YlOrRd', aspect='auto', interpolation='nearest')

    # 设置刻度
    ax.set_xticks(np.arange(len(all_categories)))
    ax.set_yticks(np.arange(len(all_clusters)))
    ax.set_xticklabels(all_categories, rotation=90, ha='center')
    ax.set_yticklabels(all_clusters)

    # 添加数值标注（如果数值不太多）
    for i in range(len(all_clusters)):
        for j in range(len(all_categories)):
            val = pivot.iloc[i, j]
            if val > 0:
                ax.text(j, i, f'{int(val)}', ha='center', va='center',
                        color='black' if val < pivot.max().max() * 0.5 else 'white', fontsize=8)

    ax.set_title(f'行为 "{behavior}" — 各簇在各品类的计数热力图')
    ax.set_xlabel('品类')
    ax.set_ylabel('簇')
    plt.colorbar(im, ax=ax, label='计数')
    plt.tight_layout()
    plt.savefig(f'../result/figures/heatmap_{behavior}.png', dpi=150)
    plt.close()
    print(f"热力图已保存: heatmap_{behavior}.png")

# ========== 2. 每个簇的 top5 品类条形图（分行为） ==========
# 按簇分组，对每个簇绘制三个子图：view, cart, purchase (若存在)
clusters = sorted(df['cluster'].unique())

for cluster in clusters:
    # 提取该簇数据
    sub = df[df['cluster'] == cluster]
    # 按行为分组
    behaviors_present = sub['behavior'].unique()
    n_behaviors = len(behaviors_present)
    if n_behaviors == 0:
        continue

    fig, axes = plt.subplots(1, n_behaviors, figsize=(5 * n_behaviors, 6), squeeze=False)
    axes = axes.flatten()

    for idx, behavior in enumerate(behaviors_present):
        ax = axes[idx]
        data = sub[sub['behavior'] == behavior].sort_values('rank')
        categories = data['category'].values
        counts = data['count'].values
        # 绘制水平条形图
        bars = ax.barh(categories, counts, color='steelblue')
        ax.set_title(f'行为: {behavior}')
        ax.set_xlabel('计数')
        # 在条末端显示数值
        for bar, val in zip(bars, counts):
            ax.text(val + max(counts) * 0.01, bar.get_y() + bar.get_height() / 2,
                    f'{int(val)}', va='center', fontsize=10)
        ax.invert_yaxis()  # rank1在上方
        # 如果该行为没有数据，显示提示
        if len(data) == 0:
            ax.text(0.5, 0.5, '无数据', transform=ax.transAxes, ha='center', va='center')

    # 隐藏多余的子图（如果有）
    for j in range(n_behaviors, len(axes)):
        axes[j].set_visible(False)

    fig.suptitle(f'簇 {cluster} 各行为 top5 品类偏好', fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(f'../result/figures/cluster_{cluster}_top5_bars.png', dpi=150)
    plt.close()
    print(f"簇 {cluster} 条形图已保存: cluster_{cluster}_top5_bars.png")