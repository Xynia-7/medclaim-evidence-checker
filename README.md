# MedClaim Evidence Checker

面向医学内容审核人员的医疗 AI 作品集项目：判断公开证据是否支持一条 HER2 阳性胃/胃食管交界部癌与 ADC 相关主张，并显式检查人群、治疗线别、关键数字、引用和证据边界。

## 当前可运行内容

```bash
cd medclaim-evidence-checker
python3 evaluate_medclaim.py --self-test
python3 evaluate_medclaim.py
python3 retrieve_medclaim.py --self-test
python3 retrieve_medclaim.py
python3 run_medclaim_model.py --self-test
python3 analyze_rater_agreement.py --self-test
```

第二条命令会读取 10 条金标准和多数类规则预测，生成 JSON 与 Markdown 报告。当前基线结果：

- Accuracy：50.0%
- Macro-F1：0.1667
- Rubric 通过率：0.0%
- 平均加权分：12.50/100

这个结果只验证评测管线；多数类规则不读取医学内容，不是医疗 AI 模型。

检索层在给定来源内部对 17 个权威证据块排序：两个 holdout 各有9个可评病例，Hit@1、Hit@3 和 MRR@3 均为 1.0。该结果只代表小型人工语料的段落检索，不代表开放网络、跨语言或临床性能。

当前病例总数为 50：30 条开发/校准病例、20 条隔离 holdout。开发病例不能冒充独立测试结果，50例也不能证明模型有效。

在三次隔离的 `gpt-5.6-sol / low` 运行中，同一20条 holdout 的无检索/RAG 平均 Accuracy 为80.0%/81.7%，Macro-F1 为0.7769/0.7915；两次运行的 Accuracy 没有差异，因此不能声称 RAG 稳定提高分类正确率。主评分者给出的平均 Rubric 通过率为73.3%/81.7%，但独立 AI 预复核发现人群/线别维度评分偏宽，最终加权结果仍需第二名人类评分者确认。

## 文件

| 文件 | 用途 |
|---|---|
| [`medclaim-eval-cases-v0.2.csv`](medclaim-eval-cases-v0.2.csv) | 10 条开发/校准主张、来源、金标准和严重错误定义 |
| [`medclaim-eval-review-slice-v0.1.csv`](medclaim-eval-review-slice-v0.1.csv) | 基于个人共同第一作者综述公开摘要的10条证据边界病例 |
| [`medclaim-review-slice-validation-v0.1.md`](medclaim-review-slice-validation-v0.1.md) | 个人综述切片的标签、重复度和版权边界复核 |
| [`medclaim-eval-2026-review-slice-v0.1.csv`](medclaim-eval-2026-review-slice-v0.1.csv) | 基于2026综述摘要的10条靶点、早线研究与耐药病例 |
| [`medclaim-rubric-v0.2.md`](medclaim-rubric-v0.2.md) | 原子主张裁决、六维评分和安全门 |
| [`medclaim-predictions-majority-baseline.csv`](medclaim-predictions-majority-baseline.csv) | 可复现的多数类规则基线 |
| [`evaluate_medclaim.py`](evaluate_medclaim.py) | 零第三方依赖的评测器 |
| [`medclaim-results-majority-baseline.md`](medclaim-results-majority-baseline.md) | 人类可读基线结果 |
| [`medclaim-results-majority-baseline.json`](medclaim-results-majority-baseline.json) | 机器可读基线结果 |
| [`medclaim-holdout-prompts-v0.1.csv`](medclaim-holdout-prompts-v0.1.csv) | 不含类别、标签或证据答案的独立模型输入 |
| [`medclaim-holdout-prompts-open-review-v0.1.csv`](medclaim-holdout-prompts-open-review-v0.1.csv) | 第二组不含 gold 的 CC BY 4.0 综述 holdout |
| [`medclaim-corpus-v0.1.csv`](medclaim-corpus-v0.1.csv) | 17 个绑定版本、定位与许可的权威证据块 |
| [`retrieve_medclaim.py`](retrieve_medclaim.py) | 标准库 BM25、Top-3、Hit@K 与 MRR |
| [`medclaim-holdout-retrieved-context-v0.1.csv`](medclaim-holdout-retrieved-context-v0.1.csv) | 不含 gold 的 RAG 模型输入 |
| [`medclaim-holdout-retrieved-context-open-review-v0.1.csv`](medclaim-holdout-retrieved-context-open-review-v0.1.csv) | 第二组不含 gold 的 RAG 模型输入 |
| [`medclaim-model-evaluation-protocol.md`](medclaim-model-evaluation-protocol.md) | 无检索/RAG 固定提示词、输出契约和污染控制 |
| [`medclaim-model-output-schema.json`](medclaim-model-output-schema.json) | 独立模型结构化输出的 JSON Schema |
| [`run_medclaim_model.py`](run_medclaim_model.py) | 固定条件并隔离 gold 的无检索/RAG重复实验 runner |
| [`medclaim-model-comparison-run1.md`](medclaim-model-comparison-run1.md) | 20例无检索/RAG单次探索性对比与错误边界 |
| [`medclaim-model-comparison-3runs.md`](medclaim-model-comparison-3runs.md) | 三次重复结果、标签稳定性和 AI 预复核敏感性分析 |
| [`medclaim-second-rater-schema.json`](medclaim-second-rater-schema.json) | 独立评分者六维评分的结构化输出契约 |
| [`analyze_rater_agreement.py`](analyze_rater_agreement.py) | 标准库逐维一致率、Cohen's κ及边际分布分析器 |
| [`medclaim-error-report-v0.1.md`](medclaim-error-report-v0.1.md) | 多数类规则基线的错误分布与下一轮实验假设 |
| [`medclaim-demo-script-3min.md`](medclaim-demo-script-3min.md) | 面试现场可照着运行和讲解的3分钟脚本 |
| [`medclaim-workflow-metrics.md`](medclaim-workflow-metrics.md) | 人机审核流程、指标口径、计时实验和发布门槛 |
| [`medclaim-fhir-workflow.md`](medclaim-fhir-workflow.md) | FHIR资源、SMART授权、只读临床文档审核与90分钟验收 |
| [`medclaim-source-pack.md`](medclaim-source-pack.md) | FDA、NCI、EMA、PubMed/PMC 资料边界 |
| [`medclaim-validation-v0.2.md`](medclaim-validation-v0.2.md) | 数据、Rubric、计算和已知限制复核 |
| [`medclaim-50-case-validation-v0.1.md`](medclaim-50-case-validation-v0.1.md) | 50例组成、隔离、许可、检索和剩余有效性缺口 |
| [`medclaim-prd.md`](medclaim-prd.md) | 用户、边界、输出契约、失败归因和验收标准 |

