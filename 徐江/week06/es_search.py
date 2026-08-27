"""
Elasticsearch 检索工具类 + RAG 演示
功能：连接本地 ES，封装 全文检索 / 条件过滤 / 向量检索（kNN）/ 混合检索（手动RRF）
适配：Elasticsearch 9.x + IK 分词器 + BAAI/bge-small-zh-v1.5
"""

import os
import random
import math
from typing import List, Dict, Any, Optional
import time
# 离线模式（已有本地模型时启用）
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk


# ==================== 向量编码器 ====================
class LocalEmbedder:
    """本地向量编码器 - BAAI/bge-small-zh-v1.5"""

    def __init__(self, model_path: str = None, vector_dim: int = 512):
        """
        初始化本地编码模型
        Args:
            model_path: 模型本地路径（可选，默认从默认路径加载）
            vector_dim: 向量维度（bge-small-zh-v1.5 为 512）
        """
        self.vector_dim = vector_dim
        self._model = None
        self._model_path = model_path

    def load_model(self):
        """加载本地模型"""
        if self._model is not None:
            return self._model

        try:
            from sentence_transformers import SentenceTransformer

            if self._model_path:
                model_path = self._model_path
            else:
                # 尝试常见本地模型路径
                possible_paths = [
                    r'E:\modelscope_cache\models\BAAI--bge-small-zh-v1.5\snapshots\master',
                    r'E:\models\BAAI--bge-small-zh-v1.5',
                    r'./models\BAAI--bge-small-zh-v1.5',
                ]
                model_path = None
                for p in possible_paths:
                    if os.path.exists(p):
                        model_path = p
                        break

                if not model_path:
                    raise FileNotFoundError("未找到本地模型，请指定 model_path")

            self._model = SentenceTransformer(model_path)
            print(f"✅ 模型加载成功: {model_path}")
            return self._model

        except Exception as e:
            print(f"⚠️ 模型加载失败: {e}")
            return None

    def encode(self, texts: str | List[str], normalize: bool = True) -> List[List[float]]:
        """
        将文本编码为向量
        Args:
            texts: 单个文本或文本列表
            normalize: 是否归一化向量
        Returns:
            向量列表
        """
        model = self.load_model()
        if model is None:
            # 模型加载失败，使用随机向量
            print("模型加载失败！")
            if isinstance(texts, str):
                texts = [texts]
            return [self._random_vector() for _ in texts]

        embeddings = model.encode(texts, normalize_embeddings=normalize)
        return embeddings.tolist() if hasattr(embeddings, 'tolist') else embeddings

    def _random_vector(self) -> List[float]:
        """生成随机单位向量（演示用）"""
        vec = [random.uniform(-1, 1) for _ in range(self.vector_dim)]
        norm = math.sqrt(sum(x * x for x in vec))
        return [x / norm for x in vec]


