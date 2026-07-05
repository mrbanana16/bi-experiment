# 电商平台用户行为分析与商品推荐策略研究

本项目为《商务智能与数据挖掘综合实习》课程项目，主题为“电商平台用户行为分析与商品推荐策略研究”。 项目基于公开电商平台用户行为数据集，围绕用户浏览、加购、购买等行为展开分析，完成数据预处理、用户行为分析、用户分群、商品关联规则挖掘、商品推荐策略设计、数据可视化展示以及 AI 智能分析模块开发。

项目目标是将原始电商用户行为数据转化为具有业务解释价值的分析结果，并进一步形成可落地的商品推荐策略和 AI 辅助分析能力，为电商平台用户运营、商品推荐和营销决策提供参考。

---

## 一、项目主要功能

本项目主要包括以下功能模块：

1. **数据采集与预处理**
   - 读取公开电商用户行为数据集；
   - 处理缺失值、重复值和异常数据；
   - 转换时间字段；
   - 构建购买行为表和用户会话特征表。

2. **用户行为分析**
   - 分析浏览、加购、购买等行为数量；
   - 构建用户行为转化漏斗；
   - 分析用户行为时间分布、商品品类热度、价格区间转化率和用户消费特征。

3. **用户分群分析**
   - 针对单事件会话采用规则分层；
   - 针对多事件会话使用 K-Means 聚类；
   - 识别仅浏览型、加购未转化型、直接购买型、高价值转化型等用户群体。

4. **商品关联规则挖掘**
   - 基于购买行为构建用户级购买事务表；
   - 使用 Apriori 算法挖掘频繁项集和商品关联规则；
   - 分析商品之间的搭配购买关系。

5. **商品推荐策略设计**
   - 基于购买次数和销售金额生成热门商品推荐；
   - 基于 Apriori 关联规则生成关联商品推荐；
   - 基于用户分群和品类偏好生成用户群体偏好推荐；
   - 最终输出结构化推荐结果 `recommendations.json`。

6. **数据可视化展示**
   - 生成转化漏斗图、品类热度图、用户分群雷达图、推荐策略数量图、热力图和 HTML Dashboard 页面；
   - 直观展示数据分析和推荐策略结果。

7. **AI 智能分析模块**
   - 使用 Flask 构建后端服务；
   - 使用 HTML、CSS、JavaScript 构建前端页面；
   - 调用 DeepSeek API 进行自然语言问答；
   - 支持选择分析结果文件、AI 智能解读、历史对话保存、Markdown / Word / PDF 导出。

---

## 二、开发环境

### Python 版本

推荐使用：

```text
Python 3.11.9
```

开发过程中请尽量保持所有成员使用相同 Python 版本，以避免依赖兼容问题。

### 2. 操作系统

本项目主要在 Windows 11 环境下开发和测试。
其中，AI 模块的 PDF 导出功能依赖本机 Microsoft Word 环境，建议在 Windows + Microsoft Word 环境下运行。

### 3. 主要技术栈

| 类型        | 技术                                     |
| ----------- | ---------------------------------------- |
| 编程语言    | Python、HTML、CSS、JavaScript            |
| 数据处理    | pandas、numpy                            |
| 机器学习    | scikit-learn                             |
| 关联规则    | mlxtend                                  |
| 可视化      | matplotlib、seaborn                      |
| Web 后端    | Flask                                    |
| AI 模型调用 | DeepSeek API、openai 兼容接口            |
| 文档导出    | python-docx、pypandoc、docx2pdf、pywin32 |
| 项目管理    | Git、GitHub                              |

---

## 三、项目开发初始化

### 0 配置git
（可选）为防止git连接GitHub失败，可先为git设置本地代理

```bash
# 为 GitHub 设置 HTTP 代理（设置一次即可，将xxxx替换为自己代理的端口）
git config --global http.https://github.com.proxy http://127.0.0.1:xxxx
```

### 1. 克隆仓库

```bash
git clone <仓库克隆url>
cd <repository-name>
```

### 2. 创建虚拟环境

Windows：

```bash
python -m venv .venv
```

MacOS / Linux：

```bash
python3 -m venv .venv
```

### 3. 激活虚拟环境

Windows：

```bash
.venv\Scripts\activate
```

MacOS / Linux：

```bash
source .venv/bin/activate
```

### 4. 安装项目依赖

```bash
pip install -r requirements.txt
```

安装完成后即可开始开发。

---

## 四、项目目录结构

