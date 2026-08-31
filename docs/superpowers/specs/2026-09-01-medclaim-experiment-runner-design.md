# MedClaim 重复实验 Runner 设计

## 目的

用一个标准库脚本重复运行无检索或 RAG 条件，固定输入、模型、推理强度、输出 Schema 与隔离方式，减少手工复制命令造成的实验漂移。

## 接口

命令接收 `condition`、`run-id`、`model` 和 `effort`。`no-retrieval` 只读取两份公开 prompt；`rag` 只读取两份公开 retrieved-context。脚本不得读取任何 gold、评分或旧模型输出。

## 执行与输出

脚本把20例转成 JSON，创建全新临时目录，然后调用本机 Codex CLI 的临时会话、只读沙箱和结构化输出 Schema。原始结果写入被 `.gitignore` 隔离的文件，随后校验20个唯一 case_id 及输入顺序。

## 失败处理

Codex CLI 非零退出、JSON 无法解析、病例缺失/重复/乱序时立即失败，不生成“成功”结论。已存在的同名输出默认拒绝覆盖，需显式 `--overwrite`。

## 验收

- `--self-test` 不调用模型即可验证两类 prompt 和输出校验；
- run2/run3 的模型、推理强度和20例顺序与 run1 一致；
- 原始输出不被 Git 跟踪；
- runner 不含第三方 Python 依赖，也不接触 gold。
