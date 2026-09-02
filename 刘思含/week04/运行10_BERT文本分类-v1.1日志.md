```
次数	数据量	warmup	epochs	最佳 acc	备注
第一次	500	    500	      4	     0.79	LayerNorm 被重载 bug 损坏
第二次	500	    500	      4	     0.81	模型完好
第三次	5000	500	      4	     0.979	epoch 3 峰值,epoch 4 过拟合回落
第四次	5000	100	      3	     0.976	恰停峰值,无过拟合,配置自洽
```


PS G:\ai技能库\课程\Week4-Transfomer和BERT、GPT模型\Week04> & E:\Conda\envs\course\python.exe g:/ai技能库/课程/Week4-Transfomer和BERT、GPT模型/Week04/10.1_BERT文本分类.py
Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
Loading weights: 100%|█████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 199/199 [00:00<00:00, 11600.65it/s]
[transformers] BertForSequenceClassification LOAD REPORT from: bert-base-chinese
Key                                        | Status     | 
-------------------------------------------+------------+-
cls.predictions.bias                       | UNEXPECTED | 
cls.seq_relationship.weight                | UNEXPECTED | 
cls.predictions.transform.LayerNorm.bias   | UNEXPECTED | 
cls.predictions.transform.LayerNorm.weight | UNEXPECTED | 
cls.seq_relationship.bias                  | UNEXPECTED | 
cls.predictions.transform.dense.bias       | UNEXPECTED | 
cls.predictions.transform.dense.weight     | UNEXPECTED | 
classifier.bias                            | MISSING    | 
classifier.weight                          | MISSING    | 

