"""
子任务 2.2：用户分群分析（K-Means聚类 + 规则分层）
数据集：Datasets/processed/session_based_features.csv
输出：result/figures/ 下的聚类图表，result/models/ 下的聚类模型

改动说明：
- 原逻辑仅对 event_count>1 的会话聚类，丢失 94.8% 的购买用户
- 新逻辑：单事件会话用规则分群，多事件会话用 K-Means 聚类，合并后统一输出
- 输出格式向后兼容：cluster_profiles.csv / cluster_profiles_business.csv 列名不变
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
import pickle
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体（Windows）
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 创建输出目录
os.makedirs('result/figures', exist_ok=True)
os.makedirs('result/models', exist_ok=True)

# ==================== 1. 读取数据 ====================
print("=" * 50)
print("1. 读取数据")
print("=" * 50)

df = pd.read_csv("Datasets/processed/session_based_features.csv")
print(f"数据形状: {df.shape}")
print(f"列名: {df.columns.tolist()}")
print(f"\n数据类型:\n{df.dtypes}")
print(f"\n缺失值统计:\n{df.isnull().sum()}")

# ==================== 1.5 异常值过滤 ====================
print("\n" + "=" * 50)
print("1.5 异常值过滤")
print("=" * 50)

original_count = len(df)

# 过滤 session_duration_min 异常值（>1440分钟 = 24小时，会话不可能超过一天）
outlier_mask = df['session_duration_min'] > 1440
outlier_count = outlier_mask.sum()
if outlier_count > 0:
    print(f"发现 {outlier_count} 个会话时长异常（>24小时），将被过滤：")
    print(df.loc[outlier_mask, ['user_session', 'session_duration_min', 'event_count']].to_string())
    df = df[~outlier_mask].reset_index(drop=True)
    print(f"\n过滤后数据形状: {df.shape}（减少 {original_count - len(df)} 条）")
else:
    print("未发现会话时长异常值")

# ==================== 2. 分离单事件 / 多事件会话 ====================
print("\n" + "=" * 50)
print("2. 分离单事件 / 多事件会话")
print("=" * 50)

df_single = df[df['event_count'] == 1].copy()
df_multi = df[df['event_count'] > 1].copy()

print(f"单事件会话: {len(df_single):,}（{len(df_single)/len(df)*100:.1f}%）")
print(f"多事件会话: {len(df_multi):,}（{len(df_multi)/len(df)*100:.1f}%）")
print(f"\n单事件会话中：")
print(f"  有购买行为: {df_single['has_purchase'].sum():,}")
print(f"  有加购行为: {(df_single['cart_count'] > 0).sum():,}")
print(f"  仅浏览: {((df_single['has_purchase'] == False) & (df_single['cart_count'] == 0)).sum():,}")

# ==================== 3. 单事件会话：规则分群 ====================
print("\n" + "=" * 50)
print("3. 单事件会话：规则分群")
print("=" * 50)

# 规则分群
# 0 = 仅浏览型（无购买、无加购）
# 1 = 加购未转化型（有加购、无购买）
# 2 = 直接购买型（有购买）
df_single['cluster'] = 0  # 默认：浏览型
df_single.loc[(df_single['has_purchase'] == 0) & (df_single['cart_count'] > 0), 'cluster'] = 1
df_single.loc[df_single['has_purchase'] == 1, 'cluster'] = 2

single_dist = df_single['cluster'].value_counts().sort_index()
single_labels = {0: '仅浏览型', 1: '加购未转化型', 2: '直接购买型'}
print("单事件会话分群结果：")
for cid, count in single_dist.items():
    pct = count / len(df_single) * 100
    print(f"  Cluster {cid}（{single_labels[cid]}）: {count:,} 个会话（{pct:.1f}%）")

# ==================== 4. 多事件会话：K-Means 聚类（保留原逻辑） ====================
print("\n" + "=" * 50)
print("4. 多事件会话：K-Means 聚类")
print("=" * 50)

# 特征工程（与原逻辑完全一致）
df_multi['has_duration'] = (df_multi['session_duration_min'] > 0).astype(int)
df_multi['has_purchase'] = df_multi['has_purchase'].astype(int)
df_multi['log_purchase_amount'] = np.log1p(df_multi['purchase_amount'])

feature_cols = ['event_count', 'cart_count', 'purchase_count',
                'log_purchase_amount', 'has_purchase', 'has_duration']

business_display_cols = ['event_count', 'unique_products', 'cart_count', 'purchase_count',
                         'session_duration_min', 'purchase_amount', 'unique_categories']

X = df_multi[feature_cols].copy()
X = X.fillna(0)
X = X.replace([np.inf, -np.inf], 0)

print(f"训练特征: {feature_cols}")
print(f"特征矩阵形状: {X.shape}")

# 标准化
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 确定最优K值
K_range = range(2, 6)
inertias = []
sil_scores = []
for k in K_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X_scaled)
    inertias.append(kmeans.inertia_)
    sil_scores.append(silhouette_score(X_scaled, labels))
    min_size = pd.Series(labels).value_counts().min()
    print(f"K={k}: Inertia={kmeans.inertia_:.2f}, Silhouette={sil_scores[-1]:.4f}, 最小聚类={min_size}")

best_k = list(K_range)[np.argmax(sil_scores)]
sil_pre_merge = max(sil_scores)
print(f"\n最优K值: {best_k}")

# 绘制肘部法则和轮廓系数图
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].plot(K_range, inertias, 'bo-')
axes[0].set_title('Elbow Method', fontsize=12, fontweight='bold')
axes[0].set_xlabel('Number of Clusters (K)')
axes[0].set_ylabel('Inertia')
axes[0].axvline(x=best_k, color='r', linestyle='--', label=f'Best K={best_k}')
axes[0].legend()
axes[0].set_xticks(list(K_range))

axes[1].plot(K_range, sil_scores, 'ro-')
axes[1].set_title('Silhouette Score', fontsize=12, fontweight='bold')
axes[1].set_xlabel('Number of Clusters (K)')
axes[1].set_ylabel('Silhouette Score')
axes[1].axvline(x=best_k, color='b', linestyle='--', label=f'Best K={best_k}')
axes[1].legend()
axes[1].set_xticks(list(K_range))

plt.tight_layout()
plt.savefig('result/figures/elbow_silhouette.png', dpi=150, bbox_inches='tight')
plt.close()
print("[OK] elbow_silhouette.png saved")

# 执行K-Means聚类
kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
df_multi['cluster'] = kmeans.fit_predict(X_scaled)

print(f"\n聚类结果分布:\n{df_multi['cluster'].value_counts().sort_index()}")

# 小聚类合并
MIN_CLUSTER_SIZE = 10
cluster_merge_map = {}
cluster_merge_map_original = {}
renumber_map = {}

cluster_sizes = df_multi['cluster'].value_counts().sort_index()
small_clusters = cluster_sizes[cluster_sizes < MIN_CLUSTER_SIZE].index.tolist()

if small_clusters:
    cluster_centers = {}
    for c in range(best_k):
        mask = df_multi['cluster'] == c
        cluster_centers[c] = X_scaled[mask].mean(axis=0)

    for small_c in small_clusters:
        small_center = cluster_centers[small_c]
        best_target = None
        best_dist = float('inf')
        for c in range(best_k):
            if c == small_c or c in small_clusters:
                continue
            dist = np.linalg.norm(small_center - cluster_centers[c])
            if dist < best_dist:
                best_dist = dist
                best_target = c
        if best_target is not None:
            cluster_merge_map[int(small_c)] = int(best_target)

    cluster_merge_map_original = dict(cluster_merge_map)

    for old_c, new_c in cluster_merge_map.items():
        df_multi.loc[df_multi['cluster'] == old_c, 'cluster'] = new_c

    # 重新编号（从0开始）
    unique_clusters = sorted(df_multi['cluster'].unique())
    renumber_map = {old: new for new, old in enumerate(unique_clusters)}
    df_multi['cluster'] = df_multi['cluster'].map(renumber_map)
    cluster_merge_map = {k: renumber_map[v] for k, v in cluster_merge_map_original.items()}

    print(f"合并了 {len(small_clusters)} 个小聚类: {small_clusters}")
    print(f"合并映射: {cluster_merge_map}")
else:
    print("无小聚类需要合并")

multi_n_clusters = df_multi['cluster'].nunique()
print(f"多事件会话聚类数: {multi_n_clusters}")

sil_post_merge = silhouette_score(X_scaled, df_multi['cluster'].values) if multi_n_clusters >= 2 else float('nan')
print(f"轮廓系数（合并前）: {sil_pre_merge:.4f}")
print(f"轮廓系数（合并后）: {sil_post_merge:.4f}")

# ==================== 5. 合并：将多事件聚类 ID 偏移 ====================
print("\n" + "=" * 50)
print("5. 合并单事件规则分群 + 多事件 K-Means 聚类")
print("=" * 50)

# 单事件分群占用 cluster 0/1/2，多事件聚类从 3 开始
n_single_clusters = 3  # 仅浏览型(0)、加购未转化型(1)、直接购买型(2)
df_multi['cluster'] = df_multi['cluster'] + n_single_clusters

# 统一 has_purchase 类型（df_single 为 bool，df_multi 已转为 int）
df_single['has_purchase'] = df_single['has_purchase'].astype(int)

# 合并
df_all = pd.concat([df_single[df.columns.tolist() + ['cluster']],
                     df_multi[df.columns.tolist() + ['cluster']]],
                    ignore_index=True)

# 确保 cluster 列为 int
df_all['cluster'] = df_all['cluster'].astype(int)

total_clusters = n_single_clusters + multi_n_clusters
print(f"合并后总聚类数: {total_clusters}")
print(f"\n全量用户聚类分布:")
for cid in range(total_clusters):
    count = (df_all['cluster'] == cid).sum()
    pct = count / len(df_all) * 100
    if cid < n_single_clusters:
        label = single_labels[cid]
    else:
        label = f"K-Means Cluster {cid - n_single_clusters}"
    print(f"  Cluster {cid}（{label}）: {count:,} 个会话（{pct:.1f}%）")

# ==================== 6. 保存聚类模型 ====================
print("\n" + "=" * 50)
print("6. 保存聚类模型")
print("=" * 50)

model_path = 'result/models/kmeans_model.pkl'
with open(model_path, 'wb') as f:
    pickle.dump({
        'model': kmeans,
        'scaler': scaler,
        'feature_cols': feature_cols,
        'final_labels': df_all['cluster'].values,
        'renumber_map': renumber_map if cluster_merge_map_original else {},
        'metadata': {
            'n_clusters': total_clusters,
            'n_single_clusters': n_single_clusters,
            'n_multi_clusters': multi_n_clusters,
            'silhouette_score_pre_merge': sil_pre_merge,
            'silhouette_score_post_merge': sil_post_merge,
            'training_samples_multi': len(df_multi),
            'training_samples_all': len(df_all),
            'training_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'removed_features': ['unique_products', 'session_duration_min'],
            'engineered_features': ['log_purchase_amount', 'has_purchase', 'has_duration'],
            'filter_note': '已过滤时长异常会话（>24h）；单事件会话用规则分群',
            'cluster_merge_map': cluster_merge_map_original,
            'min_cluster_size': MIN_CLUSTER_SIZE,
            'single_cluster_labels': single_labels,
        }
    }, f)
print(f"[OK] K-Means model saved: {model_path}")

# ==================== 7. 聚类结果分析 ====================
print("\n" + "=" * 50)
print("7. 聚类结果分析")
print("=" * 50)

# 训练特征画像（全量用户）
# 注意：df_all 通过 df.columns.tolist() 拼接，不含衍生特征列，需在此创建
df_all['has_duration'] = (df_all['session_duration_min'] > 0).astype(int)
df_all['has_purchase'] = df_all['has_purchase'].astype(int)
df_all['log_purchase_amount'] = np.log1p(df_all['purchase_amount'])

cluster_profiles_training = df_all.groupby('cluster')[feature_cols].mean()
print(f"\n训练特征画像（聚类中心）:\n{cluster_profiles_training.round(4)}")

cluster_profiles_path = 'result/models/cluster_profiles.csv'
cluster_profiles_training.to_csv(cluster_profiles_path)
print(f"\n[OK] 训练特征画像已保存: {cluster_profiles_path}")

# 业务展示特征画像
cluster_profiles_business = df_all.groupby('cluster')[business_display_cols].mean()
print(f"\n业务展示特征画像:\n{cluster_profiles_business.round(2)}")

cluster_profiles_business_path = 'result/models/cluster_profiles_business.csv'
cluster_profiles_business.to_csv(cluster_profiles_business_path)
print(f"\n[OK] 业务展示特征画像已保存: {cluster_profiles_business_path}")

# 各聚类的购买比例
cluster_funnel = df_all.groupby('cluster').agg({
    'event_count': 'sum',
    'purchase_count': 'sum',
    'purchase_amount': 'sum'
})
cluster_funnel['purchase_ratio'] = (cluster_funnel['purchase_count'] / cluster_funnel['event_count'].replace(0, np.nan) * 100).round(2)
print(f"\n各聚类购买比例:\n{cluster_funnel}")

# ==================== 7.5 各聚类偏好品类分布 ====================
print("\n" + "=" * 50)
print("7.5 各聚类偏好品类分布")
print("=" * 50)

# 读取预处理数据获取品类信息
df_preprocessed = pd.read_csv("Datasets/processed/preprocessed.csv")
df_preprocessed = df_preprocessed[df_preprocessed['category_code'].notna() & (df_preprocessed['category_code'] != '')]

# 将 cluster 标签映射回会话
session_cluster = df_all[['user_session', 'cluster']].copy()
df_with_cluster = df_preprocessed.merge(session_cluster, on='user_session', how='inner')

# 计算各聚类的浏览品类 Top5 和购买品类 Top5
cluster_category_list = []
for cid in range(total_clusters):
    cluster_data = df_with_cluster[df_with_cluster['cluster'] == cid]

    # 浏览品类 Top5
    view_cats = cluster_data[cluster_data['event_type'] == 'view']['category_code'].value_counts().head(5)
    for rank, (cat, count) in enumerate(view_cats.items(), 1):
        cluster_category_list.append({
            'cluster': cid,
            'behavior': 'view',
            'rank': rank,
            'category': cat,
            'count': int(count)
        })

    # 购买品类 Top5
    purchase_cats = cluster_data[cluster_data['event_type'] == 'purchase']['category_code'].value_counts().head(5)
    for rank, (cat, count) in enumerate(purchase_cats.items(), 1):
        cluster_category_list.append({
            'cluster': cid,
            'behavior': 'purchase',
            'rank': rank,
            'category': cat,
            'count': int(count)
        })

cluster_category_df = pd.DataFrame(cluster_category_list)
cluster_category_path = 'result/models/cluster_category_preferences.csv'
cluster_category_df.to_csv(cluster_category_path, index=False)
print(f"[OK] 各聚类偏好品类已保存: {cluster_category_path}")

# 打印各聚类的浏览和购买 Top3
for cid in range(total_clusters):
    if cid < n_single_clusters:
        label = single_labels[cid]
    else:
        label = f"K-Means Cluster {cid - n_single_clusters}"
    print(f"\n  Cluster {cid}（{label}）:")
    top_views = cluster_category_df[(cluster_category_df['cluster'] == cid) & (cluster_category_df['behavior'] == 'view')].head(3)
    if len(top_views) > 0:
        cats_str = ', '.join([f"{r['category']}({r['count']})" for _, r in top_views.iterrows()])
        print(f"    浏览 Top3: {cats_str}")
    top_purchases = cluster_category_df[(cluster_category_df['cluster'] == cid) & (cluster_category_df['behavior'] == 'purchase')].head(3)
    if len(top_purchases) > 0:
        cats_str = ', '.join([f"{r['category']}({r['count']})" for _, r in top_purchases.iterrows()])
        print(f"    购买 Top3: {cats_str}")

# ==================== 8. 可视化 ====================
print("\n" + "=" * 50)
print("8. 可视化")
print("=" * 50)

colors = plt.cm.Set2(np.linspace(0, 1, total_clusters))

# 8.1 雷达图（训练特征，min-max 标准化到 [0,1]）
fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

categories = feature_cols
N = len(categories)
angles = [n / float(N) * 2 * np.pi for n in range(N)]
angles += angles[:1]

profiles_min = cluster_profiles_training.min()
profiles_max = cluster_profiles_training.max()
profiles_range = profiles_max - profiles_min
profiles_range = profiles_range.replace(0, 1)
cluster_profiles_norm = (cluster_profiles_training - profiles_min) / profiles_range

for i in range(total_clusters):
    values = cluster_profiles_norm.loc[i].values.tolist()
    values += values[:1]
    if i < n_single_clusters:
        label = f'C{i}({single_labels[i]})'
    else:
        label = f'C{i}(K-Means {i - n_single_clusters})'
    ax.plot(angles, values, 'o-', linewidth=2, label=label, color=colors[i])
    ax.fill(angles, values, alpha=0.1, color=colors[i])

ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=9)
ax.set_title('Cluster Radar Chart (All Users, Normalized)', fontsize=14, fontweight='bold', pad=20)
ax.set_ylim(0, 1.1)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
plt.tight_layout()
plt.savefig('result/figures/cluster_radar.png', dpi=150, bbox_inches='tight')
plt.close()
print("[OK] cluster_radar.png saved")

# 8.2 PCA降维散点图（仅多事件会话，因为单事件会话特征维度低）
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)

fig, ax = plt.subplots(figsize=(10, 8))
scatter = ax.scatter(X_pca[:, 0], X_pca[:, 1],
                     c=df_multi['cluster'].astype(int),
                     cmap='Set2', alpha=0.6, s=10,
                     vmin=n_single_clusters - 0.5,
                     vmax=total_clusters - 0.5)
ax.set_title('Cluster PCA Scatter Plot (Multi-event Sessions)', fontsize=14, fontweight='bold')
ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]*100:.2f}%)')
ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]*100:.2f}%)')
plt.colorbar(scatter, label='Cluster')
plt.tight_layout()
plt.savefig('result/figures/cluster_pca.png', dpi=150, bbox_inches='tight')
plt.close()
print("[OK] cluster_pca.png saved")

# 8.3 各聚类特征对比柱状图（全量用户，归一化值）
fig, axes = plt.subplots(2, 3, figsize=(15, 8))
axes = axes.flatten()

for i, col in enumerate(feature_cols):
    cluster_means = cluster_profiles_training[col]
    col_min, col_max = cluster_means.min(), cluster_means.max()
    col_range = col_max - col_min if col_max != col_min else 1
    normalized = (cluster_means - col_min) / col_range
    bar_colors = [colors[int(c)] for c in normalized.index]
    axes[i].bar(normalized.index, normalized.values, color=bar_colors)
    axes[i].set_title(col, fontsize=10, fontweight='bold')
    axes[i].set_xlabel('Cluster')
    axes[i].set_ylabel('Normalized (0-1)')
    axes[i].set_ylim(0, 1.1)
    for x, (nv, rv) in enumerate(zip(normalized.values, cluster_means.values)):
        axes[i].text(x, nv + 0.03, f'{rv:.2f}', ha='center', va='bottom', fontsize=7)

plt.tight_layout()
plt.savefig('result/figures/cluster_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("[OK] cluster_comparison.png saved")

# ==================== 9. 聚类结论 ====================
print("\n" + "=" * 50)
print("9. 聚类结论")
print("=" * 50)

print(f"""
【用户分群分析汇总】

