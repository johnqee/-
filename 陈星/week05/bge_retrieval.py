# -*- coding: utf-8 -*-
"""
文本检索作业：使用 sentence-transformers + BAAI/bge-small-zh-v1.5 做语义检索（不使用 ES）
"""
from sentence_transformers import SentenceTransformer

# 1. 加载本地 bge 模型（已通过 modelscope 下载到本地目录）
model_path = r'BAAI/bge-small-zh-v1.5'
model = SentenceTransformer(model_path)

# 2. 待检索的查询文本
query = "我今天很开心"

# 3. 数据库文本（候选文档库）
corpus = [
    "我喜欢机器学习",
    "我喜欢深度学习",
    "我今天心情很不错",
]

# 4. bge 模型官方推荐：检索查询语句需加指令前缀
QUERY_INSTRUCTION = "为这个句子生成表示以用于检索相关文章："

# 5. 编码：query 加指令前缀，corpus 不加；normalize_embeddings 归一化后点积即余弦相似度
query_emb = model.encode([QUERY_INSTRUCTION + query], normalize_embeddings=True)
corpus_emb = model.encode(corpus, normalize_embeddings=True)

# 6. 计算相似度（归一化向量点积 = 余弦相似度）
scores = (corpus_emb @ query_emb.T).squeeze()

# 7. 按相似度降序排序输出
results = sorted(zip(corpus, scores.tolist()), key=lambda x: x[1], reverse=True)

print(f"查询文本：{query}\n")
print("=" * 50)
print("检索结果（按相似度从高到低排序）：")
print("=" * 50)
for i, (text, score) in enumerate(results, 1):
    print(f"第 {i} 名  | 相似度: {score:.4f}  |  {text}")

print("\n最佳匹配：", results[0][0])