Notes:
- UNEXPECTED:   can be ignored when loading from different task/architecture; not ok if you expect identical arch.
- MISSING:      those params were newly initialized because missing from the checkpoint. Consider training on your downstream task.
[transformers] `logging_dir` is deprecated and will be removed in v5.2. Please set `TENSORBOARD_LOGGING_DIR` instead.
{'eval_loss': '2.409', 'eval_accuracy': '0.15', 'eval_runtime': '0.0689', 'eval_samples_per_second': '1450', 'eval_steps_per_second': '101.5', 'epoch': '1'}                        
Writing model shards: 100%|███████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00,  2.37it/s]
{'eval_loss': '2.236', 'eval_accuracy': '0.24', 'eval_runtime': '0.0614', 'eval_samples_per_second': '1629', 'eval_steps_per_second': '114', 'epoch': '2'}                          
Writing model shards: 100%|███████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00,  2.65it/s]
{'eval_loss': '1.931', 'eval_accuracy': '0.47', 'eval_runtime': '0.052', 'eval_samples_per_second': '1923', 'eval_steps_per_second': '134.6', 'epoch': '3'}                         
Writing model shards: 100%|███████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00,  2.64it/s]
{'loss': '2.155', 'grad_norm': '9.883', 'learning_rate': '9.9e-06', 'epoch': '4'}                                                                                                   
{'eval_loss': '1.495', 'eval_accuracy': '0.79', 'eval_runtime': '0.0552', 'eval_samples_per_second': '1812', 'eval_steps_per_second': '126.8', 'epoch': '4'}                        
Writing model shards: 100%|███████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00,  2.46it/s]
{'train_runtime': '9.115', 'train_samples_per_second': '175.5', 'train_steps_per_second': '10.97', 'train_loss': '2.155', 'epoch': '4'}                                             
100%|█████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 100/100 [00:09<00:00, 19.06it/s][transformers] There were missing keys in the checkpoint model loaded: ['bert.embeddings.LayerNorm.weight', 'bert.embeddings.LayerNorm.bias', 'bert.encoder.layer.0.attention.output.LayerNorm.weight', 'bert.encoder.layer.0.attention.output.LayerNorm.bias', 'bert.encoder.layer.0.output.LayerNorm.weight', 'bert.encoder.layer.0.output.LayerNorm.bias', 'bert.encoder.layer.1.attention.output.LayerNorm.weight', 'bert.encoder.layer.1.attention.output.LayerNorm.bias', 'bert.encoder.layer.1.output.LayerNorm.weight', 'bert.encoder.layer.1.output.LayerNorm.bias', 'bert.encoder.layer.2.attention.output.LayerNorm.weight', 'bert.encoder.layer.2.attention.output.LayerNorm.bias', 'bert.encoder.layer.2.output.LayerNorm.weight', 'bert.encoder.layer.2.output.LayerNorm.bias', 'bert.encoder.layer.3.attention.output.LayerNorm.weight', 'bert.encoder.layer.3.attention.output.LayerNorm.bias', 'bert.encoder.layer.3.output.LayerNorm.weight', 'bert.encoder.layer.3.output.LayerNorm.bias', 'bert.encoder.layer.4.attention.output.LayerNorm.weight', 'bert.encoder.layer.4.attention.output.LayerNorm.bias', 'bert.encoder.layer.4.output.LayerNorm.weight', 'bert.encoder.layer.4.output.LayerNorm.bias', 'bert.encoder.layer.5.attention.output.LayerNorm.weight', 'bert.encoder.layer.5.attention.output.LayerNorm.bias', 'bert.encoder.layer.5.output.LayerNorm.weight', 'bert.encoder.layer.5.output.LayerNorm.bias', 'bert.encoder.layer.6.attention.output.LayerNorm.weight', 'bert.encoder.layer.6.attention.output.LayerNorm.bias', 'bert.encoder.layer.6.output.LayerNorm.weight', 'bert.encoder.layer.6.output.LayerNorm.bias', 'bert.encoder.layer.7.attention.output.LayerNorm.weight', 'bert.encoder.layer.7.attention.output.LayerNorm.bias', 'bert.encoder.layer.7.output.LayerNorm.weight', 'bert.encoder.layer.7.output.LayerNorm.bias', 'bert.encoder.layer.8.attention.output.LayerNorm.weight', 'bert.encoder.layer.8.attention.output.LayerNorm.bias', 'bert.encoder.layer.8.output.LayerNorm.weight', 'bert.encoder.layer.8.output.LayerNorm.bias', 'bert.encoder.layer.9.attention.output.LayerNorm.weight', 'bert.encoder.layer.9.attention.output.LayerNorm.bias', 'bert.encoder.layer.9.output.LayerNorm.weight', 'bert.encoder.layer.9.output.LayerNorm.bias', 'bert.encoder.layer.10.attention.output.LayerNorm.weight', 'bert.encoder.layer.10.attention.output.LayerNorm.bias', 'bert.encoder.layer.10.output.LayerNorm.weight', 'bert.encoder.layer.10.output.LayerNorm.bias', 'bert.encoder.layer.11.attention.output.LayerNorm.weight', 'bert.encoder.layer.11.attention.output.LayerNorm.bias', 'bert.encoder.layer.11.output.LayerNorm.weight', 'bert.encoder.layer.11.output.LayerNorm.bias'].
[transformers] There were unexpected keys in the checkpoint model loaded: ['bert.embeddings.LayerNorm.beta', 'bert.embeddings.LayerNorm.gamma', 'bert.encoder.layer.0.attention.output.LayerNorm.beta', 'bert.encoder.layer.0.attention.output.LayerNorm.gamma', 'bert.encoder.layer.0.output.LayerNorm.beta', 'bert.encoder.layer.0.output.LayerNorm.gamma', 'bert.encoder.layer.1.attention.output.LayerNorm.beta', 'bert.encoder.layer.1.attention.output.LayerNorm.gamma', 'bert.encoder.layer.1.output.LayerNorm.beta', 'bert.encoder.layer.1.output.LayerNorm.gamma', 'bert.encoder.layer.2.attention.output.LayerNorm.beta', 'bert.encoder.layer.2.attention.output.LayerNorm.gamma', 'bert.encoder.layer.2.output.LayerNorm.beta', 'bert.encoder.layer.2.output.LayerNorm.gamma', 'bert.encoder.layer.3.attention.output.LayerNorm.beta', 'bert.encoder.layer.3.attention.output.LayerNorm.gamma', 'bert.encoder.layer.3.output.LayerNorm.beta', 'bert.encoder.layer.3.output.LayerNorm.gamma', 'bert.encoder.layer.4.attention.output.LayerNorm.beta', 'bert.encoder.layer.4.attention.output.LayerNorm.gamma', 'bert.encoder.layer.4.output.LayerNorm.beta', 'bert.encoder.layer.4.output.LayerNorm.gamma', 'bert.encoder.layer.5.attention.output.LayerNorm.beta', 'bert.encoder.layer.5.attention.output.LayerNorm.gamma', 'bert.encoder.layer.5.output.LayerNorm.beta', 'bert.encoder.layer.5.output.LayerNorm.gamma', 'bert.encoder.layer.6.attention.output.LayerNorm.beta', 'bert.encoder.layer.6.attention.output.LayerNorm.gamma', 'bert.encoder.layer.6.output.LayerNorm.beta', 'bert.encoder.layer.6.output.LayerNorm.gamma', 'bert.encoder.layer.7.attention.output.LayerNorm.beta', 'bert.encoder.layer.7.attention.output.LayerNorm.gamma', 'bert.encoder.layer.7.output.LayerNorm.beta', 'bert.encoder.layer.7.output.LayerNorm.gamma', 'bert.encoder.layer.8.attention.output.LayerNorm.beta', 'bert.encoder.layer.8.attention.output.LayerNorm.gamma', 'bert.encoder.layer.8.output.LayerNorm.beta', 'bert.encoder.layer.8.output.LayerNorm.gamma', 'bert.encoder.layer.9.attention.output.LayerNorm.beta', 'bert.encoder.layer.9.attention.output.LayerNorm.gamma', 'bert.encoder.layer.9.output.LayerNorm.beta', 'bert.encoder.layer.9.output.LayerNorm.gamma', 'bert.encoder.layer.10.attention.output.LayerNorm.beta', 'bert.encoder.layer.10.attention.output.LayerNorm.gamma', 'bert.encoder.layer.10.output.LayerNorm.beta', 'bert.encoder.layer.10.output.LayerNorm.gamma', 'bert.encoder.layer.11.attention.output.LayerNorm.beta', 'bert.encoder.layer.11.attention.output.LayerNorm.gamma', 'bert.encoder.layer.11.output.LayerNorm.beta', 'bert.encoder.layer.11.output.LayerNorm.gamma'].
100%|█████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 100/100 [00:09<00:00, 10.80it/s]
100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 7/7 [00:00<00:00, 133.85it/s]
PS G:\ai技能库\课程\Week4-Transfomer和BERT、GPT模型\Week04> & E:\Conda\envs\course\python.exe g:/ai技能库/课程/Week4-Transfomer和BERT、GPT模型/Week04/10.1_BERT文本分类.py
Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
Loading weights: 100%|█████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 199/199 [00:00<00:00, 11367.14it/s]
[transformers] BertForSequenceClassification LOAD REPORT from: bert-base-chinese
Key                                        | Status     | 
-------------------------------------------+------------+-
cls.seq_relationship.weight                | UNEXPECTED | 
cls.predictions.transform.LayerNorm.bias   | UNEXPECTED | 
cls.predictions.transform.LayerNorm.weight | UNEXPECTED | 
cls.predictions.transform.dense.bias       | UNEXPECTED | 
cls.seq_relationship.bias                  | UNEXPECTED | 
cls.predictions.transform.dense.weight     | UNEXPECTED | 
cls.predictions.bias                       | UNEXPECTED | 
classifier.weight                          | MISSING    | 
classifier.bias                            | MISSING    | 

