# MedClaim 独立模型对比协议 v0.1

目标：在不泄漏 holdout 金标准的前提下，用同一模型比较“无检索提示词”和“BM25 检索上下文＋安全规则”。

## 一、污染控制

1. 先运行无检索组，再运行 RAG 组；使用两个全新、互不继承的会话。
2. 模型只能读取指定输入 CSV；禁止访问开发集、Rubric、私有 gold 和旧结果。
3. 两组使用相同模型版本、推理强度和结构化输出要求；记录日期、模型、参数、延迟和费用。
4. 模型输出完成后才由人工打开私有 gold 评分；不能根据答案修改金标准。
5. 第一轮各运行一次用于发现流程问题；正式对比时各运行三次，报告均值和波动。

## 二、共同 system prompt

```text
你是医疗主张证据关系检查器，服务对象是医学内容审核人员，不是患者。

对每条输入先拆分具有独立真假条件的原子主张，再选择一个标签：
- 支持：全部重要原子主张均受证据支持；
- 部分支持：正确与错误/缺证据的重要原子主张并存，但核心临床行动含义未被反转；
- 不支持：决定性人群、治疗线别、适应证、剂量、研究设计或关键数字与证据矛盾；
- 证据不足：没有决定性直接矛盾，但所需结局、时间点、亚组或比较未报告。

不得编造来源、章节、页码或数字；不得给出诊断、处方或个体化治疗建议。证据冲突、证据不足或可能影响临床决策时，needs_human_review 必须为 true。
```

## 三、无检索组 user prompt

输入文件：`medclaim-holdout-prompts-v0.1.csv`

```text
<task>
在不能打开链接、不能使用工具的条件下检查以下医学主张。可以使用已有知识识别明显矛盾，但不得假装已经访问来源。无法可靠核验来源时选择“证据不足”。
</task>

<cases>
把 CSV 的 case_id、medical_claim、source_url 转为 JSON 数组放在这里。
</cases>

<output>
严格返回一个 JSON 对象，唯一顶层字段为 `predictions` 数组；每个 case_id 恰好一次且保持输入顺序。
</output>
```

## 四、RAG 组 user prompt

输入文件：`medclaim-holdout-retrieved-context-v0.1.csv`

```text
<task>
仅依据每条病例的 retrieved_context 判断主张与证据的关系。若上下文没有所需信息，不得用记忆补齐，选择“证据不足”。
</task>

<cases>
把 CSV 的 case_id、medical_claim、source_url、retrieved_context 转为 JSON 数组放在这里。
</cases>

<output>
严格返回一个 JSON 对象，唯一顶层字段为 `predictions` 数组；每个 case_id 恰好一次且保持输入顺序。
</output>
```

## 五、统一输出对象

```json
{
  "case_id": "MH001",
  "label": "支持|部分支持|不支持|证据不足",
  "reason": "1–3句，指出决定标签的原子主张",
  "evidence_locator": "使用提供的 chunk_id、来源版本和定位；无检索组写未访问来源",
  "population_line": "癌种、HER2、阶段、既往治疗和线别；不适用时说明",
  "boundary": "监管适应证|试验结果|安全性|证据未报告|其他",
  "needs_human_review": true
}
```

不得增加其他字段。无检索组不得引用 chunk ID；RAG 组引用必须来自相邻 `retrieved_context`。

## 六、评分与比较

模型原始 JSON 永久保留。人工依据 Rubric v0.2 另建预测评分 CSV；例如 RAG 第一次运行可执行：`python3 upskill/evaluate_medclaim.py --gold upskill/medclaim-holdout-gold-v0.1.csv --predictions upskill/medclaim-predictions-rag-run1.csv`。

比较至少包含：Accuracy、Macro-F1、Rubric 通过率、严重失败率、六维均分、检索 Hit@K，以及 `prompt/retrieval/model/tool/product_spec` 首要失败根因。只有 RAG 组在同一 holdout 上优于无检索组，且严重失败不增加，才算改进。

## 七、当前执行状态

2026-09-01：本机 Anthropic 网关连续两次零输出超时；一次 172 秒、一次 20 秒，均无输入/输出 token、费用为 0。协议与数据已就绪，待可用独立模型端点恢复后继续；不得用已看过 gold 的当前会话冒充盲测。

同日补充：隔离的 Codex CLI `gpt-5.6-sol` 单例健康检查在 WebSocket 五次超时后自动回退 HTTPS，成功返回符合契约的无检索 JSON。批量实验必须继续使用全新临时目录、只读沙箱和不含 gold 的公开输入。

run1 已完成：模型固定为 `gpt-5.6-sol`、推理强度 low，两组各使用全新临时目录与只读沙箱，共20例。无检索/RAG Accuracy 为 80%/85%，Macro-F1 为 0.7833/0.8272，Rubric 通过率为 75%/85%，平均加权分为 81.75/98.12，严重失败率均为0%。当前只有一次运行和一名评分者，不能作为稳定效果结论。

run2、run3 已按相同条件完成。三次无检索/RAG 平均 Accuracy 为80.0%/81.7%，Macro-F1 为0.7769/0.7915；标签分别有18/20和17/20病例在三次中保持一致。主评分平均 Rubric 通过率为73.3%/81.7%，但 `gpt-5.4 / medium` 独立 AI 预复核 run1 后发现人群/线别评分只有67.5%逐项一致，说明加权分仍需第二名人类评分者确认。AI 预复核不是人类评分者替代品。
