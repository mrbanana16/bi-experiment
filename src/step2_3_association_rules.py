"""
子任务 2.3：商品关联规则挖掘（Apriori）
数据集：从 Datasets/processed/preprocessed.csv 生成事务表
输出：result/figures/ 下的关联规则图表，result/models/ 下的关联规则结果
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
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
print("1. 数据适配：生成事务表（用户级共购）")
print("=" * 50)

# 读取预处理数据
df = pd.read_csv("Datasets/processed/preprocessed.csv")
print(f"预处理数据形状: {df.shape}")
print(f"列名: {df.columns.tolist()}")

# 仅取购买记录，构建"用户级共购事务表"
# 理由：关联规则用于推荐应基于实际购买行为；用户可能跨会话浏览后在另一个会话完成购买
df_purchase = df[df['event_type'] == 'purchase'].copy()
df_purchase = df_purchase[df_purchase['category_code'].notna() & (df_purchase['category_code'] != '')]
print(f"\n购买记录数: {len(df_purchase):,}")
print(f"有品类的购买用户数: {df_purchase['user_id'].nunique():,}")

# 提取一级品类（如 electronics.smartphone -> electronics）
df_purchase['category_l1'] = df_purchase['category_code'].str.split('.').str[0]

# --- 细粒度事务表（原始 category_code）---
# Apriori 前提：只有包含 2+ 品类的事务才可能产生关联规则
# 单品类事务会被 Apriori 自动过滤（无法形成 itemset），但会稀释 support 导致规则无法生成
print("\n--- 细粒度分析（category_code）---")
transactions_all = df_purchase.groupby('user_id')['category_code'].apply(lambda x: list(set(x))).reset_index()
transactions_all.columns = ['user_id', 'items']
total_purchasing_users = len(transactions_all)
multi_cat_users = (transactions_all['items'].apply(len) > 1).sum()
transactions = transactions_all[transactions_all['items'].apply(len) > 1].copy()
print(f"购买用户总数: {total_purchasing_users:,}")
print(f"跨品类用户（事务数）: {len(transactions):,}（{len(transactions)/total_purchasing_users*100:.1f}%）")

# --- 粗粒度事务表（一级品类）---
print("\n--- 粗粒度分析（category_l1）---")
transactions_l1_all = df_purchase.groupby('user_id')['category_l1'].apply(lambda x: list(set(x))).reset_index()
transactions_l1_all.columns = ['user_id', 'items']
multi_cat_users_l1 = (transactions_l1_all['items'].apply(len) > 1).sum()
transactions_l1 = transactions_l1_all[transactions_l1_all['items'].apply(len) > 1].copy()
print(f"跨品类用户（事务数）: {len(transactions_l1):,}（{len(transactions_l1)/total_purchasing_users*100:.1f}%）")

# 保存事务表（细粒度）
transactions_path = 'Datasets/processed/transactions_for_apriori.csv'
transactions.to_csv(transactions_path, index=False)
print(f"\n[OK] 细粒度事务表已保存: {transactions_path}")

# 保存事务表（粗粒度）
transactions_l1_path = 'Datasets/processed/transactions_l1_for_apriori.csv'
transactions_l1.to_csv(transactions_l1_path, index=False)
print(f"[OK] 粗粒度事务表已保存: {transactions_l1_path}")


def run_apriori_pipeline(transactions_df, min_support=0.01, min_lift=1.0, label=""):
    """运行完整的 Apriori 管线，返回 (frequent_itemsets, rules)"""
    print(f"\n{'='*50}")
    print(f"Apriori 管线 [{label}]")
    print(f"{'='*50}")

    if len(transactions_df) == 0:
        print(f"[WARNING] 无有效事务，跳过 {label}")
        return pd.DataFrame(), pd.DataFrame()

    # TransactionEncoder 编码
    te = TransactionEncoder()
    te_ary = te.fit(transactions_df['items']).transform(transactions_df['items'])
    df_encoded = pd.DataFrame(te_ary, columns=te.columns_)
    print(f"编码后矩阵形状: {df_encoded.shape}")
    print(f"商品类别数: {len(te.columns_)}")

    # Apriori 挖掘频繁项集
    frequent_itemsets = apriori(df_encoded, min_support=min_support, use_colnames=True)
    print(f"频繁项集数量: {len(frequent_itemsets)}")

    if len(frequent_itemsets) == 0:
        print(f"[WARNING] 未找到频繁项集 [{label}]")
        return pd.DataFrame(), pd.DataFrame()

    frequent_itemsets = frequent_itemsets.sort_values('support', ascending=False)

    # 生成关联规则
    # min_threshold 控制下界：fine-grained 用 1.0 排除独立规则(lift=1.0)，coarse-grained 用 1.1 排除弱规则
    rules = association_rules(frequent_itemsets, metric="lift", min_threshold=min_lift)
    if min_lift <= 1.0:
        rules = rules[rules['lift'] > 1.0]  # 排除 lift=1.0（独立）的规则
    print(f"关联规则数量（含双向）: {len(rules)}")

    if len(rules) == 0:
        print(f"[WARNING] 未生成关联规则 [{label}]")
        return frequent_itemsets, pd.DataFrame()

    rules = rules.sort_values('lift', ascending=False)

    # 转换 frozenset 为字符串
    rules['antecedents_str'] = rules['antecedents'].apply(lambda x: ', '.join(list(x)))
    rules['consequents_str'] = rules['consequents'].apply(lambda x: ', '.join(list(x)))

    # 双向去重：保留提升度较高的一条（与最终按 lift 排序的展示逻辑一致）
    rules_for_dedup = rules.copy()
    rules_for_dedup['_pair_key'] = rules_for_dedup.apply(
        lambda r: tuple(sorted([r['antecedents_str'], r['consequents_str']])), axis=1)
    rules_deduped = rules_for_dedup.sort_values(['lift', 'confidence'], ascending=[False, False]).drop_duplicates(
        subset='_pair_key', keep='first')
    rules_deduped = rules_deduped.drop(columns=['_pair_key'])

    print(f"去重后独立规则: {len(rules_deduped)}")

    # 将 frozenset 列转为干净的字符串（避免 CSV 序列化为 "frozenset({'xxx'})"）
    # 注意：必须在 association_rules() 之后转换，因为 mlxtend 需要 frozenset 格式
    # 此操作会覆盖原始 frozenset 列，如需 frozenset 格式可从 antecedents_str 重新解析
    rules_deduped['antecedents'] = rules_deduped['antecedents_str']
    rules_deduped['consequents'] = rules_deduped['consequents_str']
    frequent_itemsets['itemsets'] = frequent_itemsets['itemsets'].apply(lambda x: ', '.join(sorted(list(x))))

    return frequent_itemsets, rules_deduped


# ==================== 2. 细粒度分析 ====================
# 跨品类用户仅 9 人，min_support=0.1 要求至少 1 个用户支持
frequent_itemsets, rules_deduped = run_apriori_pipeline(
    transactions, min_support=0.1, label="细粒度")

# 保存细粒度结果
if len(frequent_itemsets) > 0:
    frequent_itemsets.to_csv('result/models/frequent_itemsets.csv', index=False)
    print(f"[OK] 频繁项集已保存: result/models/frequent_itemsets.csv")
if len(rules_deduped) > 0:
    rules_deduped.to_csv('result/models/association_rules.csv', index=False)
    print(f"[OK] 关联规则已保存: result/models/association_rules.csv")
else:
    rules_path = 'result/models/association_rules.csv'
    if os.path.exists(rules_path):
        os.remove(rules_path)
        print(f"[INFO] 细粒度无规则，已删除旧文件: {rules_path}")

# ==================== 2.5 粗粒度分析 ====================
frequent_itemsets_l1, rules_l1_deduped = run_apriori_pipeline(
    transactions_l1, min_support=0.1, min_lift=1.1, label="粗粒度")

# 保存粗粒度结果
if len(frequent_itemsets_l1) > 0:
    # 确保 itemsets 列为干净字符串（run_apriori_pipeline 内部已转换，此处二次保障）
    if frequent_itemsets_l1['itemsets'].dtype == object:
        sample = str(frequent_itemsets_l1['itemsets'].iloc[0])
        if sample.startswith('frozenset'):
            frequent_itemsets_l1['itemsets'] = frequent_itemsets_l1['itemsets'].apply(
                lambda x: ', '.join(sorted(list(x))) if isinstance(x, frozenset) else str(x)
            )
    frequent_itemsets_l1.to_csv('result/models/frequent_itemsets_l1.csv', index=False)
    print(f"[OK] 粗粒度频繁项集已保存: result/models/frequent_itemsets_l1.csv")
if len(rules_l1_deduped) > 0:
    rules_l1_deduped.to_csv('result/models/association_rules_l1.csv', index=False)
    print(f"[OK] 粗粒度关联规则已保存: result/models/association_rules_l1.csv")
else:
    # 无规则时删除旧文件，避免下游读到过期数据
    l1_rules_path = 'result/models/association_rules_l1.csv'
    if os.path.exists(l1_rules_path):
        os.remove(l1_rules_path)
        print(f"[INFO] 粗粒度无规则，已删除旧文件: {l1_rules_path}")

# ==================== 3. 可视化（细粒度） ====================
print("\n" + "=" * 50)
print("3. 可视化（细粒度关联规则）")
print("=" * 50)

if len(rules_deduped) > 0:
    # 3.1 支持度-置信度散点图
    fig, ax = plt.subplots(figsize=(10, 8))
    scatter = ax.scatter(rules_deduped['support'], rules_deduped['confidence'],
                        c=rules_deduped['lift'], cmap='YlOrRd', alpha=0.6, s=50)
    ax.set_title('Association Rules: Support vs Confidence', fontsize=14, fontweight='bold')
    ax.set_xlabel('Support')
    ax.set_ylabel('Confidence')
    plt.colorbar(scatter, label='Lift')
    plt.tight_layout()
    plt.savefig('result/figures/association_scatter.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("[OK] association_scatter.png saved")

    # 3.2 关联网络图（Top 20 去重规则）
    top_n = min(20, len(rules_deduped))
    top_rules = rules_deduped.head(top_n)

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
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color='gray',
                          width=[G[u][v]['weight']/2 for u, v in G.edges()],
                          alpha=0.5, arrows=True, arrowsize=20)
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color='lightblue',
                          node_size=2000, alpha=0.8)
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=8, font_weight='bold')
    ax.set_title(f'Association Rules Network (Top {top_n})', fontsize=14, fontweight='bold')
    ax.axis('off')
    plt.tight_layout()
    plt.savefig('result/figures/association_network.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("[OK] association_network.png saved")

    # 3.3 Top 10 规则柱状图
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    top_10 = rules_deduped.head(10)
    x = range(len(top_10))

    axes[0].barh(x, top_10['support'], color='#3498db', alpha=0.8)
    axes[0].set_yticks(x)
    axes[0].set_yticklabels([f"{a} -> {c}" for a, c in zip(top_10['antecedents_str'], top_10['consequents_str'])], fontsize=8)
    axes[0].set_title('Support', fontsize=12, fontweight='bold')
    axes[0].invert_yaxis()

    axes[1].barh(x, top_10['confidence'], color='#e74c3c', alpha=0.8)
    axes[1].set_yticks(x)
    axes[1].set_yticklabels([f"{a} -> {c}" for a, c in zip(top_10['antecedents_str'], top_10['consequents_str'])], fontsize=8)
    axes[1].set_title('Confidence', fontsize=12, fontweight='bold')
    axes[1].invert_yaxis()

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
    print("[SKIP] 无细粒度关联规则，跳过可视化")

# ==================== 4. 可视化（粗粒度） ====================
print("\n" + "=" * 50)
print("4. 可视化（粗粒度关联规则）")
print("=" * 50)

if len(rules_l1_deduped) > 0:
    # 粗粒度 Top10 柱状图
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    top_10_l1 = rules_l1_deduped.head(10)
    x = range(len(top_10_l1))

    axes[0].barh(x, top_10_l1['support'], color='#3498db', alpha=0.8)
    axes[0].set_yticks(x)
    axes[0].set_yticklabels([f"{a} -> {c}" for a, c in zip(top_10_l1['antecedents_str'], top_10_l1['consequents_str'])], fontsize=8)
    axes[0].set_title('Support (L1 Category)', fontsize=12, fontweight='bold')
    axes[0].invert_yaxis()

    axes[1].barh(x, top_10_l1['confidence'], color='#e74c3c', alpha=0.8)
    axes[1].set_yticks(x)
    axes[1].set_yticklabels([f"{a} -> {c}" for a, c in zip(top_10_l1['antecedents_str'], top_10_l1['consequents_str'])], fontsize=8)
    axes[1].set_title('Confidence (L1 Category)', fontsize=12, fontweight='bold')
    axes[1].invert_yaxis()

    axes[2].barh(x, top_10_l1['lift'], color='#f39c12', alpha=0.8)
    axes[2].set_yticks(x)
    axes[2].set_yticklabels([f"{a} -> {c}" for a, c in zip(top_10_l1['antecedents_str'], top_10_l1['consequents_str'])], fontsize=8)
    axes[2].set_title('Lift (L1 Category)', fontsize=12, fontweight='bold')
    axes[2].invert_yaxis()

    plt.tight_layout()
    plt.savefig('result/figures/association_top10_l1.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("[OK] association_top10_l1.png saved")
else:
    print("[SKIP] 无粗粒度关联规则，跳过可视化")

# ==================== 5. 汇总统计 ====================
print("\n" + "=" * 50)
print("5. 汇总统计")
print("=" * 50)

print(f"""
【商品关联规则挖掘汇总】