Notes:
- UNEXPECTED:   can be ignored when loading from different task/architecture; not ok if you expect identical arch.
- MISSING:      those params were newly initialized because missing from the checkpoint. Consider training on your downstream task.
{'eval_loss': '2.481', 'eval_accuracy': '0.08', 'eval_runtime': '0.0866', 'eval_samples_per_second': '1155', 'eval_steps_per_second': '80.84', 'epoch': '1'}                        
{'eval_loss': '2.185', 'eval_accuracy': '0.35', 'eval_runtime': '0.0625', 'eval_samples_per_second': '1601', 'eval_steps_per_second': '112.1', 'epoch': '2'}                        
{'eval_loss': '1.737', 'eval_accuracy': '0.58', 'eval_runtime': '0.0638', 'eval_samples_per_second': '1568', 'eval_steps_per_second': '109.7', 'epoch': '3'}                        
{'loss': '2.074', 'grad_norm': '8.324', 'learning_rate': '9.9e-06', 'epoch': '4'}                                                                                                   
{'eval_loss': '1.117', 'eval_accuracy': '0.81', 'eval_runtime': '0.0623', 'eval_samples_per_second': '1605', 'eval_steps_per_second': '112.4', 'epoch': '4'}                        
{'train_runtime': '3.328', 'train_samples_per_second': '480.8', 'train_steps_per_second': '30.05', 'train_loss': '2.074', 'epoch': '4'}                                             
100%|█████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 100/100 [00:03<00:00, 30.04it/s]
100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 7/7 [00:00<00:00, 128.04it/s]
PS G:\ai技能库\课程\Week4-Transfomer和BERT、GPT模型\Week04> & E:\Conda\envs\course\python.exe g:/ai技能库/课程/Week4-Transfomer和BERT、GPT模型/Week04/10.1_BERT文本分类.py
Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
Loading weights: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 199/199 [00:00<00:00, 9690.66it/s]
[transformers] BertForSequenceClassification LOAD REPORT from: bert-base-chinese
Key                                        | Status     | 
-------------------------------------------+------------+-
cls.seq_relationship.bias                  | UNEXPECTED | 
cls.predictions.transform.LayerNorm.bias   | UNEXPECTED | 
cls.predictions.transform.dense.weight     | UNEXPECTED | 
cls.predictions.bias                       | UNEXPECTED | 
cls.predictions.transform.LayerNorm.weight | UNEXPECTED | 
cls.predictions.transform.dense.bias       | UNEXPECTED | 
cls.seq_relationship.weight                | UNEXPECTED | 
classifier.bias                            | MISSING    | 
classifier.weight                          | MISSING    | 