# ==================== ES 检索工具类 ====================
class ESSearcher:
    """ES 检索封装类 - 自动连接本地ES，无需认证"""

    def __init__(
        self,
        hosts: str = "http://localhost:9200",
        request_timeout: int = 30,
    ):
        """
        初始化 ES 连接器
        Args:
            hosts: ES 主机地址（默认本地9200）
            request_timeout: 请求超时时间（秒）
        """
        self.hosts = hosts
        self.request_timeout = request_timeout
        self._client: Optional[Elasticsearch] = None

    def connect(self) -> Elasticsearch:
        """连接本地 Elasticsearch"""
        try:
            self._client = Elasticsearch(
                self.hosts,
                request_timeout=self.request_timeout,
                retry_on_timeout=True,
                max_retries=3,
            )
            if not self._client.ping():
                raise ConnectionError("ES ping 失败，请检查服务是否启动")
            info = self._client.info()
            print(f"✅ ES 连接成功！版本: {info['version']['number']}")
            return self._client
        except Exception as e:
            raise RuntimeError(f"❌ 连接 ES 失败：{e}")

    @property
    def client(self) -> Elasticsearch:
        """获取 ES 客户端（延迟连接）"""
        if self._client is None:
            self.connect()
        return self._client

    def create_index(
        self,
        index_name: str,
        vector_dim: int = 512,
        text_field: str = "content",
    ) -> bool:
        """创建索引（带向量字段）"""
        if self.client.indices.exists(index=index_name):
            print(f"📦 索引 '{index_name}' 已存在")
            return True

        mappings = {
            "properties": {
                text_field: {
                    "type": "text",
                    "analyzer": "ik_max_word",
                    "search_analyzer": "ik_smart",
                },
                "title": {"type": "text", "analyzer": "ik_max_word"},
                "category": {"type": "keyword"},
                "embedding": {
                    "type": "dense_vector",
                    "dims": vector_dim,
                    "index": True,
                    "similarity": "cosine",
                },
            }
        }
        try:
            self.client.indices.create(index=index_name, mappings=mappings)
            print(f"📦 索引 '{index_name}' 创建成功（向量维度={vector_dim}）")
        except Exception as e:
            raise RuntimeError(f"❌ 创建索引失败：{e}")
        return True

    def delete_index(self, index_name: str):
        """删除索引"""
        self.client.indices.delete(index=index_name, ignore=[400, 404])
        print(f"🗑️ 索引 '{index_name}' 已删除")

    def bulk_index(self, index_name: str, docs: List[Dict[str, Any]]) -> int:
        """批量写入文档"""
        if not docs:
            return 0
        actions = [{"_index": index_name, "_source": doc} for doc in docs]
        try:
            success, errors = bulk(
                self.client,
                actions,
                raise_on_error=False,
                raise_on_exception=False,
            )
        except Exception as e:
            raise RuntimeError(f"❌ 批量写入异常：{e}")

        print(f"📥 批量写入完成：成功 {success} 条，失败 {len(errors)} 条")
        if errors:
            print(f"   失败详情(前3条): {errors[:3]}")
        return success

    def full_text_search(
        self,
        index_name: str,
        query_text: str,
        text_field: str = "content",
        top_k: int = 10,
        highlight: bool = True,
    ) -> List[Dict]:
        """全文检索"""
        body = {
            "size": top_k,
            "query": {
                "multi_match": {
                    "query": query_text,
                    "fields": [text_field, "title"],
                    "type": "best_fields",
                }
            },
        }
        if highlight:
            body["highlight"] = {
                "fields": {text_field: {}, "title": {}},
                "pre_tags": ["<em>"],
                "post_tags": ["</em>"],
            }
        resp = self.client.search(index=index_name, body=body)
        return self._parse_hits(resp)

    def filter_search(
        self,
        index_name: str,
        filter_terms: Dict[str, Any] = None,
        top_k: int = 10,
    ) -> List[Dict]:
        """条件过滤检索"""
        if filter_terms is None:
            filter_terms = {}
        body = {
            "size": top_k,
            "query": {
                "bool": {
                    "filter": [{"term": {k: v}} for k, v in filter_terms.items()]
                }
            },
        }
        resp = self.client.search(index=index_name, body=body)
        return self._parse_hits(resp)

    def vector_search(
        self,
        index_name: str,
        query_vector: List[float],
        vector_field: str = "embedding",
        top_k: int = 10,
    ) -> List[Dict]:
        """向量检索 (kNN)"""
        body = {
            "size": top_k,
            "knn": {
                "field": vector_field,
                "query_vector": query_vector,
                "k": top_k,
                "num_candidates": max(top_k * 2, 50),
            },
        }
        resp = self.client.search(index=index_name, body=body)
        return self._parse_hits(resp)

    def hybrid_search(
        self,
        index_name: str,
        query_text: str,
        query_vector: List[float],
        text_field: str = "content",
        vector_field: str = "embedding",
        top_k: int = 10,
        rrf_k: int = 60,
    ) -> List[Dict]:
        """混合检索 - 手动 RRF 融合"""
        # 并行执行两种检索
        text_hits = self.full_text_search(
            index_name, query_text, text_field, top_k=top_k, highlight=False
        )
        vec_hits = self.vector_search(
            index_name, query_vector, vector_field, top_k=top_k
        )

        # RRF 融合
        fused = {}
        for rank, hit in enumerate(text_hits, 1):
            fused[hit["_id"]] = fused.get(hit["_id"], 0) + 1.0 / (rrf_k + rank)
        for rank, hit in enumerate(vec_hits, 1):
            fused[hit["_id"]] = fused.get(hit["_id"], 0) + 1.0 / (rrf_k + rank)

        # 合并结果
        id_to_source = {h["_id"]: h["_source"] for h in text_hits + vec_hits}
        results = [
            {"_id": did, "_score": s, "_source": id_to_source[did]}
            for did, s in fused.items()
        ]
        results.sort(key=lambda x: x["_score"], reverse=True)
        return results[:top_k]

    def _parse_hits(self, resp: Dict) -> List[Dict]:
        """解析搜索结果"""
        results = []
        for hit in resp.get("hits", {}).get("hits", []):
            item = {
                "_id": hit.get("_id"),
                "_score": hit.get("_score"),
                "_source": hit.get("_source", {}),
            }
            if "highlight" in hit:
                item["highlight"] = hit["highlight"]
            results.append(item)
        return results


