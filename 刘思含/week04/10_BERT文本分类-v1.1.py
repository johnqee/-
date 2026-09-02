import os
import pandas as pd
import torch
from sklearn.model_selection import train_test_split
# AutoTokenizer / AutoModelForSequenceClassification：根据模型名自动选择对应的类
#   - AutoTokenizer：通用分词器（与 BertTokenizer 等价，但更灵活）
#   - AutoModelForSequenceClassification：通用文本分类模型，会在 BERT 顶部自动接一个分类头
#   注意：要求里给的 AutoModelForMaskedLM 是“掩码语言模型”，用于填空预测，
#         不能直接做文本分类，这里改用 SequenceClassification。
# Trainer：直接实现 正向传播、损失计算、参数更新
# TrainingArguments：超参数、实验设置
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments

from sklearn.preprocessing import LabelEncoder
from datasets import Dataset
import numpy as np

# 模型缓存目录：所有下载/缓存的数据都存到 作业 目录下（与要求.md 同目录）
# 使用原始字符串 r"..." 避免 Windows 反斜杠被当作转义字符（如 \w \a 等）
CACHE_DIR = r"G:\ai技能库\课程\Week4-Transfomer和BERT、GPT模型\作业"

# 加载和预处理数据
dataset_df = pd.read_csv("dataset.csv", sep="\t", header=None)

# 初始化 LabelEncoder，用于将文本标签转换为数字标签
lbl = LabelEncoder()
# 拟合数据并转换前5000个标签，得到数字标签
labels = lbl.fit_transform(dataset_df[1].values[:5000])
# 类别数量（动态获取，避免硬编码出错）
num_labels = len(lbl.classes_)
# 提取前5000个文本内容
texts = list(dataset_df[0].values[:5000])

# 分割数据为训练集和测试集
x_train, x_test, train_labels, test_labels = train_test_split(
    texts,             # 文本数据
    labels,            # 对应的数字标签
    test_size=0.2,     # 测试集比例为20%
    stratify=labels    # 确保训练集和测试集的标签分布一致
)


# 从预训练模型加载分词器和模型（从 HuggingFace Hub 下载并缓存到 CACHE_DIR）
# 第一次运行会联网下载 bert-base-chinese（约 400MB），之后从本地缓存加载
tokenizer = AutoTokenizer.from_pretrained("bert-base-chinese", cache_dir=CACHE_DIR)
model = AutoModelForSequenceClassification.from_pretrained(
    "bert-base-chinese", num_labels=num_labels, cache_dir=CACHE_DIR
)

# 使用分词器对训练集和测试集的文本进行编码
# truncation=True：如果文本过长则截断
# padding=True：对齐所有序列长度，填充到最长
# max_length=64：最大序列长度
train_encodings = tokenizer(x_train, truncation=True, padding=True, max_length=64)
test_encodings = tokenizer(x_test, truncation=True, padding=True, max_length=64)

# 将编码后的数据和标签转换为 Hugging Face `datasets` 库的 Dataset 对象
train_dataset = Dataset.from_dict({
    'input_ids': train_encodings['input_ids'],           # 文本的token ID
    'attention_mask': train_encodings['attention_mask'], # 注意力掩码
    'labels': train_labels                               # 对应的标签
})
test_dataset = Dataset.from_dict({
    'input_ids': test_encodings['input_ids'],
    'attention_mask': test_encodings['attention_mask'],
    'labels': test_labels
})


# 定义用于计算评估指标的函数
def compute_metrics(eval_pred):
    # eval_pred 是一个元组，包含模型预测的 logits 和真实的标签
    logits, labels = eval_pred
    # 找到 logits 中最大值的索引，即预测的类别
    predictions = np.argmax(logits, axis=-1)
    # 计算预测准确率并返回一个字典
    return {'accuracy': (predictions == labels).mean()}

# 配置训练参数
training_args = TrainingArguments(
    output_dir='./results',              # 训练输出目录，用于保存模型和状态
    num_train_epochs=3,                  # 训练的总轮数
    per_device_train_batch_size=16,      # 训练时每个设备（GPU/CPU）的批次大小
    per_device_eval_batch_size=16,       # 评估时每个设备的批次大小
    warmup_steps=100,                    # 学习率预热的步数，有助于稳定训练， step 定义为 一次 正向传播 + 参数更新
    weight_decay=0.01,                   # 权重衰减，用于防止过拟合
    logging_steps=100,                   # 每隔100步记录一次日志
    eval_strategy="epoch",               # 每训练完一个 epoch 进行一次评估
    save_strategy="no",                  # 训练过程中不保存 checkpoint，避免 load_best_model_at_end 重新加载时
                                          # 因 LayerNorm 参数命名(gamma/beta vs weight/bias)映射缺失导致 BERT 主干归一化层被随机初始化
)

# 实例化 Trainer 简化模型训练代码
trainer = Trainer(
    model=model,                         # 要训练的模型
    args=training_args,                  # 训练参数
    train_dataset=train_dataset,         # 训练数据集
    eval_dataset=test_dataset,           # 评估数据集
    compute_metrics=compute_metrics,     # 用于计算评估指标的函数
)

# 深度学习训练过程，数据获取，epoch batch 循环，梯度计算 + 参数更新

# 开始训练模型
trainer.train()
# 在测试集上进行最终评估
trainer.evaluate()

# trainer 是比较简单，适合训练过程比较规范化的模型
# 如果我要定制化训练过程，trainer无法满足