Notes:
- UNEXPECTED:   can be ignored when loading from different task/architecture; not ok if you expect identical arch.
- MISSING:      those params were newly initialized because missing from the checkpoint. Consider training on your downstream task.
{'loss': '1.342', 'grad_norm': '1.879', 'learning_rate': '4.95e-05', 'epoch': '0.4'}                                                                                                
{'loss': '0.2527', 'grad_norm': '0.1881', 'learning_rate': '4.45e-05', 'epoch': '0.8'}                                                                                              
{'eval_loss': '0.1616', 'eval_accuracy': '0.958', 'eval_runtime': '0.5615', 'eval_samples_per_second': '1781', 'eval_steps_per_second': '112.2', 'epoch': '1'}                      
{'loss': '0.1885', 'grad_norm': '5.341', 'learning_rate': '3.894e-05', 'epoch': '1.2'}                                                                                              
{'loss': '0.1063', 'grad_norm': '9.342', 'learning_rate': '3.339e-05', 'epoch': '1.6'}                                                                                              
{'loss': '0.1128', 'grad_norm': '0.1113', 'learning_rate': '2.783e-05', 'epoch': '2'}                                                                                               
{'eval_loss': '0.1439', 'eval_accuracy': '0.969', 'eval_runtime': '0.5956', 'eval_samples_per_second': '1679', 'eval_steps_per_second': '105.8', 'epoch': '2'}                      
{'loss': '0.05047', 'grad_norm': '0.3595', 'learning_rate': '2.228e-05', 'epoch': '2.4'}                                                                                            
{'loss': '0.06858', 'grad_norm': '0.9168', 'learning_rate': '1.672e-05', 'epoch': '2.8'}                                                                                            
{'eval_loss': '0.1032', 'eval_accuracy': '0.979', 'eval_runtime': '0.5878', 'eval_samples_per_second': '1701', 'eval_steps_per_second': '107.2', 'epoch': '3'}                      
{'loss': '0.03715', 'grad_norm': '0.05004', 'learning_rate': '1.117e-05', 'epoch': '3.2'}                                                                                           
{'loss': '0.01763', 'grad_norm': '6.553', 'learning_rate': '5.611e-06', 'epoch': '3.6'}                                                                                             
{'loss': '0.01426', 'grad_norm': '0.03811', 'learning_rate': '5.556e-08', 'epoch': '4'}                                                                                             
{'eval_loss': '0.1135', 'eval_accuracy': '0.978', 'eval_runtime': '0.5874', 'eval_samples_per_second': '1702', 'eval_steps_per_second': '107.3', 'epoch': '4'}                      
{'train_runtime': '32.12', 'train_samples_per_second': '498.2', 'train_steps_per_second': '31.14', 'train_loss': '0.2191', 'epoch': '4'}                                            
100%|███████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1000/1000 [00:32<00:00, 31.13it/s]
100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 63/63 [00:00<00:00, 109.56it/s]
PS G:\ai技能库\课程\Week4-Transfomer和BERT、GPT模型\Week04> & E:\Conda\envs\course\python.exe g:/ai技能库/课程/Week4-Transfomer和BERT、GPT模型/Week04/10.1_BERT文本分类.py
Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
Loading weights: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 199/199 [00:00<00:00, 9827.35it/s]
[transformers] BertForSequenceClassification LOAD REPORT from: bert-base-chinese
Key                                        | Status     | 
-------------------------------------------+------------+-
cls.seq_relationship.weight                | UNEXPECTED | 
cls.predictions.bias                       | UNEXPECTED | 
cls.predictions.transform.dense.weight     | UNEXPECTED | 
cls.predictions.transform.LayerNorm.bias   | UNEXPECTED | 
cls.predictions.transform.LayerNorm.weight | UNEXPECTED | 
cls.seq_relationship.bias                  | UNEXPECTED | 
cls.predictions.transform.dense.bias       | UNEXPECTED | 
classifier.weight                          | MISSING    | 
classifier.bias                            | MISSING    | 

