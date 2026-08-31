# MedClaim 公开仓库设计

## 目的

把现有 MedClaim Evidence Checker 整理为可复现、可审计的医疗 AI 求职作品集，同时避免公开私有 holdout 金标准、评测结果、个人训练计划和简历措辞。

## 方案

直接在 `upskill` 建立独立 Git 仓库，不复制第二份项目，也不把上层论文目录纳入版本控制。只提交项目代码、公开数据、方法文档和不含 gold 的 holdout 输入；`.gitignore` 隔离私有和个人材料。

## 数据流与边界

公开开发集与多数类预测进入 `evaluate_medclaim.py`，生成可复现基线。公开语料进入 `retrieve_medclaim.py`，生成不含 gold 的 RAG 上下文。私有 holdout gold 只留在本机，模型预测完成后才能用于盲评。

## 失败处理

发现密钥、本机绝对路径、个人材料或私有 gold 时停止发布。GitHub 发布前审计实际跟踪文件，而不是依赖目录观感。

## 验收

- 两个 Python 自测通过；
- README 相对链接存在；
- 跟踪文件不含本机路径或疑似密钥；
- 私有 holdout gold、私有结果和个人材料均未跟踪；
- Git 提交可从干净检出运行。
