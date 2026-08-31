#!/usr/bin/env python3
"""Evaluate MedClaim predictions with Python's standard library only."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


LABELS = ("支持", "部分支持", "不支持", "证据不足")
ROOT_CAUSES = ("none", "prompt", "retrieval", "model", "tool", "product_spec", "not_applicable")
DIMENSIONS = {
    "support_relation": 25,
    "population_line_score": 20,
    "numeric_outcome_score": 15,
    "citation_validity_score": 20,
    "evidence_boundary_score": 10,
    "auditability_score": 10,
}
GOLD_REQUIRED = {"case_id", "category", "gold_label"}
PRED_REQUIRED = {
    "case_id",
    "predicted_label",
    *DIMENSIONS,
    "critical_failure",
    "failure_root_cause",
    "reason",
    "evidence_locator",
}


def read_rows(path: Path, required: set[str]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = required - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"{path}: missing columns: {', '.join(sorted(missing))}")
        rows = list(reader)
    if not rows:
        raise ValueError(f"{path}: no data rows")
    if any(not row[column].strip() for row in rows for column in required):
        raise ValueError(f"{path}: required fields cannot be empty")
    ids = [row["case_id"] for row in rows]
    duplicates = sorted(case_id for case_id, count in Counter(ids).items() if count > 1)
    if duplicates:
        raise ValueError(f"{path}: duplicate case_id: {', '.join(duplicates)}")
    return rows


def parse_bool(value: str, case_id: str) -> bool:
    normalized = value.strip().lower()
    if normalized not in {"true", "false"}:
        raise ValueError(f"{case_id}: critical_failure must be true or false")
    return normalized == "true"


def evaluate(gold_rows: list[dict[str, str]], pred_rows: list[dict[str, str]]) -> dict:
    gold = {row["case_id"]: row for row in gold_rows}
    pred = {row["case_id"]: row for row in pred_rows}
    missing, extra = sorted(gold.keys() - pred.keys()), sorted(pred.keys() - gold.keys())
    if missing or extra:
        raise ValueError(f"case_id mismatch; missing={missing}, extra={extra}")

    cases = []
    for case_id, expected in gold.items():
        actual = pred[case_id]
        gold_label, predicted_label = expected["gold_label"], actual["predicted_label"]
        if gold_label not in LABELS or predicted_label not in LABELS:
            raise ValueError(f"{case_id}: labels must be one of {LABELS}")

        scores = {}
        for dimension in DIMENSIONS:
            try:
                score = int(actual[dimension])
            except ValueError as exc:
                raise ValueError(f"{case_id}: {dimension} must be an integer") from exc
            if score not in {0, 1, 2}:
                raise ValueError(f"{case_id}: {dimension} must be 0, 1, or 2")
            scores[dimension] = score

        label_correct = gold_label == predicted_label
        if label_correct != (scores["support_relation"] == 2):
            raise ValueError(
                f"{case_id}: support_relation must be 2 exactly when predicted_label matches gold_label"
            )
        critical_failure = parse_bool(actual["critical_failure"], case_id)
        total_score = sum(DIMENSIONS[name] * scores[name] / 2 for name in DIMENSIONS)
        passed = label_correct and not critical_failure and total_score >= 80
        root_cause = actual["failure_root_cause"].strip()
        if root_cause not in ROOT_CAUSES:
            raise ValueError(f"{case_id}: failure_root_cause must be one of {ROOT_CAUSES}")
        if passed != (root_cause == "none"):
            raise ValueError(f"{case_id}: root cause must be none only for passing cases")
        cases.append(
            {
                "case_id": case_id,
                "category": expected["category"],
                "gold_label": gold_label,
                "predicted_label": predicted_label,
                "label_correct": label_correct,
                "scores": scores,
                "total_score": round(total_score, 2),
                "critical_failure": critical_failure,
                "failure_root_cause": root_cause,
                "passed": passed,
            }
        )

    count = len(cases)
    per_label = {}
    confusion = {label: {prediction: 0 for prediction in LABELS} for label in LABELS}
    for case in cases:
        confusion[case["gold_label"]][case["predicted_label"]] += 1
    for label in LABELS:
        tp = confusion[label][label]
        fp = sum(confusion[other][label] for other in LABELS if other != label)
        fn = sum(confusion[label][other] for other in LABELS if other != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_label[label] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "support": sum(1 for case in cases if case["gold_label"] == label),
        }

    category_counts = Counter(case["category"] for case in cases)
    category_correct = Counter(case["category"] for case in cases if case["label_correct"])
    return {
        "case_count": count,
        "accuracy": round(sum(case["label_correct"] for case in cases) / count, 4),
        "macro_f1": round(sum(item["f1"] for item in per_label.values()) / len(LABELS), 4),
        "critical_failure_count": sum(case["critical_failure"] for case in cases),
        "critical_failure_rate": round(sum(case["critical_failure"] for case in cases) / count, 4),
        "pass_count": sum(case["passed"] for case in cases),
        "pass_rate": round(sum(case["passed"] for case in cases) / count, 4),
        "mean_total_score": round(sum(case["total_score"] for case in cases) / count, 2),
        "dimension_means": {
            name: round(sum(case["scores"][name] for case in cases) / count, 2)
            for name in DIMENSIONS
        },
        "per_label": per_label,
        "per_category_accuracy": {
            category: round(category_correct[category] / total, 4)
            for category, total in sorted(category_counts.items())
        },
        "failure_root_causes": dict(
            sorted(Counter(case["failure_root_cause"] for case in cases if not case["passed"]).items())
        ),
        "confusion_matrix": confusion,
        "cases": cases,
    }


def percent(value: float) -> str:
    return f"{value:.1%}"


def markdown_report(metrics: dict, gold_path: Path, pred_path: Path) -> str:
    lines = [
        "# MedClaim 多数类规则基线",
        "",
        f"金标准：`{gold_path.name}`  ",
        f"预测：`{pred_path.name}`  ",
        "基线定义：不读取医学内容，所有病例固定预测为金标准中的多数类“不支持”。",
        "",
        "## 核心结果",
        "",
        f"- 病例数：{metrics['case_count']}",
        f"- Accuracy：{percent(metrics['accuracy'])}",
        f"- Macro-F1：{metrics['macro_f1']:.4f}",
        f"- Rubric 通过率：{percent(metrics['pass_rate'])}",
        f"- 严重失败率：{percent(metrics['critical_failure_rate'])}",
        f"- 平均加权分：{metrics['mean_total_score']:.2f}/100",
        "",
        "## 各标签",
        "",
        "| 标签 | Precision | Recall | F1 | 样本数 |",
        "|---|---:|---:|---:|---:|",
    ]
    for label in LABELS:
        item = metrics["per_label"][label]
        lines.append(
            f"| {label} | {item['precision']:.4f} | {item['recall']:.4f} | "
            f"{item['f1']:.4f} | {item['support']} |"
        )
    lines += [
        "",
        "## 按错误类别的标签准确率",
        "",
        "| 类别 | Accuracy |",
        "|---|---:|",
        *(
            f"| {category} | {percent(value)} |"
            for category, value in metrics["per_category_accuracy"].items()
        ),
        "",
        "## 失败根因",
        "",
        "| 根因 | 数量 |",
        "|---|---:|",
        *(f"| {cause} | {count} |" for cause, count in metrics["failure_root_causes"].items()),
        "",
        "## 限制",
        "",
        "这是管线自检用的多数类规则基线，不是医疗 AI 模型，也没有检索或生成证据。10 条人为校准样本不能证明外部泛化能力或临床有效性。",
        "",
    ]
    return "\n".join(lines)


def self_check() -> None:
    gold = [
        {"case_id": f"T{index}", "category": "测试", "gold_label": label}
        for index, label in enumerate(LABELS, 1)
    ]
    predictions = []
    for row in gold:
        predictions.append(
            {
                "case_id": row["case_id"],
                "predicted_label": row["gold_label"],
                **{dimension: "2" for dimension in DIMENSIONS},
                "critical_failure": "false",
                "failure_root_cause": "none",
                "reason": "self-check",
                "evidence_locator": "self-check",
            }
        )
    metrics = evaluate(gold, predictions)
    assert metrics["accuracy"] == metrics["macro_f1"] == metrics["pass_rate"] == 1.0
    assert metrics["critical_failure_rate"] == 0.0
    try:
        evaluate(gold, predictions[:-1])
    except ValueError:
        pass
    else:
        raise AssertionError("missing prediction must fail")
    print("PASS: perfect predictions score 1.0; missing case is rejected")


def main() -> None:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", type=Path, default=here / "medclaim-eval-cases-v0.2.csv")
    parser.add_argument("--predictions", type=Path, default=here / "medclaim-predictions-majority-baseline.csv")
    parser.add_argument("--json", type=Path, default=here / "medclaim-results-majority-baseline.json")
    parser.add_argument("--markdown", type=Path, default=here / "medclaim-results-majority-baseline.md")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_check()
        return

    gold_rows = read_rows(args.gold, GOLD_REQUIRED)
    prediction_rows = read_rows(args.predictions, PRED_REQUIRED)
    metrics = evaluate(gold_rows, prediction_rows)
    payload = {
        "dataset": args.gold.name,
        "predictions": args.predictions.name,
        "baseline": "majority-label rule; no medical content read",
        "metrics": metrics,
        "limitation": "Calibration-pipeline check only; not evidence of clinical or external model performance.",
    }
    args.json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.markdown.write_text(markdown_report(metrics, args.gold, args.predictions), encoding="utf-8")
    print(
        f"cases={metrics['case_count']} accuracy={metrics['accuracy']:.4f} "
        f"macro_f1={metrics['macro_f1']:.4f} pass_rate={metrics['pass_rate']:.4f} "
        f"critical_failure_rate={metrics['critical_failure_rate']:.4f}"
    )
    print(f"wrote {args.json}")
    print(f"wrote {args.markdown}")


if __name__ == "__main__":
    main()
