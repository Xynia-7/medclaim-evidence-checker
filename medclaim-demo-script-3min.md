# MedClaim 3分钟演示稿

## 0:00–0:25 问题

“医学内容审核的难点不是模型能否给出流畅回答，而是它有没有把人群、治疗线别、数字和来源边界说对。这个项目把这些风险变成可以重复评测的任务。”

## 0:25–0:55 输入与输出

打开 `medclaim-eval-cases-v0.2.csv` 的一条病例：主张、来源、金标准和严重错误是分开的。再打开 `medclaim-rubric-v0.2.md`：输出不只判四分类，还检查人群/线别、数字、引用、证据边界和可审计性。

## 0:55–1:25 现场运行

```bash
python3 evaluate_medclaim.py --self-test
python3 evaluate_medclaim.py
python3 retrieve_medclaim.py --self-test
python3 retrieve_medclaim.py
```

“两个脚本都只依赖 Python 标准库。评测器会拒绝缺失、重复或非法病例；检索器输出 Top-3，并把没有 gold 的病例排除在 Hit@K 计算之外。”

## 1:25–1:55 结果

“当前共有50例：30例用于开发/校准，20例隔离 holdout。多数类规则基线 Accuracy 是50%，但 Macro-F1 只有0.1667、Rubric 通过率是0%，说明只看准确率会误导。17个证据块上的两个 holdout 共18个可评病例均命中 Top-1。”

## 1:55–2:25 诚实边界

“Top-1 结果来自小型、人工整理且按来源 URL 过滤的中文转述语料，不能外推到开放网络、跨语言或临床性能。公开仓库只放 holdout prompts 和 RAG context；gold 与私有评测结果被隔离，避免模型看到答案。”

## 2:25–3:00 产品价值与下一步

“这个作品展示的不是训练大模型，而是把医疗证据审核做成可定义、可复现、可归因的产品流程。三次盲测说明 RAG 没有稳定提高分类正确率，但增强了证据可审计性。当前所有结果仍由人复核；下一步用20例平衡 AB/BA 计时实验，在严重漏检为零的前提下，检验中位复核时长能否缩短25%。”

面试追问时可打开 `medclaim-error-report-v0.1.md` 解释为什么50% Accuracy 仍然是失败基线，或打开 `medclaim-workflow-metrics.md` 解释指标分母、人工升级和发布门槛。
