"""
子任务 2.3：商品关联规则挖掘（Apriori）
数据集：从 Datasets/raw/Dataset.csv 重新生成事务表
输出：result/figures/ 下的关联规则图表，result/models/ 下的关联规则结果
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder
import networkx as nx
import os
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体（Windows）
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 创建输出目录
os.makedirs('result/figures', exist_ok=True)
os.makedirs('result/models', exist_ok=True)

# ==================== 1. 数据适配：生成事务表 ====================
print("=" * 50)
print("1. 数据适配：生成事务表")
print("=" * 50)

# 读取原始数据
df = pd.read_csv("Datasets/raw/Dataset.csv")
print(f"原始数据形状: {df.shape}")
print(f"列名: {df.columns.tolist()}")

# 过滤掉 category_code 为空的记录
df_with_category = df[df['category_code'].notna() & (df['category_code'] != '')]
print(f"\n有 category_code 的记录数: {len(df_with_category):,}")

# 按 user_session 聚合 category_code，生成事务表（去重）
transactions = df_with_category.groupby('user_session')['category_code'].apply(lambda x: list(set(x))).reset_index()
transactions.columns = ['user_session', 'items']

# 过滤掉只有1个类别的会话（无法产生关联规则）
transactions = transactions[transactions['items'].apply(len) > 1]
print(f"有 2+ 类别的会话数: {len(transactions):,}")

# 查看事务表示例
print(f"\n事务表示例:")
print(transactions.head())

# 保存事务表
transactions_path = 'Datasets/processed/transactions_for_apriori.csv'
transactions.to_csv(transactions_path, index=False)
print(f"\n[OK] 事务表已保存: {transactions_path}")

# ==================== 2. TransactionEncoder 编码 ====================
print("\n" + "=" * 50)
print("2. TransactionEncoder 编码")
print("=" * 50)

# 将事务列表转换为布尔矩阵
te = TransactionEncoder()
te_ary = te.fit(transactions['items']).transform(transactions['items'])
df_encoded = pd.DataFrame(te_ary, columns=te.columns_)

print(f"编码后矩阵形状: {df_encoded.shape}")
print(f"商品类别数: {len(te.columns_)}")
print(f"\n商品类别列表:")
for i, col in enumerate(te.columns_):
    print(f"  {i+1}. {col}")

# ==================== 3. Apriori 挖掘频繁项集 ====================
print("\n" + "=" * 50)
print("3. Apriori 挖掘频繁项集")
print("=" * 50)

# 设置最小支持度阈值
min_support = 0.01
print(f"最小支持度阈值: {min_support}")

# 挖掘频繁项集
frequent_itemsets = apriori(df_encoded, min_support=min_support, use_colnames=True)
print(f"\n频繁项集数量: {len(frequent_itemsets)}")

if len(frequent_itemsets) > 0:
    # 按支持度排序
    frequent_itemsets = frequent_itemsets.sort_values('support', ascending=False)
    print(f"\nTop 10 频繁项集:")
    print(frequent_itemsets.head(10))

    # 保存频繁项集
    frequent_itemsets_path = 'result/models/frequent_itemsets.csv'
    frequent_itemsets.to_csv(frequent_itemsets_path, index=False)
    print(f"\n[OK] 频繁项集已保存: {frequent_itemsets_path}")
else:
    print("\n[WARNING] 未找到频繁项集，请降低 min_support 阈值")

# ==================== 4. 生成关联规则 ====================
print("\n" + "=" * 50)
print("4. 生成关联规则")
print("=" * 50)

if len(frequent_itemsets) > 0:
    # 生成关联规则
    rules = association_rules(frequent_itemsets, metric="lift", min_threshold=1.0)
    print(f"关联规则数量: {len(rules)}")

    if len(rules) > 0:
        # 按 lift 排序
        rules = rules.sort_values('lift', ascending=False)

        # 转换 frozenset 为字符串以便显示
        rules['antecedents_str'] = rules['antecedents'].apply(lambda x: ', '.join(list(x)))
        rules['consequents_str'] = rules['consequents'].apply(lambda x: ', '.join(list(x)))

        print(f"\nTop 10 关联规则（按 lift 排序）:")
        top_rules = rules.head(10)[['antecedents_str', 'consequents_str', 'support', 'confidence', 'lift']]
        print(top_rules.to_string(index=False))

        # 保存关联规则
        rules_path = 'result/models/association_rules.csv'
        rules.to_csv(rules_path, index=False)
        print(f"\n[OK] 关联规则已保存: {rules_path}")
    else:
        print("\n[WARNING] 未生成关联规则，请调整参数")
else:
    print("\n[WARNING] 无频繁项集，无法生成关联规则")
    rules = pd.DataFrame()

# ==================== 5. 可视化 ====================
print("\n" + "=" * 50)
print("5. 可视化")
print("=" * 50)

if len(rules) > 0:
    # 5.1 支持度-置信度散点图
    fig, ax = plt.subplots(figsize=(10, 8))
    scatter = ax.scatter(rules['support'], rules['confidence'],
                        c=rules['lift'], cmap='YlOrRd', alpha=0.6, s=50)
    ax.set_title('Association Rules: Support vs Confidence', fontsize=14, fontweight='bold')
    ax.set_xlabel('Support')
    ax.set_ylabel('Confidence')
    plt.colorbar(scatter, label='Lift')
    plt.tight_layout()
    plt.savefig('result/figures/association_scatter.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("[OK] association_scatter.png saved")

    # 5.2 关联网络图（Top 20 规则）
    top_n = min(20, len(rules))
    top_rules = rules.head(top_n)

    G = nx.DiGraph()

    for _, row in top_rules.iterrows():
        antecedent = row['antecedents_str']
        consequent = row['consequents_str']
        lift = row['lift']

        G.add_node(antecedent)
        G.add_node(consequent)
        G.add_edge(antecedent, consequent, weight=lift)

    fig, ax = plt.subplots(figsize=(12, 10))
    pos = nx.spring_layout(G, k=2, iterations=50)

    # 绘制边
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color='gray',
                          width=[G[u][v]['weight']/2 for u, v in G.edges()],
                          alpha=0.5, arrows=True, arrowsize=20)

    # 绘制节点
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color='lightblue',
                          node_size=2000, alpha=0.8)
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=8, font_weight='bold')

    ax.set_title(f'Association Rules Network (Top {top_n})', fontsize=14, fontweight='bold')
    ax.axis('off')
    plt.tight_layout()
    plt.savefig('result/figures/association_network.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("[OK] association_network.png saved")

    # 5.3 Top 10 规则柱状图
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    top_10 = rules.head(10)
    x = range(len(top_10))

    # 支持度
    axes[0].barh(x, top_10['support'], color='#3498db', alpha=0.8)
    axes[0].set_yticks(x)
    axes[0].set_yticklabels([f"{a} -> {c}" for a, c in zip(top_10['antecedents_str'], top_10['consequents_str'])], fontsize=8)
    axes[0].set_title('Support', fontsize=12, fontweight='bold')
    axes[0].invert_yaxis()

    # 置信度
    axes[1].barh(x, top_10['confidence'], color='#e74c3c', alpha=0.8)
    axes[1].set_yticks(x)
    axes[1].set_yticklabels([f"{a} -> {c}" for a, c in zip(top_10['antecedents_str'], top_10['consequents_str'])], fontsize=8)
    axes[1].set_title('Confidence', fontsize=12, fontweight='bold')
    axes[1].invert_yaxis()

    # Lift
    axes[2].barh(x, top_10['lift'], color='#f39c12', alpha=0.8)
    axes[2].set_yticks(x)
    axes[2].set_yticklabels([f"{a} -> {c}" for a, c in zip(top_10['antecedents_str'], top_10['consequents_str'])], fontsize=8)
    axes[2].set_title('Lift', fontsize=12, fontweight='bold')
    axes[2].invert_yaxis()

    plt.tight_layout()
    plt.savefig('result/figures/association_top10.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("[OK] association_top10.png saved")

else:
    print("[SKIP] 无关联规则，跳过可视化")

# ==================== 6. 汇总统计 ====================
print("\n" + "=" * 50)
print("6. 汇总统计")
print("=" * 50)

print(f"""
【商品关联规则挖掘汇总】

1. 数据处理：
   - 原始记录数：{len(df):,}
   - 有类别记录数：{len(df_with_category):,}
   - 有效事务数（2+类别）：{len(transactions):,}

2. 频繁项集：
   - 最小支持度阈值：{min_support}
   - 频繁项集数量：{len(frequent_itemsets) if len(frequent_itemsets) > 0 else 0}

3. 关联规则：
   - 关联规则数量：{len(rules) if len(rules) > 0 else 0}
""")

if len(rules) > 0:
    print(f"4. Top 5 关联规则（按 lift 排序）:")
    for i, (_, row) in enumerate(rules.head(5).iterrows()):
        print(f"   {i+1}. {row['antecedents_str']} -> {row['consequents_str']}")
        print(f"      Support: {row['support']:.4f}, Confidence: {row['confidence']:.4f}, Lift: {row['lift']:.4f}")

print("\n" + "=" * 50)
print("子任务 2.3 完成！")
print("=" * 50)