```text
project/
├─ Datasets/                     # 数据文件
│  ├─ raw/                        # 原始数据
│  └─ processed/                  # 预处理后的数据
│
├─ notebook/                      # Jupyter Notebook（可选）
│
├─ src/                           # 项目源代码
│  ├─ ai-module/                  # AI 智能分析助手前后端模块
│  ├─ step1_preprocess.py         # 数据预处理脚本
│  ├─ step2_1_behavior_analysis.py# 用户行为分析脚本
│  ├─ step2_2_clustering.py       # 用户分群分析脚本
│  ├─ step2_3_association_rules.py# 商品关联规则挖掘脚本
│  ├─ step3_recommendation.py     # 商品推荐策略脚本
│  ├─ step4_visualization.py      # 三个综合可视化脚本
│  ├─ visualization_hot_products.py
│  └─ visualization_cluster_user.py
│
├─ result/                        # 输出结果
│  ├─ figures/                    # 可视化图表与 HTML Dashboard
│  ├─ reports/                    # 分析报告
│  ├─ models/                     # 模型结果、关联规则、推荐结果等
│  └─ ai/                         # AI 模块输出结果
│     ├─ ai-history/              # AI 历史对话记录
│     └─ ai-output/               # AI 导出的 md / docx / pdf 文件
│
├─ requirements.txt               # 项目依赖
├─ .gitignore
└─ README.md
```

---

## 五、项目运行流程

### 0.依赖安装

在执行代码前，必须先安装所有依赖。在终端输入命令：

```bash
pip install -r requirements.txt
```

建议按照以下顺序运行项目：

### 1. 数据预处理

运行数据预处理脚本，对原始数据进行缺失值处理、重复值处理、时间字段转换和会话特征构造。

```bash
python src/step1_preprocess.py
```

主要输出：

- 清洗后的有效数据；
- 购买行为表；
- 用户会话特征表。

### 2. 用户行为分析

```bash
python src/step2_1_behavior_analysis.py
```

主要分析内容：

- 用户行为转化漏斗；
- 时间分布特征；
- 商品品类热度；
- 不同价格区间转化率；
- 用户消费特征。

### 3. 用户分群分析

```bash
python src/step2_2_clustering.py
```

主要分析内容：

- 单事件会话规则分群；
- 多事件会话 K-Means 聚类；
- 用户群体画像；
- 各聚类品类偏好。

### 4. 商品关联规则挖掘

```bash
python src/step2_3_association_rules.py
```

主要分析内容：

- 构建用户级购买事务表；
- 使用 Apriori 挖掘频繁项集；
- 生成商品关联规则。

### 5. 商品推荐策略生成

```bash
python src/step3_recommendation.py
```

主要输出：

```text
result/models/recommendations.json
```

推荐结果包括：

- 热门商品推荐；
- 关联商品推荐；
- 用户群体偏好推荐。

### 6. 数据可视化展示

```bash
python src/step4_visualization.py
python src/visualization_hot_products.py
python src/visualization_cluster_user.py
```

主要输出：

- 转化漏斗图；
- 品类热度图；
- 用户分群雷达图；
- 推荐策略数量对比图；
- 品类偏好热力图；
- HTML Dashboard 页面。

### 7. 启动 AI 智能分析模块

在运行 AI 模块前，务必在 `src/ai-module/backend.py` 中输入 DeepSeek API Key。

```python
DEEPSEEK_API_KEY = "your_api_key"
```

然后进入 AI 模块目录：

```bash
cd src/ai-module
```

运行 Flask 后端：

```bash
python backend.py
```

浏览器访问：

```text
http://127.0.0.1:9090/
```

即可进入“电商数据智能分析助手”。

主要功能包括：

- 选择待分析结果文件；
- 调用 DeepSeek API 进行自然语言问答；
- 根据分析结果生成运营建议；
- 保存和读取历史对话；
- 导出 Markdown、Word、PDF 文件；
- 生成正式 AI 分析报告。

------

## 八、Git 开发流程

### 开始开发前

先同步最新代码：

```bash
git pull
```

### 提交代码


查看变更：

```bash
git status
```

添加文件：

```bash
git add .
```

提交：

```bash
git commit -m "本次提交的内容说明"
```

推送：

```bash
git push
```

---

## 九、数据文件管理

原则：

### 上传

- 小型示例数据
- 已清洗后的分析数据
- 项目运行所需配置文件

### 不上传

- 超大原始数据集
- 临时缓存文件
- 本地生成的日志文件
- 虚拟环境文件

---

## 十、开发原则

1. 每次开发前先执行 `git pull`
2. 每次功能完成后及时提交
3. 新增依赖必须同步更新 `requirements.txt`
4. 不提交 `.venv`、缓存文件和临时数据
5. 保持代码结构清晰、命名统一

---

## 十一、常见问题

### 1. 安装依赖后仍然运行失败

可以尝试重新安装依赖：

```bash
pip install -r requirements.txt
```

如仍有问题，检查 Python 版本是否与推荐版本一致。

### 2. AI 模块无法连接 DeepSeek

请检查：

- API Key 是否填写正确；
- 网络是否正常；
- DeepSeek API 服务是否可用；

### 3. PDF 导出失败

PDF 导出通常依赖本机 Microsoft Word 环境。若未安装 Word，可以优先导出 Markdown 或 Word 文件。

### 4. GitHub 提交失败

可先检查是否需要配置代理，或确认远程仓库地址和账号权限是否正确。