# ==================== 便捷函数 ====================
def create_searcher() -> ESSearcher:
    """创建并连接 ES 检索器"""
    searcher = ESSearcher()
    searcher.connect()
    return searcher


def create_embedder(
    model_path: str = None,
    vector_dim: int = 512,
) -> LocalEmbedder:
    """创建本地向量化编码器"""
    return LocalEmbedder(model_path=model_path, vector_dim=vector_dim)


# ==================== 演示 ====================
if __name__ == "__main__":
    # 配置
    ES_HOST = "http://localhost:9200"
    INDEX_NAME = "qa_demo"
    VECTOR_DIM = 512  # bge-small-zh-v1.5 为 512 维

    # 可选：指定本地模型路径
    MODEL_PATH = r'E:\modelscope_cache\models\BAAI--bge-small-zh-v1.5\snapshots\master'

    # 1. 初始化组件（自动连接本地ES，无需认证）
    print("=" * 50)
    print("1. 连接 Elasticsearch...")
    searcher = ESSearcher(hosts=ES_HOST)
    searcher.connect()

    print("\n2. 加载本地向量模型...")
    embedder = LocalEmbedder(model_path=MODEL_PATH, vector_dim=VECTOR_DIM)

    # 2. 准备测试数据
    raw_docs = [
        {
            "title": "什么是 RAG",
            "content": "RAG 是检索增强生成技术，结合检索与大模型生成，提升回答准确性。",
            "category": "tech",
        },
        {
            "title": "Elasticsearch 简介",
            "content": "Elasticsearch 是分布式搜索引擎，支持全文检索与向量检索。",
            "category": "tech",
        },
        {
            "title": "今日天气",
            "content": "今天晴天，气温25度，适合出门散步。",
            "category": "life",
        },
        {
            "title": "Python 入门",
            "content": "Python 是一种简单易学的编程语言，适合数据分析与AI开发。",
            "category": "tech",
        },
    ]

    # 3. 生成向量
    print("\n3. 生成文档向量...")
    doc_texts = [f"{d['title']} {d['content']}" for d in raw_docs]
    doc_embeddings = embedder.encode(doc_texts)

    # 4. 组装文档（添加向量字段）
    docs_with_embedding = []
    for doc, emb in zip(raw_docs, doc_embeddings):
        d = doc.copy()
        d["embedding"] = emb
        docs_with_embedding.append(d)

    # # 检查索引是否存在，如果不存在则创建
    # if searcher.client.indices.exists(index=INDEX_NAME):
    #     print(f"旧索引 '{INDEX_NAME}' 已删除。")
    # else:
    #     searcher.create_index(INDEX_NAME, vector_dim=VECTOR_DIM)
    #     searcher.bulk_index(INDEX_NAME, docs_with_embedding)

    # 5. 创建索引并写入
    print("\n4. 创建索引并写入数据...")
    searcher.delete_index(INDEX_NAME)  # 重建索引
    searcher.create_index(INDEX_NAME, vector_dim=VECTOR_DIM)
    searcher.bulk_index(INDEX_NAME, docs_with_embedding)

    #刷新索引，等待1s
    searcher.client.indices.refresh(index=INDEX_NAME)
    time.sleep(1)  # 等待索引刷新
    # 6. 执行查询
    query_text = "RAG技术"
    print(f"\n5. 执行查询: '{query_text}'")
    query_vector = embedder.encode(query_text)

    # 5.1 全文检索
    print("\n" + "=" * 50)
    print("【全文检索】")
    for r in searcher.full_text_search(INDEX_NAME, query_text, top_k=3):
        print(f"  score={r['_score']:.2f} | {r['_source'].get('title')}")

    # 5.2 条件过滤
    print("\n【条件过滤 - category:tech】")
    for r in searcher.filter_search(INDEX_NAME, {"category": "tech"}, top_k=3):
        print(f"  score={r['_score']} | {r['_source'].get('title')} | {r['_source'].get('category')}")

    # 5.3 向量检索
    print("\n【向量检索】")
    for r in searcher.vector_search(INDEX_NAME, query_vector, top_k=3):
        print(f"  score={r['_score']:.2f} | {r['_source'].get('title')}")

    # 5.4 混合检索
    print("\n【混合检索 (RRF)】")
    for r in searcher.hybrid_search(INDEX_NAME, query_text, query_vector, top_k=3):
        print(f"  score={r['_score']:.4f} | {r['_source'].get('title')}")

    print("\n" + "=" * 50)
    print("🎉 演示完成！")