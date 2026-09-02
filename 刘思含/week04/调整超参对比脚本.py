import os
import pandas as pd
import torch
from sklearn.model_selection import train_test_split
# 本脚本：作业1的超参对比实验
#   固定其他设置不变，只改 learning_rate，跑三组对比模型精度。
#   每组都重新从预训练权重加载模型，保证公平起点；固定随机种子，保证差异只来自超参。
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments

from sklearn.preprocessing import LabelEncoder
from datasets import Dataset
import numpy as np

# 模型缓存目录（与 10.1 保持一致）
CACHE_DIR = r"G:\ai技能库\课程\Week4-Transfomer和BERT、GPT模型\作业"

# 固定随机种子，保证三组实验除了 learning_rate 之外的一切都相同，差异只能来自超参
# 这样对比才有意义
def set_seed(seed=42):
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

# ========== 1. 数据加载与预处理（三组共用同一份数据，只算一次） ==========
dataset_df = pd.read_csv("dataset.csv", sep="\t", header=None)

lbl = LabelEncoder()
labels = lbl.fit_transform(dataset_df[1].values[:5000])
num_labels = len(lbl.classes_)
texts = list(dataset_df[0].values[:5000])

x_train, x_test, train_labels, test_labels = train_test_split(
    texts, labels, test_size=0.2, stratify=labels
)

# 分词器三组共用
tokenizer = AutoTokenizer.from_pretrained("bert-base-chinese", cache_dir=CACHE_DIR)

# 编码（三组共用）
train_encodings = tokenizer(x_train, truncation=True, padding=True, max_length=64)
test_encodings = tokenizer(x_test, truncation=True, padding=True, max_length=64)

train_dataset = Dataset.from_dict({
    'input_ids': train_encodings['input_ids'],
    'attention_mask': train_encodings['attention_mask'],
    'labels': train_labels
})
test_dataset = Dataset.from_dict({
    'input_ids': test_encodings['input_ids'],
    'attention_mask': test_encodings['attention_mask'],
    'labels': test_labels
})

# ========== 2. 评估指标函数 ==========
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    return {'accuracy': (predictions == labels).mean()}

# ========== 3. 三组待对比的学习率 ==========
# 5e-5 是 Trainer 默认值；2e-5 更小更稳；1e-4 更大可能更快收敛也更可能发散
learning_rates = [
    {"lr": 2e-5, "name": "小学习率"},
    {"lr": 5e-5, "name": "默认学习率"},
    {"lr": 1e-4, "name": "大学习率"},
]

results = []  # 收集每组的最终准确率，最后打印对比表

print("=" * 70)
print("超参对比实验：固定 batch_size=16、epochs=3，只改 learning_rate")
print("=" * 70)

for i, cfg in enumerate(learning_rates, 1):
    print(f"\n{'#' * 70}")
    print(f"# 第 {i} 组 / 共 {len(learning_rates)} 组：{cfg['name']}  learning_rate={cfg['lr']}")
    print(f"{'#' * 70}")

    # 关键：每组都重置随机种子 + 重新加载预训练权重
    #   - 重置种子保证数据顺序、dropout、分类头初始化完全一致
    #   - 重新 from_pretrained 保证都从同一份 bert-base-chinese 起点训练
    #   这样三组之间唯一差别就是 learning_rate，对比才有说服力
    set_seed(42)
    model = AutoModelForSequenceClassification.from_pretrained(
        "bert-base-chinese", num_labels=num_labels, cache_dir=CACHE_DIR
    )

    training_args = TrainingArguments(
        output_dir=f'./results_lr_{cfg["lr"]}',   # 每组单独输出目录，互不干扰
        learning_rate=cfg["lr"],                  # ★ 本次实验唯一变量
        num_train_epochs=3,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        warmup_steps=100,
        weight_decay=0.01,
        logging_steps=100,
        eval_strategy="epoch",
        save_strategy="no",                       # 不保存checkpoint，避开重载bug
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=test_dataset,
        compute_metrics=compute_metrics,
    )

    # 训练并在测试集上做最终评估
    train_result = trainer.train()
    eval_result = trainer.evaluate()

    # 提取最终准确率
    final_acc = eval_result.get("eval_accuracy", float('nan'))
    results.append({
        "name": cfg["name"],
        "learning_rate": cfg["lr"],
        "accuracy": final_acc,
    })

    # 及时释放显存，避免三组累加爆显存
    del model, trainer
    torch.cuda.empty_cache()

# ========== 4. 打印对比表 ==========
print("\n")
print("=" * 70)
print("【对比结果】固定 batch_size=16、epochs=3，不同 learning_rate 的准确率")
print("=" * 70)
print(f"{'组别':<14}{'learning_rate':<18}{'最终准确率':<14}")
print("-" * 46)
for r in results:
    print(f"{r['name']:<14}{r['learning_rate']:<18}{r['accuracy']:.4f}")
print("-" * 46)

best = max(results, key=lambda x: x["accuracy"])
print(f"\n最佳配置：{best['name']} (learning_rate={best['learning_rate']})，准确率={best['accuracy']:.4f}")
print("=" * 70)