## 输入格式

预测 CSV 每条必须包含：

```text
case_id,predicted_label,support_relation,population_line_score,numeric_outcome_score,citation_validity_score,evidence_boundary_score,auditability_score,critical_failure,failure_root_cause,reason,evidence_locator
```

四分类标签只能是：`支持`、`部分支持`、`不支持`、`证据不足`。六维评分只能是 0、1、2；严重失败只能是 `true` 或 `false`。失败根因只能是 `prompt`、`retrieval`、`model`、`tool`、`product_spec`，通过例用 `none`，非模型规则基线用 `not_applicable`。缺失、多余、重复病例或非法值会直接报错并停止。

独立模型只能读取 `medclaim-holdout-prompts-v0.1.csv`。本地金标准文件已由 `.gitignore` 排除，不能放进公开仓库或模型上下文。得到预测并完成盲态人工六维评分后，再显式指定本地金标准运行评测器。

两名评分者完成同一批病例后，将评分规范化为包含 `condition`、`case_id`、六维分和 `critical_failure` 的两份 CSV，再运行：

```bash
python3 analyze_rater_agreement.py --rater-a rater-a.csv --rater-b rater-b.csv
```

脚本会拒绝缺失、重复或非法记录，输出逐维原始一致率、类别计数与 Cohen's κ。κ不可定义时保留为空，不能写成0；解释时必须同时报告一致率和边际分布。

κ定义与边际分布口径参照 [scikit-learn 官方文档](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.cohen_kappa_score.html)，但实现仅使用 Python 标准库。

## 项目边界

- 只用公开的 FDA、NCI、EMA、PubMed 摘要及合法开放获取资料；
- 不使用真实患者数据；
- 不做诊断、处方或个体化治疗建议；
- 10 条是 Rubric 校准集，不代表外部泛化或临床有效性；
- 金标准锁定后才评模型，避免根据模型输出迁就答案。

## 下一里程碑

1. 由第二名人类评分者盲态复核六维分，重点校准人群/线别遗漏；
2. 针对“证据不足”和决定性错误的标签优先级做开发集回归，不修改本轮 holdout gold；
3. 完成个人技能迁移验收：独立运行、评分5例并用3分钟讲清结果与限制。