Notes:
- UNEXPECTED:   can be ignored when loading from different task/architecture; not ok if you expect identical arch.
- MISSING:      those params were newly initialized because missing from the checkpoint. Consider training on your downstream task.
{'loss': '1.447', 'grad_norm': '7.322', 'learning_rate': '4.95e-05', 'epoch': '0.4'}                                                                                                
{'loss': '0.2332', 'grad_norm': '0.317', 'learning_rate': '4.238e-05', 'epoch': '0.8'}                                                                                              
{'eval_loss': '0.1744', 'eval_accuracy': '0.96', 'eval_runtime': '0.517', 'eval_samples_per_second': '1934', 'eval_steps_per_second': '121.9', 'epoch': '1'}                        
{'loss': '0.1476', 'grad_norm': '0.1619', 'learning_rate': '3.469e-05', 'epoch': '1.2'}                                                                                             
{'loss': '0.1134', 'grad_norm': '16.93', 'learning_rate': '2.7e-05', 'epoch': '1.6'}                                                                                                
{'loss': '0.09196', 'grad_norm': '0.05626', 'learning_rate': '1.931e-05', 'epoch': '2'}                                                                                             
{'eval_loss': '0.1307', 'eval_accuracy': '0.973', 'eval_runtime': '0.5176', 'eval_samples_per_second': '1932', 'eval_steps_per_second': '121.7', 'epoch': '2'}                      
{'loss': '0.06835', 'grad_norm': '0.02861', 'learning_rate': '1.162e-05', 'epoch': '2.4'}                                                                                           
{'loss': '0.03958', 'grad_norm': '0.3191', 'learning_rate': '3.923e-06', 'epoch': '2.8'}                                                                                            
{'eval_loss': '0.1074', 'eval_accuracy': '0.976', 'eval_runtime': '0.5222', 'eval_samples_per_second': '1915', 'eval_steps_per_second': '120.7', 'epoch': '3'}                      
{'train_runtime': '23.96', 'train_samples_per_second': '500.9', 'train_steps_per_second': '31.31', 'train_loss': '0.2891', 'epoch': '3'}                                            
100%|█████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 750/750 [00:23<00:00, 31.31it/s]
100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 63/63 [00:00<00:00, 124.50it/s]
PS G:\ai技能库\课程\Week4-Transfomer和BERT、GPT模型\Week04> & E:\Conda\envs\course\python.exe g:/ai技能库/课程/Week4-Transfomer和BERT、GPT模型/Week04/10.2_超参对比.py
Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
