from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer

ELASTICSEARCH_URL = "http://localhost:9200"
es_client = Elasticsearch(ELASTICSEARCH_URL)
if es_client.ping():
    print("Elasticsearch OK!")
else:
    print("Elasticsearch unavailable, please check!")

print("开始加载编码模型")
model = SentenceTransformer('../../modelscope/bge/BAAI/bge-small-zh-v1.5')
print("编码模型加载完成")

index_name = "good_books"
mapping = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    },
    "mappings": {
        "properties": {
            "title": {
                "type": "text",
                "analyzer": "ik_max_word",
                "search_analyzer": "ik_smart"
            },
            "content": {
                "type": "text",
                "analyzer": "ik_max_word",
                "search_analyzer": "ik_smart"
            },
            "content_vector": {
                    "type": "dense_vector",
                    "dims": 512,  # 根据模型的输出维度来设置
                    "index": True,
                    "similarity": "cosine"
            },
            "tags": {"type": "keyword"},
            "author": {"type": "keyword"},
            "price": {"type": "float"}
        }
    }
}

if  es_client.indices.exists(index=index_name):
    es_client.indices.delete(index=index_name)
es_client.indices.create(index=index_name, body=mapping)


documents = [
      {
        "title": "三体：黑暗森林",
        "content": "庞大的宇宙史诗，讲述了人类文明与三体文明之间的生死博弈，以及黑暗森林法则带来的深刻震撼。",
        "tags": ["科幻", "宇宙", "经典", "刘慈欣"],
        "author": "刘慈欣",
        "price": 39.99
      },
      {
        "title": "深度学习入门：基于Python的理论与实现",
        "content": "一本非常好的深度学习入门实践书，从零开始用Python实现神经网络，通俗易懂，代码清晰。",
        "tags": ["技术", "编程", "AI", "入门", "教材"],
        "author": "斋藤康毅",
        "price": 58.00
      },
      {
        "title": "百年孤独",
        "content": "魔幻现实主义经典之作，讲述了布恩迪亚家族七代人的传奇故事，折射出整个拉丁美洲的历史变迁。",
        "tags": ["文学", "经典", "魔幻", "诺贝尔文学奖"],
        "author": "加西亚·马尔克斯",
        "price": 55.00
      },
      {
        "title": "人类群星闪耀时",
        "content": "奥地利作家茨威格的传记名作，描绘了拿破仑、歌德、列宁等历史伟人决定世界命运的14个瞬间。",
        "tags": ["历史", "传记", "经典"],
        "author": "斯蒂芬·茨威格",
        "price": 28.00
      },
      {
        "title": "算法导论（第3版）",
        "content": "计算机科学领域最权威的算法教材之一，系统论述了算法设计与分析的核心知识，是程序员进阶的必读经典。",
        "tags": ["技术", "计算机", "算法", "教材"],
        "author": "Thomas H. Cormen",
        "price": 128.00
      },
      {
        "title": "人间失格",
        "content": "太宰治半自传体的绝笔之作，以极致的颓废与敏感，描绘了主角大庭叶藏在社会边缘的挣扎与沉沦。",
        "tags": ["文学", "日本文学", "经典"],
        "author": "太宰治",
        "price": 25.00
      },
      {
        "title": "刻意练习：如何从新手到大师",
        "content": "推翻了‘天赋论’，通过大量科学研究和实例，证明了任何人都可以通过‘刻意练习’在特定领域获得卓越成就。",
        "tags": ["心理学", "成长", "技能", "学习方法"],
        "author": "安德斯·埃里克森",
        "price": 45.00
      }
]
for doc in documents:
    doc["content_vector"] = model.encode(doc["content"]).tolist()
    es_client.index(index= index_name, document=doc)
    print(f"{doc["title"]} 已入库")

es_client.indices.refresh(index=index_name)

def search_docs(query):
    response = es_client.search(index=index_name, body=query)
    for hit in response['hits']['hits']:
        if '_source' in hit and hit['_source']:
            print(f"得分：{hit['_score']}, 书籍名称: {hit['_source']['title']}")
        elif 'fields' in hit:
            print(f"得分：{hit['_score']}, 书籍名称: {hit['fields']['title'][0]}")



query1 = {
    "query": {
        "match":{
            "tags": "技术"
        }
    }
}
query2 = {
    "query": {
        "bool": {
            "must": {
                "match_all": {}
            },
            "filter": [
                {"term": {"tags": "教材"}},
                {"range": {"price": {"lt": 60}}}
            ]
        }
    }
}
query_vector = model.encode("关于深度学习").tolist()
query3 = {
    "knn": {
            "field": "content_vector",
            "query_vector": query_vector,
            "k": 3,
            "num_candidates": 7
        },
    "fields": ["title"],
    "_source": False  # 不返回整个文档源
}
print("1...")
search_docs(query1)
print("2...")
search_docs(query2)
print("3...")
search_docs(query3)









