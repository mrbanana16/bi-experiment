# 项目开发说明

## 开发环境

### Python 版本

推荐使用：

```text
Python 3.11.9
```

开发过程中请尽量保持所有成员使用相同 Python 版本，以避免依赖兼容问题。

---

## 项目初始化

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

## 项目目录结构

```text
project/

├─ Datasets/            # 数据文件
│   ├─ raw/             # 原始数据【注意，不要上传太大的原始数据】
│   └─ processed/       # 处理后数据
│
├─ notebook/            # Jupyter Notebook（可选，需保留分步执行代码或运行结果时编写）
│
├─ src/                 # 源代码
│   └─ ai-module/       # AI 智能分析助手前后端模块
│
├─ result/              # 输出结果
│   ├─ figures/         # 图表
│   ├─ reports/         # 分析报告
│   ├─ models/          # 模型结果
│   └─ ai-history/      # AI 助手历史对话记录
│
├─ requirements.txt     # 项目依赖
├─ .gitignore
└─ README.md
```

---

## ！！！依赖管理

### 安装新依赖

例如：

```bash
pip install pandas
```

【重要！】安装成功后更新依赖文件：

```bash
pip freeze > requirements.txt
```

然后，将依赖文件随其他代码更改一起提交：

```bash
git add requirements.txt
git commit -m "update dependencies"
git push
```

其他成员拉取最新代码后执行：

```bash
pip install -r requirements.txt
```

即可同步最新依赖。

---



## Git 开发流程

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


## 数据文件管理

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

## 常见问题

### 更新依赖后其他成员运行报错

执行：

```bash
pip install -r requirements.txt
```

重新同步依赖。

---


## 开发原则

1. 每次开发前先执行 `git pull`
2. 每次功能完成后及时提交
3. 新增依赖必须同步更新 `requirements.txt`
4. 不提交 `.venv`、缓存文件和临时数据
5. 保持代码结构清晰、命名统一
