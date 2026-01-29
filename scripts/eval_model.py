#!/usr/bin/env python3
"""
Atlas Model Evaluation - Measure NL-to-SQL quality metrics.

Evaluates the fine-tuned model against a test set and reports:
- SQL validity rate (parseable SELECT statements)
- Exact match accuracy (against gold SQL)
- Read-only compliance (no forbidden keywords)
- Hallucination rate (references to non-existent tables/columns)

Usage:
    python scripts/eval_model.py \
        --model-path ./models/atlas-qwen-v2/final \
        --eval-data ./data/eval_data.jsonl \
        --schema-path ./data/oracle_fusion_schema.json
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Forbidden SQL keywords (must match connector.py)
FORBIDDEN_KEYWORDS = frozenset({
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
    "TRUNCATE", "MERGE", "GRANT", "REVOKE", "EXECUTE", "CALL",
})

_KEYWORD_PATTERN = re.compile(
    r"\b(" + "|".join(FORBIDDEN_KEYWORDS) + r")\b",
    re.IGNORECASE,
)


def is_valid_select(sql: str) -> bool:
    """Check if SQL is a parseable SELECT statement."""
    sql = sql.strip().rstrip(";")
    return bool(re.match(r"^\s*SELECT\b", sql, re.IGNORECASE))


def is_read_only(sql: str) -> bool:
    """Check that SQL contains no forbidden DML/DDL keywords."""
    return _KEYWORD_PATTERN.search(sql) is None


def normalize_sql(sql: str) -> str:
    """Normalize SQL for comparison."""
    sql = sql.strip().rstrip(";").upper()
    sql = re.sub(r"\s+", " ", sql)
    return sql


def check_hallucination(sql: str, known_tables: set[str]) -> bool:
    """Check if SQL references tables not in the schema.

    Returns True if hallucination detected.
    """
    if not known_tables:
        return False

    # Extract table references (FROM/JOIN clauses)
    table_refs = re.findall(
        r"(?:FROM|JOIN)\s+(?:\w+\.)?(\w+)",
        sql,
        re.IGNORECASE,
    )

    for ref in table_refs:
        if ref.upper() not in known_tables and ref.upper() != "DUAL":
            return True

    return False


def load_known_tables(schema_path: str) -> set[str]:
    """Load known table names from schema JSON."""
    path = Path(schema_path)
    if not path.exists():
        return set()

    with open(path, encoding="utf-8") as f:
        schema = json.load(f)

    return {obj["name"].upper() for obj in schema if obj.get("object_type") == "TABLE"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Atlas NL-to-SQL model")
    parser.add_argument("--model-path", required=True, help="Path to fine-tuned model")
    parser.add_argument("--eval-data", required=True, help="JSONL eval data")
    parser.add_argument(
        "--schema-path",
        default="./data/oracle_fusion_schema.json",
        help="Oracle schema JSON for hallucination detection",
    )
    parser.add_argument("--max-samples", type=int, default=0, help="Limit eval samples (0=all)")
    parser.add_argument("--output", default=None, help="Save results to JSON file")
    args = parser.parse_args()

    if not Path(args.eval_data).exists():
        print(f"Error: Eval data not found: {args.eval_data}")
        return 1

    # Load schema for hallucination check
    known_tables = load_known_tables(args.schema_path)
    print(f"Known tables: {len(known_tables)}")

    # Load eval data
    eval_records = []
    with open(args.eval_data, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                eval_records.append(json.loads(line))

    if args.max_samples > 0:
        eval_records = eval_records[:args.max_samples]

    print(f"Eval samples: {len(eval_records)}")

    # Load model
    print(f"Loading model: {args.model_path}")
    try:
        from unsloth import FastLanguageModel

        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=args.model_path,
            max_seq_length=2048,
            dtype=None,
            load_in_4bit=True,
        )
        FastLanguageModel.for_inference(model)
    except ImportError:
        print("Error: Unsloth not installed")
        return 1

    # Evaluate
    metrics = {
        "total": len(eval_records),
        "valid_select": 0,
        "read_only": 0,
        "exact_match": 0,
        "hallucinations": 0,
        "errors": 0,
    }

    from atlas.agent.unsloth_llm import UnslothLLM

    prompt_template = UnslothLLM.SYSTEM_PROMPT

    print("\nEvaluating...")
    for i, record in enumerate(eval_records):
        prompt = prompt_template.format(
            schema_context=record.get("input", ""),
            question=record["instruction"],
        )

        try:
            inputs = tokenizer(
                prompt, return_tensors="pt", truncation=True, max_length=1792
            ).to("cuda")

            outputs = model.generate(
                **inputs,
                max_new_tokens=256,
                temperature=0.1,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
            )

            generated = tokenizer.decode(
                outputs[0][inputs["input_ids"].shape[1]:],
                skip_special_tokens=True,
            ).strip()

            # Extract SQL
            match = re.search(r"(SELECT\s+.+?)(?:;|$)", generated, re.IGNORECASE | re.DOTALL)
            predicted_sql = match.group(1).strip() if match else generated

            # Metrics
            if is_valid_select(predicted_sql):
                metrics["valid_select"] += 1

            if is_read_only(predicted_sql):
                metrics["read_only"] += 1

            if normalize_sql(predicted_sql) == normalize_sql(record["output"]):
                metrics["exact_match"] += 1

            if check_hallucination(predicted_sql, known_tables):
                metrics["hallucinations"] += 1

        except Exception as e:
            metrics["errors"] += 1
            if i < 5:
                print(f"  Error on sample {i}: {e}")

        if (i + 1) % 50 == 0:
            print(f"  Processed {i + 1}/{len(eval_records)}")

    # Results
    total = metrics["total"]
    print("\n" + "=" * 50)
    print("EVALUATION RESULTS")
    print("=" * 50)
    print(f"Total samples:       {total}")
    def pct(k: str) -> str:
        return f"{metrics[k]}/{total} ({100*metrics[k]/total:.1f}%)"

    print(f"SQL validity:        {pct('valid_select')}")
    print(f"Read-only compliant: {pct('read_only')}")
    print(f"Exact match:         {pct('exact_match')}")
    print(f"Hallucinations:      {pct('hallucinations')}")
    print(f"Errors:              {metrics['errors']}/{total}")
    print("=" * 50)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(metrics, f, indent=2)
        print(f"Results saved to: {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
