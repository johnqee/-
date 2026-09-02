# BERT 微调文本分类 — 基于 `fka/prompts.chat`

使用 **PyTorch + HuggingFace Transformers** 对 **BERT** 进行微调，完成文本分类任务。数据集 `fka/prompts.chat` 的 prompt 文本被分类到三个 `type` 类别：**TEXT / STRUCTURED / IMAGE**。训练/评估使用 `transformers.Trainer` 实现，全部缓存与产物保存在本目录内。

---

## 1. 项目背景与可行性要点

要求原文希望：基于 BERT 做文本分类微调，用 torch + transformers + Trainer，数据缓存在本目录，产出流程图与 README。

在动手前对数据与模型做了可行性核查，得到三条关键结论，并据其对要求做了修正：

| 核查项 | 实测结果 | 处理 |
|---|---|---|
| `act` 字段 | 2109 行数据，`act` 共 **2109 类、每类仅 1 个样本** | 无法用于分类，改用 `type` 字段做三分类 |
| 模型 | 要求数据为**全英文**，而 `bert-base-chinese` 是中文模型 | 改用英文模型 **`bert-base-uncased`** |
| 模型类 | 要求给的 `AutoModelForMaskedLM` 是掩码预训练头 | 改用 **`AutoModelForSequenceClassification`**（分类头） |

数据集 `type` 分布极不均衡，是本任务的主要难点：

| 类别 | 样本数 | 占比 |
|---|---|---|
| TEXT | 1780 | 84.4% |
| STRUCTURED | 308 | 14.6% |
| IMAGE | 21 | 1.0% |

为缓解不平衡，训练时采用了**带类别权重的交叉熵损失**（逆频率加权，再归一化到均值 1）。

---

## 2. 运行环境

- **Python 环境**：conda 环境 `course`（`E:\Conda\envs\course`），已设为默认环境。
- 硬件：NVIDIA RTX 5080 16GB（torch 2.11.0+cu128，CUDA 可用）。
- 关键库：torch、transformers 5.14.1、datasets 5.0.1、scikit-learn 1.9.0、matplotlib（画流程图）。

如需在终端默认使用该环境，已写入 `~/.bashrc` / `~/.bash_profile`（将 `course` 的 `python`/`Scripts` 前置于 PATH）。

---

## 3. 项目结构

```
作业/
├── 要求.md                 # 原始需求
├── README.md               # 本说明文件
├── flowchart.png           # 项目流程图
├── cache/                  # HuggingFace 下载缓存（模型与数据集）
├── data/                   # 数据准备脚本生成的数据
│   ├── train.jsonl          #  1687 行
│   ├── val.jsonl            #   211 行
│   └── test.jsonl           #   211 行
├── outputs/                # 训练产物
│   ├── best/                #  以验证集 f1_macro 选出的最佳模型 + 分词器
│   ├── ckpt/                #  Trainer 的 checkpoint
│   └── logs/
└── src/                    # 源代码
    ├── config.py            #  路径与超参数配置
    ├── prepare_data.py      #  下载并划分数据
    ├── train.py             #  微调训练（Trainer）
    ├── predict.py           #  加载最佳模型推理
    └── make_flowchart.py    #  生成流程图
```

所有"需要下载/缓存"的内容（模型权重、数据集）统一落在 `cache/`，与要求文件同目录，分类新建了 `data/`、`outputs/` 等文件夹保存。

---

## 4. 使用方法

进入 `src/` 目录，依次运行：

```bash
cd src

# 1) 下载 fka/prompts.chat 并按 80/10/10 分层划分生成 data/*.jsonl
python prepare_data.py

# 2) 微调训练（自动下载 bert-base-uncased，GPU 上约 1~2 分钟）
python train.py

# 3) 用最佳模型对样例 prompt 推理
python predict.py

# 4) 重新生成流程图（如需）
python make_flowchart.py
```

### 关键超参数（见 `src/config.py`）

| 参数 | 值 | 说明 |
|---|---|---|
| MODEL_NAME | bert-base-uncased | 英文 BERT |
| MAX_LENGTH | 512 | BERT 上限；prompt p95≈1341 词，超长会被截断 |
| EPOCHS | 3 | |
| LR | 2e-5 | |
| TRAIN_BATCH / EVAL_BATCH | 16 / 32 | |
| 损失 | 带类别权重的交叉熵 | 缓解类别不平衡 |
| 评估指标 | accuracy / f1_macro | 以 f1_macro 选最佳模型 |

---

## 5. 训练结果

在 RTX 5080 上训练 3 个 epoch，约 78 秒。

| 评估集 | accuracy | f1_macro |
|---|---|---|
| 验证集（epoch1，被选为最佳） | 0.967 | 0.633 |
| 测试集 | 0.910 | 0.534 |

**对结果的如实说明**：

- **准确率较高（0.91）但 macro-F1 偏低（0.53）**，根因是 `IMAGE` 类仅 21 条（约 1%），样本过少导致模型基本预测为多数类 TEXT。这是该数据集在 `type` 三分类上的**固有难点**，加权损失不足以完全解决。
- 即便如此，整个微调流水线（下载→划分→tokenize→Trainer 训练→评估→保存→推理）是**完整、可运行、可复现**的，达到了作为 BERT 微调课程工程演示的目的。

### 改进方向（可选）

1. **扩样**：对 `IMAGE`/`STRUCTURED` 类做数据增强或过采样。
2. **合并稀有类**：把 `IMAGE` 并入 `STRUCTURED`，退化为二分类，macro-F1 会显著上升。
3. **改用 `for_devs` 二分类**标签（True/False 不平衡但至少两类样本都上百）。
4. **增加 epoch / 调整类别权重**权重强度（可乘一个温度系数放大对极小类的关注），或改用 `focal loss`。

---

## 6. 流程图

见本目录下的 `flowchart.png`，完整呈现了从数据下载到推理的全流程：

`fka/prompts.chat` → 下载到 cache/ → 按 type 筛选 → 分层划分 → tokenize → bert-base-uncased 序列分类模型 → WeightedTrainer 带权重训练 → 按 f1_macro 选最佳 → 保存 best → predict.py 推理。

---

## 7. 代码要点说明

- **`config.py`**：所有路径基于脚本位置推导（`Path(__file__).resolve().parent.parent`），项目整体移动后仍可运行；超参数集中管理。
- **`prepare_data.py`**：用 `train_test_split` 的 `stratify` 做分层划分，保护 IMAGE 等小类不被切零。
- **`train.py`**：
  - 用 `AutoModelForSequenceClassification` 而非 `AutoModelForMaskedLM`（后者是预训练掩码头，不适合分类）。
  - 自定义 `WeightedTrainer`（继承 `Trainer`，重写 `compute_loss`）实现加权交叉熵。
  - `load_best_model_at_end=True` + `metric_for_best_model="f1_macro"`，自动保留最优模型到 `outputs/best`。
- **`predict.py`**：从 `outputs/best` 加载，输出预测类别与各类概率。
- **`make_flowchart.py`**：纯 matplotlib 绘制，自动回退 Windows 中文字体，仅依赖 matplotlib。