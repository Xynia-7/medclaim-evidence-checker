#!/usr/bin/env python3
"""Run one isolated MedClaim model condition without reading holdout gold."""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path


LABELS = {"支持", "部分支持", "不支持", "证据不足"}
SAFE_NAME = re.compile(r"^[A-Za-z0-9._-]+$")
COMMON = """你是医疗主张证据关系检查器，服务对象是医学内容审核人员，不是患者。
对每条输入拆分独立原子主张，然后只选一个标签：支持、部分支持、不支持、证据不足。
支持=全部重要原子主张均受证据支持；部分支持=正确与错误或缺证据的重要主张并存但核心临床行动含义未反转；不支持=决定性人群、线别、适应证、剂量、研究设计或关键数字与证据矛盾；证据不足=没有决定性直接矛盾，但所需结局、时间点、亚组或比较未报告。
不得编造来源、章节、页码、chunk_id或数字，不得给个体化建议。每个case_id恰好一次并保持顺序，只返回符合schema的JSON对象，唯一顶层字段为predictions。
"""


def load_cases(root: Path, condition: str) -> list[dict[str, str]]:
    names = (
        ("medclaim-holdout-prompts-v0.1.csv", "medclaim-holdout-prompts-open-review-v0.1.csv")
        if condition == "no-retrieval"
        else (
            "medclaim-holdout-retrieved-context-v0.1.csv",
            "medclaim-holdout-retrieved-context-open-review-v0.1.csv",
        )
    )
    cases: list[dict[str, str]] = []
    for name in names:
        with (root / name).open(newline="", encoding="utf-8-sig") as handle:
            cases.extend(dict(row) for row in csv.DictReader(handle))
    return cases


def build_prompt(cases: list[dict[str, str]], condition: str) -> str:
    if condition == "no-retrieval":
        rule = (
            "不能打开链接、不能使用工具、不能读取本地文件。可以用已有知识识别明显矛盾，"
            "但不得假装访问来源；无法可靠核验时选证据不足。evidence_locator写‘未访问来源’。"
        )
    else:
        rule = (
            "仅依据每条病例自己的retrieved_context判断，不得使用记忆补齐；上下文缺信息时选证据不足。"
            "evidence_locator只能引用该病例retrieved_context内的chunk_id、版本和定位。"
        )
    return f"{COMMON}{rule}\n输入如下：\n{json.dumps(cases, ensure_ascii=False)}\n"


def validate_output(path: Path, expected_ids: list[str]) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    predictions = payload.get("predictions") if isinstance(payload, dict) else None
    if not isinstance(predictions, list):
        raise ValueError("output must contain a predictions array")
    ids = [item.get("case_id") for item in predictions if isinstance(item, dict)]
    if ids != expected_ids:
        raise ValueError(f"case order mismatch: expected={expected_ids}, actual={ids}")
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate case_id")
    invalid = [item.get("label") for item in predictions if item.get("label") not in LABELS]
    if invalid:
        raise ValueError(f"invalid labels: {invalid}")


def self_test() -> None:
    cases = [{"case_id": "MH001", "medical_claim": "测试", "source_url": "https://example.test"}]
    assert "不能打开链接" in build_prompt(cases, "no-retrieval")
    assert "仅依据每条病例自己的retrieved_context" in build_prompt(cases, "rag")
    with tempfile.TemporaryDirectory() as temp:
        output = Path(temp) / "output.json"
        output.write_text(
            json.dumps({"predictions": [{"case_id": "MH001", "label": "证据不足"}]}),
            encoding="utf-8",
        )
        validate_output(output, ["MH001"])
    print("PASS: prompts differ by condition; ordered structured output is accepted")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("condition", nargs="?", choices=("no-retrieval", "rag"))
    parser.add_argument("run_id", nargs="?")
    parser.add_argument("--model", default="gpt-5.6-sol")
    parser.add_argument("--effort", choices=("low", "medium", "high", "xhigh"), default="low")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.condition or not args.run_id:
        parser.error("condition and run_id are required unless --self-test is used")
    if not SAFE_NAME.fullmatch(args.run_id) or not SAFE_NAME.fullmatch(args.model):
        parser.error("run_id and model may contain only letters, digits, dot, underscore, and hyphen")

    root = Path(__file__).resolve().parent
    cases = load_cases(root, args.condition)
    expected_ids = [f"MH{index:03d}" for index in range(1, 21)]
    actual_ids = [case.get("case_id") for case in cases]
    if actual_ids != expected_ids:
        raise ValueError(f"input case order mismatch: {actual_ids}")
    output = root / f"medclaim-model-output-{args.condition}-{args.model}-{args.run_id}.json"
    if output.exists() and not args.overwrite:
        raise FileExistsError(f"refusing to overwrite {output.name}; pass --overwrite explicitly")
    codex = shutil.which("codex")
    if not codex:
        raise FileNotFoundError("codex CLI is not available")

    command = [
        codex,
        "exec",
        "--ignore-user-config",
        "--ephemeral",
        "--model",
        args.model,
        "-c",
        f"model_reasoning_effort={args.effort}",
        "--sandbox",
        "read-only",
        "--skip-git-repo-check",
        "--output-schema",
        str(root / "medclaim-model-output-schema.json"),
        "--color",
        "never",
        "-o",
        str(output),
        "-",
    ]
    started = time.monotonic()
    with tempfile.TemporaryDirectory() as temp:
        subprocess.run(command, input=build_prompt(cases, args.condition), text=True, cwd=temp, check=True)
    validate_output(output, expected_ids)
    print(f"PASS: {args.condition} {args.run_id}, 20 ordered cases, {time.monotonic() - started:.1f}s")


if __name__ == "__main__":
    main()
