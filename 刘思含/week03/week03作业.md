# 作业一

### 问题1：langchain 工具调用 和 llm function call 有什么区别？

LLM Function call（function calling） 是直接调用某一家的模型API，复杂度不高，可以应付简单的项目

langchain（tool calling） 是复杂，需要调用多个工具，后期可以更换底层模型，更灵活

二者应该在开发环境中可以交替使用

### 问题2：langchain 工具调用 的 速度是受到什么影响？

受到工具调用和模型调用速度影响，不过可以使用异步来优化

## 02_Model工具调用.py运行流程

### 流程图

	用户输入 → Executor启动循环
          ↓
    Agent（模型）推理
          ↓
    有 tool_calls？ ──是──→ 执行工具 → 观察结果追加到 scratchpad → 回到 Agent 推理
          ↓ 否
    生成最终回答 → 返回给用户


# 作业二

## 意图识别流程图


                                  用户请求                                       
              {"request_id": "123","request_text": "怎么重置密码？"}                   
                                      │
                                      ▼

                           FastAPI 网关 (main.py)
                         POST /v1/text-cls/{model}                    
                        1. 记录请求日志 logger.info()                
                        2. 记录开始时间 start_time = time.time()       
                        3. try-catch 错误处理                         
                        4. 计算耗时 classify_time                    
                                      │
                                      ▼
                    ┌─────────────────┴─────────────────┐
                    │                                   │
                    ▼                                   ▼
                 regex 模型                        tfidf 模型
          (regex_rule.py)                        (tfidf_ml.py)
          预定义规则匹配：                        1. 加载预处理模型 
          - 包含"怎么"→操作                       2. 文本向量化     
          - 包含"为什么"→                        3. SVM/NaiveBayes
            原因类                                   预测          
          - 正则表达式库                         4. 返回意图标签
                  │                                  │
                  │                                  │

            bert 模型                             gpt 模型
           (bert.py)                             (prompt.py)
           1. 文本分词                           1. 构建 Prompt 
           2. BERT 编码                          2. 调用 LLM API
           3. 全连接层分类                       3. 解析返回结果
           4. Softmax 输出                       4. 提取意图标签
                |                                   |
                │                                   │ 
                └─────────────┬─────────────────────┘
                              │
                              ▼
                            返回统一响应
                          TextClassifyResponse                                

      {
        "request_id": "123",
        "request_text": "怎么重置密码？",
        "classify_result": "operation_guide",  ← 分类结果
        "classify_time": 0.125,                ← 耗时 (秒)
        "error_msg": "ok"                      ← 错误信息
      }
