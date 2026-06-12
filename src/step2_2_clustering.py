"""
子任务 2.2：用户分群分析（K-Means聚类）
数据集：Datasets/processed/session_based_features.csv
输出：result/figures/ 下的聚类图表，result/models/ 下的聚类模型
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
import pickle
import os
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

# ==================== 2. 特征选取与预处理 ====================
print("\n" + "=" * 50)
print("2. 特征选取与预处理")
print("=" * 50)

# 选取数值型特征用于聚类
feature_cols = ['event_count', 'unique_products', 'cart_count', 'purchase_count',
                'session_duration_min', 'purchase_amount', 'unique_categories']

X = df[feature_cols].copy()
print(f"\n选取的特征: {feature_cols}")
print(f"特征矩阵形状: {X.shape}")

# 处理缺失值（如果有）
X = X.fillna(0)

# 处理无穷值（如果有）
X = X.replace([np.inf, -np.inf], 0)

print(f"\n特征统计描述:\n{X.describe()}")

# 标准化
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
print(f"\n标准化后特征均值: {X_scaled.mean(axis=0).round(4)}")
print(f"标准化后特征标准差: {X_scaled.std(axis=0).round(4)}")

# ==================== 3. 确定最优K值 ====================
print("\n" + "=" * 50)
print("3. 确定最优K值")
print("=" * 50)

# 计算不同K值的惯性（Inertia）和轮廓系数（Silhouette Score）
K_range = range(2, 11)
inertias = []
silhouette_scores = []

for k in K_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans.fit(X_scaled)
    inertias.append(kmeans.inertia_)
    silhouette_scores.append(silhouette_score(X_scaled, kmeans.labels_))
    print(f"K={k}: Inertia={kmeans.inertia_:.2f}, Silhouette={silhouette_scores[-1]:.4f}")

# 找到最优K值（轮廓系数最大）
best_k = list(K_range)[np.argmax(silhouette_scores)]
print(f"\n最优K值（轮廓系数最大）: {best_k}")

# 绘制肘部法则和轮廓系数图
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# 左图：肘部法则
axes[0].plot(K_range, inertias, 'bo-')
axes[0].set_title('Elbow Method', fontsize=12, fontweight='bold')
axes[0].set_xlabel('Number of Clusters (K)')
axes[0].set_ylabel('Inertia')
axes[0].axvline(x=best_k, color='r', linestyle='--', label=f'Best K={best_k}')
axes[0].legend()
axes[0].set_xticks(list(K_range))

# 右图：轮廓系数
axes[1].plot(K_range, silhouette_scores, 'ro-')
axes[1].set_title('Silhouette Score', fontsize=12, fontweight='bold')
axes[1].set_xlabel('Number of Clusters (K)')
axes[1].set_ylabel('Silhouette Score')
axes[1].axvline(x=best_k, color='b', linestyle='--', label=f'Best K={best_k}')
axes[1].legend()
axes[1].set_xticks(list(K_range))

plt.tight_layout()
plt.savefig('result/figures/elbow_silhouette.png', dpi=150, bbox_inches='tight')
plt.close()
print("\n[OK] elbow_silhouette.png saved")

# ==================== 4. 执行K-Means聚类 ====================
print("\n" + "=" * 50)
print("4. 执行K-Means聚类")
print("=" * 50)

# 使用最优K值进行聚类
kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
df['cluster'] = kmeans.fit_predict(X_scaled)

print(f"\n聚类结果分布:\n{df['cluster'].value_counts().sort_index()}")
print(f"\n各聚类占比:\n{(df['cluster'].value_counts(normalize=True) * 100).round(2).sort_index()}")

# 保存聚类模型
model_path = 'result/models/kmeans_model.pkl'
with open(model_path, 'wb') as f:
    pickle.dump({'model': kmeans, 'scaler': scaler, 'feature_cols': feature_cols}, f)
print(f"\n[OK] K-Means model saved: {model_path}")

# ==================== 5. 聚类结果分析 ====================
print("\n" + "=" * 50)
print("5. 聚类结果分析")
print("=" * 50)

# 计算各聚类的特征均值
cluster_profiles = df.groupby('cluster')[feature_cols].mean()
print(f"\n各聚类特征均值:\n{cluster_profiles.round(2)}")

# 保存聚类画像
cluster_profiles_path = 'result/models/cluster_profiles.csv'
cluster_profiles.to_csv(cluster_profiles_path)
print(f"\n[OK] Cluster profiles saved: {cluster_profiles_path}")

# 计算各聚类的购买转化率
cluster_funnel = df.groupby('cluster').agg({
    'event_count': 'sum',
    'purchase_count': 'sum',
    'purchase_amount': 'sum'
})
cluster_funnel['conversion_rate'] = (cluster_funnel['purchase_count'] / cluster_funnel['event_count'] * 100).round(2)
print(f"\n各聚类转化率:\n{cluster_funnel}")

# ==================== 6. 可视化 ====================
print("\n" + "=" * 50)
print("6. 可视化")
print("=" * 50)

# 6.1 雷达图
fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

# 准备雷达图数据
categories = feature_cols
N = len(categories)
angles = [n / float(N) * 2 * np.pi for n in range(N)]
angles += angles[:1]

# 绘制每个聚类
colors = plt.cm.Set2(np.linspace(0, 1, best_k))
for i in range(best_k):
    values = cluster_profiles.loc[i].values.tolist()
    values += values[:1]
    ax.plot(angles, values, 'o-', linewidth=2, label=f'Cluster {i}', color=colors[i])
    ax.fill(angles, values, alpha=0.1, color=colors[i])

ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=9)
ax.set_title('Cluster Radar Chart', fontsize=14, fontweight='bold', pad=20)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
plt.tight_layout()
plt.savefig('result/figures/cluster_radar.png', dpi=150, bbox_inches='tight')
plt.close()
print("[OK] cluster_radar.png saved")

# 6.2 PCA降维散点图
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)

fig, ax = plt.subplots(figsize=(10, 8))
scatter = ax.scatter(X_pca[:, 0], X_pca[:, 1], c=df['cluster'], cmap='Set2', alpha=0.6, s=10)
ax.set_title('Cluster PCA Scatter Plot', fontsize=14, fontweight='bold')
ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]*100:.2f}%)')
ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]*100:.2f}%)')
plt.colorbar(scatter, label='Cluster')
plt.tight_layout()
plt.savefig('result/figures/cluster_pca.png', dpi=150, bbox_inches='tight')
plt.close()
print("[OK] cluster_pca.png saved")

# 6.3 各聚类特征对比柱状图
fig, axes = plt.subplots(2, 4, figsize=(16, 8))
axes = axes.flatten()

for i, col in enumerate(feature_cols):
    cluster_means = df.groupby('cluster')[col].mean()
    axes[i].bar(cluster_means.index, cluster_means.values, color=colors)
    axes[i].set_title(col, fontsize=10, fontweight='bold')
    axes[i].set_xlabel('Cluster')
    axes[i].set_ylabel('Mean Value')

# 隐藏多余的子图
axes[-1].axis('off')
plt.tight_layout()
plt.savefig('result/figures/cluster_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("[OK] cluster_comparison.png saved")

# ==================== 7. 聚类结论 ====================
print("\n" + "=" * 50)
print("7. 聚类结论")
print("=" * 50)

print(f"""
【用户分群分析汇总】

1. 聚类方法：K-Means
2. 聚类数量：{best_k} 类
3. 轮廓系数：{max(silhouette_scores):.4f}

4. 各聚类特征：
""")

for i in range(best_k):
    profile = cluster_profiles.loc[i]
    count = (df['cluster'] == i).sum()
    pct = count / len(df) * 100
    print(f"   Cluster {i}（{count:,} 个会话，占 {pct:.1f}%）：")
    print(f"      - 平均事件数: {profile['event_count']:.1f}")
    print(f"      - 平均商品数: {profile['unique_products']:.1f}")
    print(f"      - 平均加购数: {profile['cart_count']:.1f}")
    print(f"      - 平均购买数: {profile['purchase_count']:.1f}")
    print(f"      - 平均会话时长: {profile['session_duration_min']:.1f} 分钟")
    print(f"      - 平均购买金额: {profile['purchase_amount']:.1f}")
    print()

print("\n" + "=" * 50)
print("子任务 2.2 完成！")
print("=" * 50)
