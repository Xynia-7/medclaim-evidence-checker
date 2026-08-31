#!/usr/bin/env python3
"""Retrieve MedClaim evidence chunks and evaluate paragraph-level ranking."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter
from pathlib import Path


CORPUS_REQUIRED = {
    "chunk_id",
    "source_title",
    "source_url",
    "source_version",
    "locator",
    "evidence_text",
}
PROMPT_REQUIRED = {"case_id", "medical_claim", "source_url"}
GOLD_REQUIRED = {"case_id", "gold_chunk_id"}


def read_rows(path: Path, required: set[str], allow_empty: set[str] | None = None) -> list[dict[str, str]]:
    allow_empty = allow_empty or set()
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = required - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"{path}: missing columns: {', '.join(sorted(missing))}")
        rows = list(reader)
    if not rows:
        raise ValueError(f"{path}: no data rows")
    for row in rows:
        for column in required - allow_empty:
            if not row[column].strip():
                raise ValueError(f"{path}: {column} cannot be empty")
    key = "chunk_id" if "chunk_id" in required else "case_id"
    duplicates = sorted(value for value, count in Counter(row[key] for row in rows).items() if count > 1)
    if duplicates:
        raise ValueError(f"{path}: duplicate {key}: {', '.join(duplicates)}")
    return rows


def tokenize(text: str) -> list[str]:
    lowered = text.lower().replace("–", "-").replace("—", "-")
    english = re.findall(r"[a-z0-9]+(?:[.+/-][a-z0-9]+)*", lowered)
    chinese = []
    for run in re.findall(r"[\u4e00-\u9fff]+", lowered):
        chinese.extend(run if len(run) == 1 else (run[index : index + 2] for index in range(len(run) - 1)))
    return english + chinese


def bm25_rank(query: str, candidates: list[dict[str, str]], corpus: list[dict[str, str]]) -> list[tuple[dict[str, str], float]]:
    document_tokens = [tokenize(row["evidence_text"]) for row in corpus]
    document_frequency = Counter(token for tokens in document_tokens for token in set(tokens))
    average_length = sum(map(len, document_tokens)) / len(document_tokens)
    token_map = {row["chunk_id"]: tokens for row, tokens in zip(corpus, document_tokens)}
    query_tokens = set(tokenize(query))
    scored = []
    for row in candidates:
        tokens = token_map[row["chunk_id"]]
        frequencies = Counter(tokens)
        score = 0.0
        for token in query_tokens:
            frequency = frequencies[token]
            if not frequency:
                continue
            df = document_frequency[token]
            inverse_frequency = math.log(1 + (len(corpus) - df + 0.5) / (df + 0.5))
            denominator = frequency + 1.5 * (1 - 0.75 + 0.75 * len(tokens) / average_length)
            score += inverse_frequency * frequency * 2.5 / denominator
        scored.append((row, score))
    return sorted(scored, key=lambda item: (-item[1], item[0]["chunk_id"]))


def retrieve(
    corpus: list[dict[str, str]],
    prompts: list[dict[str, str]],
    gold_rows: list[dict[str, str]],
    top_k: int = 3,
) -> tuple[list[dict], dict]:
    corpus_ids = {row["chunk_id"] for row in corpus}
    prompt_ids = {row["case_id"] for row in prompts}
    gold = {row["case_id"]: row["gold_chunk_id"] for row in gold_rows}
    if prompt_ids != set(gold):
        raise ValueError(f"holdout/gold case_id mismatch; missing={sorted(prompt_ids - set(gold))}, extra={sorted(set(gold) - prompt_ids)}")
    invalid_gold = sorted(chunk_id for chunk_id in gold.values() if chunk_id and chunk_id not in corpus_ids)
    if invalid_gold:
        raise ValueError(f"gold_chunk_id not in corpus: {', '.join(invalid_gold)}")

    results = []
    for prompt in prompts:
        candidates = [row for row in corpus if row["source_url"] == prompt["source_url"]]
        if not candidates:
            raise ValueError(f"{prompt['case_id']}: no corpus chunks for source_url")
        ranked = bm25_rank(prompt["medical_claim"], candidates, corpus)[:top_k]
        ranked_ids = [row["chunk_id"] for row, _ in ranked]
        expected = gold[prompt["case_id"]]
        rank = ranked_ids.index(expected) + 1 if expected in ranked_ids else None
        results.append(
            {
                "case_id": prompt["case_id"],
                "medical_claim": prompt["medical_claim"],
                "source_url": prompt["source_url"],
                "gold_chunk_id": expected,
                "rank": rank,
                "retrieved": [
                    {
                        "rank": index,
                        "chunk_id": row["chunk_id"],
                        "score": round(score, 6),
                        "source_title": row["source_title"],
                        "source_version": row["source_version"],
                        "locator": row["locator"],
                        "evidence_text": row["evidence_text"],
                    }
                    for index, (row, score) in enumerate(ranked, 1)
                ],
            }
        )

    evaluable = [row for row in results if row["gold_chunk_id"]]
    if not evaluable:
        raise ValueError("at least one case must have a gold_chunk_id for retrieval metrics")
    metrics = {
        "case_count": len(results),
        "evaluable_count": len(evaluable),
        "excluded_no_gold_count": len(results) - len(evaluable),
        "hit_at_1": round(sum(row["rank"] == 1 for row in evaluable) / len(evaluable), 4),
        "hit_at_3": round(sum(row["rank"] is not None and row["rank"] <= 3 for row in evaluable) / len(evaluable), 4),
        "mrr_at_3": round(sum(1 / row["rank"] if row["rank"] else 0 for row in evaluable) / len(evaluable), 4),
    }
    return results, metrics


def write_contexts(path: Path, results: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["case_id", "medical_claim", "source_url", "retrieved_context"])
        writer.writeheader()
        for result in results:
            context = "\n\n".join(
                f"[{item['chunk_id']}] {item['source_title']} | {item['source_version']} | {item['locator']}\n{item['evidence_text']}"
                for item in result["retrieved"]
            )
            writer.writerow(
                {
                    "case_id": result["case_id"],
                    "medical_claim": result["medical_claim"],
                    "source_url": result["source_url"],
                    "retrieved_context": context,
                }
            )


def write_private_csv(path: Path, results: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["case_id", "gold_chunk_id", "gold_rank", "top1_chunk_id", "top1_score", "hit_at_1", "hit_at_3"],
        )
        writer.writeheader()
        for result in results:
            top = result["retrieved"][0]
            writer.writerow(
                {
                    "case_id": result["case_id"],
                    "gold_chunk_id": result["gold_chunk_id"],
                    "gold_rank": result["rank"] or "",
                    "top1_chunk_id": top["chunk_id"],
                    "top1_score": top["score"],
                    "hit_at_1": result["rank"] == 1 if result["gold_chunk_id"] else "",
                    "hit_at_3": result["rank"] is not None if result["gold_chunk_id"] else "",
                }
            )


def markdown_report(metrics: dict, results: list[dict]) -> str:
    lines = [
        "# MedClaim BM25 检索报告",
        "",
        "范围：在给定 FDA/NCI/EMA 来源内部，对人工定位的中文证据块做段落级排序。",
        "",
        "## 结果",
        "",
        f"- Holdout：{metrics['case_count']} 条",
        f"- 可评病例：{metrics['evaluable_count']} 条；证据不足排除：{metrics['excluded_no_gold_count']} 条",
        f"- Hit@1：{metrics['hit_at_1']:.1%}",
        f"- Hit@3：{metrics['hit_at_3']:.1%}",
        f"- MRR@3：{metrics['mrr_at_3']:.4f}",
        "",
        "## 逐例",
        "",
        "| case_id | gold chunk | rank | Top-1 |",
        "|---|---|---:|---|",
    ]
    for result in results:
        lines.append(
            f"| {result['case_id']} | {result['gold_chunk_id'] or '不计分'} | "
            f"{result['rank'] or '—'} | {result['retrieved'][0]['chunk_id']} |"
        )
    lines += [
        "",
        "## 限制",
        "",
        "证据库只有 8 个经过人工筛选并中文转述的块，且检索先按用户给定来源 URL 过滤；高命中率只证明小型段落排序可运行，不代表开放网络检索、跨语言检索或临床可靠性。",
        "",
    ]
    return "\n".join(lines)


def self_check() -> None:
    corpus = [
        {"chunk_id": "A", "source_title": "T", "source_url": "u", "source_version": "v", "locator": "1", "evidence_text": "胃癌 HER2 剂量 6.4 mg/kg"},
        {"chunk_id": "B", "source_title": "T", "source_url": "u", "source_version": "v", "locator": "2", "evidence_text": "间质性肺病 安全性 10%"},
    ]
    prompts = [
        {"case_id": "P1", "medical_claim": "胃癌剂量是 6.4 mg/kg", "source_url": "u"},
        {"case_id": "P2", "medical_claim": "未报告的结局", "source_url": "u"},
    ]
    results, metrics = retrieve(corpus, prompts, [{"case_id": "P1", "gold_chunk_id": "A"}, {"case_id": "P2", "gold_chunk_id": ""}])
    assert results[0]["rank"] == 1
    assert metrics == {"case_count": 2, "evaluable_count": 1, "excluded_no_gold_count": 1, "hit_at_1": 1.0, "hit_at_3": 1.0, "mrr_at_3": 1.0}
    print("PASS: exact evidence ranks first; no-gold case is excluded from metrics")


def main() -> None:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=here / "medclaim-corpus-v0.1.csv")
    parser.add_argument("--prompts", type=Path, default=here / "medclaim-holdout-prompts-v0.1.csv")
    parser.add_argument("--gold", type=Path, default=here / "medclaim-holdout-gold-chunks-v0.1.csv")
    parser.add_argument("--contexts", type=Path, default=here / "medclaim-holdout-retrieved-context-v0.1.csv")
    parser.add_argument("--csv", type=Path, default=here / "medclaim-holdout-results-retrieval-v0.1.csv")
    parser.add_argument("--json", type=Path, default=here / "medclaim-holdout-results-retrieval-v0.1.json")
    parser.add_argument("--markdown", type=Path, default=here / "medclaim-holdout-results-retrieval-v0.1.md")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_check()
        return

    corpus = read_rows(args.corpus, CORPUS_REQUIRED)
    prompts = read_rows(args.prompts, PROMPT_REQUIRED)
    gold = read_rows(args.gold, GOLD_REQUIRED, allow_empty={"gold_chunk_id"})
    results, metrics = retrieve(corpus, prompts, gold)
    write_contexts(args.contexts, results)
    write_private_csv(args.csv, results)
    args.json.write_text(json.dumps({"metrics": metrics, "results": results}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.markdown.write_text(markdown_report(metrics, results), encoding="utf-8")
    print(
        f"cases={metrics['case_count']} evaluable={metrics['evaluable_count']} "
        f"hit@1={metrics['hit_at_1']:.4f} hit@3={metrics['hit_at_3']:.4f} mrr@3={metrics['mrr_at_3']:.4f}"
    )
    print(f"wrote public contexts: {args.contexts}")
    print(f"wrote private results: {args.csv}, {args.json}, {args.markdown}")


if __name__ == "__main__":
    main()