1. 数据处理：
   - 预处理记录数：{len(df):,}
   - 购买记录数：{len(df_purchase):,}
   - 购买用户数：{total_purchasing_users:,}
   - 跨品类用户（细粒度）：{multi_cat_users:,}（{multi_cat_users/total_purchasing_users*100:.1f}%）
   - 跨品类用户（粗粒度）：{multi_cat_users_l1:,}（{multi_cat_users_l1/total_purchasing_users*100:.1f}%）

2. 细粒度分析（category_code）：
   - 有效事务数：{len(transactions):,}
   - 频繁项集数量：{len(frequent_itemsets) if len(frequent_itemsets) > 0 else 0}
   - 关联规则数量（去重）：{len(rules_deduped) if len(rules_deduped) > 0 else 0}

3. 粗粒度分析（一级品类）：
   - 有效事务数：{len(transactions_l1):,}
   - 频繁项集数量：{len(frequent_itemsets_l1) if len(frequent_itemsets_l1) > 0 else 0}
   - 关联规则数量（去重）：{len(rules_l1_deduped) if len(rules_l1_deduped) > 0 else 0}
""")

if len(rules_deduped) > 0:
    print("4. Top 5 细粒度关联规则（按 lift 排序）:")
    for i, (_, row) in enumerate(rules_deduped.head(5).iterrows()):
        print(f"   {i+1}. {row['antecedents_str']} -> {row['consequents_str']}")
        print(f"      Support: {row['support']:.4f}, Confidence: {row['confidence']:.4f}, Lift: {row['lift']:.4f}")

if len(rules_l1_deduped) > 0:
    print(f"\n5. Top 5 粗粒度关联规则（按 lift 排序）:")
    for i, (_, row) in enumerate(rules_l1_deduped.head(5).iterrows()):
        print(f"   {i+1}. {row['antecedents_str']} -> {row['consequents_str']}")
        print(f"      Support: {row['support']:.4f}, Confidence: {row['confidence']:.4f}, Lift: {row['lift']:.4f}")

print("\n" + "=" * 50)
print("子任务 2.3 完成！")
print("=" * 50)
