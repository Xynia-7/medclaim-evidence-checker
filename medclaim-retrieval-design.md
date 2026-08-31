# MedClaim 最小检索层设计

日期：2026-09-01  
状态：按用户“无需确认、可完全代理”授权执行

## 目标

在不调用大模型、Embedding 服务或向量数据库的前提下，验证每条医学主张能否从小型权威资料库中找到正确证据。模型生成质量与检索质量分开评估。

## 方案

- 资料库：8 个中文证据块，逐块绑定 FDA/NCI/EMA 来源、版本和章节/页码。
- 检索：Python 标准库实现 BM25；英文按词、中文按双字切分。
- 输入：只读取公开 holdout 的 `case_id` 与 `medical_claim`。
- 输出：每条 Top-3 chunk、分数、Hit@1/Hit@3；汇总 MRR。
- 评分：私有 `gold_chunk_id` 仅在检索完成后用于对照，不进入查询或排序。

## 边界

- 证据块是带定位的人工忠实转述，不冒充监管原文全文。
- “证据不足”病例没有唯一正确证据块，不进入 Hit/MRR 分母，但仍输出 Top-3 供人工检查。
- 只验证 retrieval，不生成最终医学判断，也不声称可用于临床。
- 本轮不做 Embedding、reranker、向量数据库、Dify UI 或外部 API。

## 验收

1. 8 个 chunk ID 唯一，来源、版本、定位、文本均非空。
2. 公开输入没有 `gold_label`、`gold_chunk_id` 或证据答案。
3. 私有 gold 与 10 个 holdout ID 一一对应；9 个有证据病例的 gold chunk 全部存在。
4. 自检能证明完全匹配排第一、无 gold 病例不进入指标分母。
5. 一条命令生成 CSV、JSON、Markdown；报告显示 Hit@1、Hit@3、MRR 和逐例排名。

## 停止条件

上述检查通过即停止；只有词法检索在实际 holdout 上明显漏检时，才考虑同义词、Embedding 或 reranker。
