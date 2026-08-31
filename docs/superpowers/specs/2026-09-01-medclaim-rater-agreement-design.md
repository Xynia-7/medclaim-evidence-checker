# MedClaim 评分者一致性分析器设计

日期：2026-09-01

## 目标

新增一个零第三方依赖的命令行脚本，在第二名人类评分者返回结果后，用相同 `condition × case_id` 对齐两名评分者，报告六维分数和严重失败判断的一致性。

## 选择

采用独立脚本 `analyze_rater_agreement.py`，不把一致性统计塞进模型正确性评测器，也不引入 pandas、scikit-learn 或 notebook。脚本接受两份 CSV，生成 JSON 与 Markdown。

## 输入

两份 CSV 必须各包含：

```text
condition,case_id,support_relation,population_line_score,
numeric_outcome_score,citation_validity_score,evidence_boundary_score,
auditability_score,critical_failure
```

- `condition` 仅限 `no-retrieval`、`rag`；
- 六维仅限整数0、1、2；
- `critical_failure` 仅限 `true`、`false`；
- 联合键必须唯一，两份文件的键集合必须完全一致。

## 输出

每个维度及 `critical_failure` 报告：

- 样本数；
- 完全一致数与一致率；
- 两名评分者各自的类别计数；
- Cohen’s κ；
- κ不可计算时返回 `null` 并说明“边际分布无变异”。

同时报告所有七个判断位的总体一致率，但不把不同维度合成一个总体 κ。Markdown 必须提醒：κ受类别流行率/边际分布影响，应与原始一致率和类别计数一起解释。

## 计算

对某维度：

```text
p_o = 完全一致数 / n
p_e = Σ(评分者A给类别c的比例 × 评分者B给类别c的比例)
κ = (p_o - p_e) / (1 - p_e)
```

当 `1 - p_e = 0` 时 κ 不可定义，不能写成0。

## 验收

- 已知例 `A=[0,0,1,1]`、`B=[0,1,1,1]` 得到一致率0.75、κ0.50；
- 两者全给同一类别时一致率1.0、κ为 `null`；
- 缺失键、重复键、非法分数和非法布尔值均尽早失败；
- 自测不读取任何私有评分文件；
- README 只增加运行示例和文件链接，不公布人类评分结果。
