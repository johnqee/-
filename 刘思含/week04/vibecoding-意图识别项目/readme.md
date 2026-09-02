# 简易意图识别系统 (Intent Classification)

## 项目概述

一个**轻量级意图识别**（文本分类）系统，可应用于语音助手、智能客服等场景。简化为两条技术路线（正则 / TF-IDF+SVM），**无需 GPU、无需预训练模型**，自带小数据集，开箱即用。

**典型场景：**
- "帮我播放周杰伦的歌曲" → `Music-Play`
- "把空调调到26度" → `HomeAppliance-Control`
- "今天天气怎么样" → `Weather-Query`

---

## 技术路线

| 路线 | 精度 | 速度 | 训练 | GPU | 定位 |
|------|------|------|------|-----|------|
| 正则表达式 (Regex) | ~70% | ~0.1ms | 无需 | 无需 | 快速关键词匹配 |
| TF-IDF + LinearSVM | ~85% | ~2ms | 需要 | 无需 | 轻量级主力 |

> 与父项目的区别：去掉了 BERT 微调和 LLM Few-shot 两条路线，专注最小可运行的意图识别闭环。

---

## 项目结构

```
意图识别/
├── main.py                    # API 服务入口 (FastAPI)
├── data_schema.py             # 请求/响应数据模型 (Pydantic)
├── config.py                  # 全局配置 (规则、类别、路径)
├── logger.py                  # 日志配置
├── model/                     # 模型推理引擎（策略模式）
│   ├── regex_rule.py          # 正则规则引擎
│   └── tfidf_ml.py            # TF-IDF + SVM 引擎
├── training_code/             # 模型训练脚本
│   └── train_tfidf.py         # TF-IDF + SVM 训练
├── assets/                    # 资源文件
│   ├── dataset/               # 数据集 & 停用词表
│   │   ├── dataset.csv
│   │   └── baidu_stopwords.txt
│   └── weights/               # 训练产出的模型权重（训练后生成）
└── test/                      # 测试数据
    └── data.json
```

---

## 快速开始

### 1. 环境准备

```bash
# Python 3.9+
pip install fastapi uvicorn scikit-learn jieba pandas joblib
```

### 2. 模型训练

```bash
cd 意图识别
python training_code/train_tfidf.py
# 产出 assets/weights/tfidf_ml.pkl
```

### 3. 启动 API 服务

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 4. 调用接口

```bash
# 正则接口
curl -X POST 'http://0.0.0.0:8000/v1/text-cls/regex' \
  -H 'Content-Type: application/json' \
  -d '{"request_id": "001", "request_text": "帮我播放周杰伦的歌曲"}'

# TF-IDF 接口（支持批量）
curl -X POST 'http://0.0.0.0:8000/v1/text-cls/tfidf' \
  -H 'Content-Type: application/json' \
  -d '{"request_id": "002", "request_text": ["打开空调", "今天天气怎么样"]}'
```

---

## API 接口

### 端点

| 端点 | 模型 | 说明 |
|------|------|------|
| `POST /v1/text-cls/regex` | 正则规则 | 关键词快速匹配 |
| `POST /v1/text-cls/tfidf` | TF-IDF+SVM | 轻量级统计分类 |

### 请求格式

```json
{
  "request_id": "可选，方便调试",
  "request_text": "字符串 或 字符串列表"
}
```

### 响应格式

```json
{
  "request_id": "001",
  "request_text": "帮我播放周杰伦的歌曲",
  "classify_result": ["Music-Play"],
  "classify_time": 0.023,
  "error_msg": "ok"
}
```

### 支持分类类别

- `Music-Play`（音乐播放）
- `Weather-Query`（天气查询）
- `HomeAppliance-Control`（家电控制）
- `Alarm-Update`（闹钟设置）
- `Other`（其他）
