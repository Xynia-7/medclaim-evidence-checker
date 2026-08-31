#!/usr/bin/env python3
"""Compare two MedClaim rubric rating CSV files."""

from __future__ import annotations

import argparse
import csv
import json
import tempfile
from collections import Counter
from pathlib import Path


CONDITIONS = ("no-retrieval", "rag")
DIMENSIONS = (
    "support_relation",
    "population_line_score",
    "numeric_outcome_score",
    "citation_validity_score",
    "evidence_boundary_score",
    "auditability_score",
)
FIELDS = (*DIMENSIONS, "critical_failure")
REQUIRED = {"condition", "case_id", *FIELDS}


def parse_bool(value: str, key: tuple[str, str]) -> bool:
    normalized = value.strip().lower()
    if normalized not in {"true", "false"}:
        raise ValueError(f"{key}: critical_failure must be true or false")
    return normalized == "true"


def read_ratings(path: Path) -> dict[tuple[str, str], dict[str, int | bool]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"{path}: missing columns: {', '.join(sorted(missing))}")
        raw_rows = list(reader)
    if not raw_rows:
        raise ValueError(f"{path}: no data rows")

    ratings = {}
    for row_number, row in enumerate(raw_rows, 2):
        if any(not (row[field] or "").strip() for field in REQUIRED):
            raise ValueError(f"{path}:{row_number}: required fields cannot be empty")
        condition, case_id = row["condition"].strip(), row["case_id"].strip()
        if condition not in CONDITIONS:
            raise ValueError(f"{path}:{row_number}: condition must be one of {CONDITIONS}")
        key = (condition, case_id)
        if key in ratings:
            raise ValueError(f"{path}:{row_number}: duplicate key: {condition}/{case_id}")

        parsed: dict[str, int | bool] = {}
        for dimension in DIMENSIONS:
            try:
                score = int(row[dimension])
            except ValueError as exc:
                raise ValueError(f"{path}:{row_number}: {dimension} must be an integer") from exc
            if score not in {0, 1, 2}:
                raise ValueError(f"{path}:{row_number}: {dimension} must be 0, 1, or 2")
            parsed[dimension] = score
        parsed["critical_failure"] = parse_bool(row["critical_failure"], key)
        ratings[key] = parsed
    return ratings


def agreement_stat(values_a: list, values_b: list, categories: tuple) -> dict:
    if len(values_a) != len(values_b) or not values_a:
        raise ValueError("rating vectors must be non-empty and the same length")
    unknown = (set(values_a) | set(values_b)) - set(categories)
    if unknown:
        raise ValueError(f"unexpected categories: {sorted(unknown, key=str)}")

    count = len(values_a)
    counts_a, counts_b = Counter(values_a), Counter(values_b)
    agreement_count = sum(left == right for left, right in zip(values_a, values_b))
    observed = agreement_count / count
    expected = sum(counts_a[item] * counts_b[item] for item in categories) / (count * count)
    kappa = None if expected == 1.0 else (observed - expected) / (1 - expected)
    confusion = {
        str(left): {
            str(right): sum(a == left and b == right for a, b in zip(values_a, values_b))
            for right in categories
        }
        for left in categories
    }
    return {
        "count": count,
        "agreement_count": agreement_count,
        "agreement_rate": round(observed, 4),
        "expected_agreement": round(expected, 4),
        "cohen_kappa": None if kappa is None else round(kappa, 4),
        "kappa_status": "undefined_no_marginal_variation" if kappa is None else "defined",
        "rater_a_distribution": {str(item): counts_a[item] for item in categories},
        "rater_b_distribution": {str(item): counts_b[item] for item in categories},
        "confusion_matrix": confusion,
    }


def compare_ratings(
    ratings_a: dict[tuple[str, str], dict[str, int | bool]],
    ratings_b: dict[tuple[str, str], dict[str, int | bool]],
) -> dict:
    keys_a, keys_b = set(ratings_a), set(ratings_b)
    missing, extra = sorted(keys_a - keys_b), sorted(keys_b - keys_a)
    if missing or extra:
        raise ValueError(f"rating key mismatch; missing_from_b={missing}, extra_in_b={extra}")
    keys = sorted(keys_a)

    fields = {}
    total_agreements = 0
    for field in FIELDS:
        categories = (False, True) if field == "critical_failure" else (0, 1, 2)
        values_a = [ratings_a[key][field] for key in keys]
        values_b = [ratings_b[key][field] for key in keys]
        fields[field] = agreement_stat(values_a, values_b, categories)
        total_agreements += fields[field]["agreement_count"]

    decision_count = len(keys) * len(FIELDS)
    return {
        "item_count": len(keys),
        "condition_counts": dict(sorted(Counter(condition for condition, _ in keys).items())),
        "decision_count": decision_count,
        "overall_agreement_count": total_agreements,
        "overall_agreement_rate": round(total_agreements / decision_count, 4),
        "fields": fields,
    }


def format_distribution(values: dict[str, int]) -> str:
    return ", ".join(f"{key}:{count}" for key, count in values.items())