1. 聚类方法：规则分层（单事件）+ K-Means（多事件）
2. 聚类数量：{total_clusters} 类（规则 {n_single_clusters} + K-Means {multi_n_clusters}）
3. 轮廓系数（多事件会话，合并前）：{sil_pre_merge:.4f}，（合并后）：{sil_post_merge:.4f}
4. 数据过滤：移除 {outlier_count} 个时长异常会话（>24h）
5. 总训练样本数：{len(df_all):,}
6. 小聚类合并：{cluster_merge_map if cluster_merge_map else '无'}

7. 各聚类特征（业务视角）：
""")

for i in range(total_clusters):
    biz = cluster_profiles_business.loc[i]
    count = (df_all['cluster'] == i).sum()
    pct = count / len(df_all) * 100
    if i < n_single_clusters:
        label = single_labels[i]
    else:
        label = f"K-Means Cluster {i - n_single_clusters}"
    print(f"   Cluster {i}（{label}，{count:,} 个会话，占 {pct:.1f}%）：")
    print(f"      - 平均事件数: {biz['event_count']:.1f}")
    print(f"      - 平均商品数: {biz['unique_products']:.1f}")
    print(f"      - 平均加购数: {biz['cart_count']:.1f}")
    print(f"      - 平均购买数: {biz['purchase_count']:.1f}")
    print(f"      - 平均会话时长: {biz['session_duration_min']:.1f} 分钟")
    print(f"      - 平均购买金额: {biz['purchase_amount']:.1f}")
    print()

# ==================== 10. 聚类质量验证 ====================
print("\n" + "=" * 50)
print("10. 聚类质量验证")
print("=" * 50)

biz_profiles = cluster_profiles_business
purchase_diversity = biz_profiles['purchase_count'].std()
amount_diversity = biz_profiles['purchase_amount'].std()

print(f"   轮廓系数（多事件会话）：{sil_post_merge:.4f}")
print(f"   购买数标准差：{purchase_diversity:.4f}")
print(f"   购买金额标准差：{amount_diversity:.4f}")

# 覆盖率检查：验证购买用户是否被正确分到含购买行为的聚类中
total_purchasing = int(df_all['has_purchase'].sum())
clusters_with_purchase = df_all[df_all['has_purchase'] == 1]['cluster'].nunique()
print(f"   购买用户总数：{total_purchasing:,}，分布在 {clusters_with_purchase} 个聚类中")

print("\n" + "=" * 50)
print("子任务 2.2 完成！（全量用户分群）")
print("=" * 50)