def markdown_report(metrics: dict, rater_a: Path, rater_b: Path) -> str:
    lines = [
        "# MedClaim 评分者一致性报告",
        "",
        f"评分者A：`{rater_a.name}`  ",
        f"评分者B：`{rater_b.name}`  ",
        f"配对病例：{metrics['item_count']}；判断位：{metrics['decision_count']}",
        f"全部判断位原始一致率：{metrics['overall_agreement_rate']:.1%}",
        "",
        "## 逐维结果",
        "",
        "| 维度 | 一致数/总数 | 一致率 | Cohen's κ | A分布 | B分布 |",
        "|---|---:|---:|---:|---|---|",
    ]
    for field in FIELDS:
        item = metrics["fields"][field]
        kappa = "不可计算" if item["cohen_kappa"] is None else f"{item['cohen_kappa']:.4f}"
        lines.append(
            f"| {field} | {item['agreement_count']}/{item['count']} | "
            f"{item['agreement_rate']:.1%} | {kappa} | "
            f"{format_distribution(item['rater_a_distribution'])} | "
            f"{format_distribution(item['rater_b_distribution'])} |"
        )
    lines += [
        "",
        "## 解释边界",
        "",
        "- κ按 `(p_o - p_e) / (1 - p_e)` 计算；当两名评分者的边际分布均无变异时，κ不可定义，不写成0。",
        "- κ会受类别流行率和边际分布影响，必须与原始一致率、分子/分母和类别计数一起解释。",
        "- 本报告只描述评分一致性，不证明gold正确、模型有效或达到临床部署要求。",
        "- 分歧应逐例裁决并记录规则修改；不能仅凭一个κ阈值自动接受或否定Rubric。",
        "",
    ]
    return "\n".join(lines)


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["condition", "case_id", *FIELDS])
        writer.writeheader()
        writer.writerows(rows)


def self_check() -> None:
    known = agreement_stat([0, 0, 1, 1], [0, 1, 1, 1], (0, 1))
    assert known["agreement_rate"] == 0.75
    assert known["cohen_kappa"] == 0.5
    constant = agreement_stat([2, 2, 2], [2, 2, 2], (0, 1, 2))
    assert constant["agreement_rate"] == 1.0
    assert constant["cohen_kappa"] is None

    base = {
        "condition": "rag",
        "case_id": "T1",
        **{dimension: "2" for dimension in DIMENSIONS},
        "critical_failure": "false",
    }
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        duplicate_path = root / "duplicate.csv"
        write_csv(duplicate_path, [base, base])
        try:
            read_ratings(duplicate_path)
        except ValueError as exc:
            assert "duplicate key" in str(exc)
        else:
            raise AssertionError("duplicate key must fail")

        invalid_path = root / "invalid.csv"
        invalid = {**base, "support_relation": "3"}
        write_csv(invalid_path, [invalid])
        try:
            read_ratings(invalid_path)
        except ValueError as exc:
            assert "must be 0, 1, or 2" in str(exc)
        else:
            raise AssertionError("invalid score must fail")

        invalid_bool_path = root / "invalid-bool.csv"
        invalid_bool = {**base, "critical_failure": "unknown"}
        write_csv(invalid_bool_path, [invalid_bool])
        try:
            read_ratings(invalid_bool_path)
        except ValueError as exc:
            assert "must be true or false" in str(exc)
        else:
            raise AssertionError("invalid boolean must fail")

    rating = {field: (False if field == "critical_failure" else 2) for field in FIELDS}
    try:
        compare_ratings({("rag", "T1"): rating}, {("rag", "T2"): rating})
    except ValueError as exc:
        assert "rating key mismatch" in str(exc)
    else:
        raise AssertionError("key mismatch must fail")
    print("PASS: known/undefined kappa, duplicate keys, invalid values, and key mismatch")


def main() -> None:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rater-a", type=Path)
    parser.add_argument("--rater-b", type=Path)
    parser.add_argument("--json", type=Path, default=here / "medclaim-rater-agreement.json")
    parser.add_argument("--markdown", type=Path, default=here / "medclaim-rater-agreement.md")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_check()
        return
    if not args.rater_a or not args.rater_b:
        parser.error("--rater-a and --rater-b are required unless --self-test is used")

    metrics = compare_ratings(read_ratings(args.rater_a), read_ratings(args.rater_b))
    payload = {
        "rater_a": args.rater_a.name,
        "rater_b": args.rater_b.name,
        "metrics": metrics,
        "limitation": "Agreement describes rating consistency, not gold validity or clinical performance.",
    }
    args.json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.markdown.write_text(markdown_report(metrics, args.rater_a, args.rater_b), encoding="utf-8")
    print(
        f"items={metrics['item_count']} decisions={metrics['decision_count']} "
        f"overall_agreement={metrics['overall_agreement_rate']:.4f}"
    )
    print(f"wrote {args.json}")
    print(f"wrote {args.markdown}")


if __name__ == "__main__":
    main()
