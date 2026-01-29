#!/usr/bin/env python3
"""
Atlas Fine-Tuning Script - Qwen NL-to-SQL via Unsloth QLoRA.

Optimized for 500K Saudi business market records on RunPod GPU instances.
Uses QLoRA (4-bit) to minimize VRAM while preserving quality.

Usage:
    # Basic training (auto-detects GPU)
    python scripts/train_model.py --data-path ./data/training_data.jsonl

    # Full config
    python scripts/train_model.py \
        --data-path ./data/training_data.jsonl \
        --output-dir ./models/atlas-qwen-v2 \
        --base-model unsloth/Qwen2.5-7B-bnb-4bit \
        --epochs 3 \
        --batch-size 4 \
        --lr 2e-4

    # Resume from checkpoint
    python scripts/train_model.py \
        --data-path ./data/training_data.jsonl \
        --resume-from ./models/atlas-qwen-v2/checkpoint-5000

Environment Variables:
    WANDB_PROJECT: W&B project name for experiment tracking
    WANDB_API_KEY: W&B API key (optional, disables tracking if unset)
    HF_TOKEN: HuggingFace token for gated models
"""

import argparse
import json
import os
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fine-tune Qwen for Atlas NL-to-SQL via Unsloth QLoRA"
    )
    parser.add_argument(
        "--data-path",
        required=True,
        help="Path to training data (JSONL with 'instruction', 'input', 'output' fields)",
    )
    parser.add_argument(
        "--eval-path",
        default=None,
        help="Path to evaluation data (same format). If not set, splits from training data.",
    )
    parser.add_argument(
        "--output-dir",
        default="./models/atlas-qwen-v2",
        help="Directory to save fine-tuned model",
    )
    parser.add_argument(
        "--base-model",
        default="unsloth/Qwen2.5-7B-bnb-4bit",
        help="Base model ID (HuggingFace or local path)",
    )
    parser.add_argument(
        "--max-seq-length",
        type=int,
        default=2048,
        help="Maximum sequence length",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=3,
        help="Number of training epochs",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=4,
        help="Per-device training batch size",
    )
    parser.add_argument(
        "--gradient-accumulation",
        type=int,
        default=4,
        help="Gradient accumulation steps (effective batch = batch-size * this)",
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=2e-4,
        help="Learning rate",
    )
    parser.add_argument(
        "--lora-r",
        type=int,
        default=16,
        help="LoRA rank",
    )
    parser.add_argument(
        "--lora-alpha",
        type=int,
        default=32,
        help="LoRA alpha (scaling = alpha/r, default 32/16 = 2x)",
    )
    parser.add_argument(
        "--lora-dropout",
        type=float,
        default=0.0,
        help="LoRA dropout (0.0 recommended for QLoRA)",
    )
    parser.add_argument(
        "--eval-split",
        type=float,
        default=0.05,
        help="Fraction of data for evaluation if --eval-path not set",
    )
    parser.add_argument(
        "--save-steps",
        type=int,
        default=500,
        help="Save checkpoint every N steps",
    )
    parser.add_argument(
        "--resume-from",
        default=None,
        help="Resume training from checkpoint directory",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed",
    )
    return parser.parse_args()


# Atlas bilingual prompt template for training
PROMPT_TEMPLATE = """أنت خبير في Oracle SQL. مهمتك كتابة استعلام SQL.
You are an Oracle SQL Expert. Write a SQL query.

القواعد / Rules:
- اكتب فقط استعلامات SELECT
- Write ONLY SELECT queries (no INSERT, UPDATE, DELETE, DROP)
- Use proper Oracle SQL syntax
- Return only the SQL query, no explanations

الجداول المتاحة / Available Tables:
{schema_context}

سؤال المستخدم / User Question: {question}

SQL Query:
{sql}"""

EOS_TOKEN = ""  # Set after tokenizer loads


def format_training_example(example: dict) -> dict:
    """Format a single training example into the prompt template."""
    text = PROMPT_TEMPLATE.format(
        schema_context=example.get("input", example.get("schema_context", "")),
        question=example["instruction"],
        sql=example["output"],
    ) + EOS_TOKEN
    return {"text": text}


def load_dataset_from_jsonl(path: str) -> list[dict]:
    """Load JSONL training data."""
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    print(f"Loaded {len(records):,} records from {path}")
    return records


def _gpu_supports_bf16() -> bool:
    """Check if the current GPU supports bfloat16 (A100, H100, L40, etc.).

    bf16 is faster and more numerically stable than fp16 on Ampere+ GPUs.
    Falls back to fp16 on older hardware (V100, T4).
    """
    try:
        import torch

        if torch.cuda.is_available():
            cap = torch.cuda.get_device_capability()
            # Ampere (sm_80+) supports bf16 natively
            return cap[0] >= 8
    except ImportError:
        pass
    return False


def main() -> int:
    args = parse_args()
    global EOS_TOKEN

    # Validate data path
    if not Path(args.data_path).exists():
        print(f"Error: Training data not found: {args.data_path}")
        return 1

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Atlas Fine-Tuning — Qwen NL-to-SQL (QLoRA)")
    print("=" * 60)
    print(f"Base model:      {args.base_model}")
    print(f"Data:            {args.data_path}")
    print(f"Output:          {args.output_dir}")
    print(f"Epochs:          {args.epochs}")
    print(f"Batch size:      {args.batch_size} (x{args.gradient_accumulation} accum)")
    print(f"Effective batch: {args.batch_size * args.gradient_accumulation}")
    print(f"Learning rate:   {args.lr}")
    use_bf16 = _gpu_supports_bf16()
    print(f"LoRA rank:       {args.lora_r}, alpha: {args.lora_alpha}")
    print(f"LoRA scaling:    {args.lora_alpha / args.lora_r:.1f}x")
    print(f"Max seq length:  {args.max_seq_length}")
    print(f"Precision:       {'bf16' if use_bf16 else 'fp16'}")
    print("=" * 60)

    # Step 1: Load model
    print("\n[1/5] Loading base model...")
    from unsloth import FastLanguageModel

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.base_model,
        max_seq_length=args.max_seq_length,
        dtype=None,  # auto-detect (float16 on V100, bfloat16 on A100+)
        load_in_4bit=True,
    )

    EOS_TOKEN = tokenizer.eos_token or ""

    # Step 2: Apply LoRA adapters
    print("\n[2/5] Applying QLoRA adapters...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        bias="none",
        use_gradient_checkpointing="unsloth",  # 60% less VRAM
        random_state=args.seed,
    )

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    print(f"Trainable params: {trainable:,} / {total:,} ({100*trainable/total:.2f}%)")

    # Step 3: Load and format dataset
    print("\n[3/5] Loading and formatting dataset...")
    from datasets import Dataset

    raw_data = load_dataset_from_jsonl(args.data_path)

    if args.eval_path:
        train_data = raw_data
        eval_data = load_dataset_from_jsonl(args.eval_path)
    else:
        import random

        random.seed(args.seed)
        random.shuffle(raw_data)
        split_idx = int(len(raw_data) * (1 - args.eval_split))
        train_data = raw_data[:split_idx]
        eval_data = raw_data[split_idx:]
        print(f"Split: {len(train_data):,} train / {len(eval_data):,} eval")

    train_dataset = Dataset.from_list([format_training_example(ex) for ex in train_data])
    eval_dataset = Dataset.from_list([format_training_example(ex) for ex in eval_data])

    # Step 4: Training
    print("\n[4/5] Starting training...")
    from transformers import TrainingArguments
    from trl import SFTTrainer

    # Disable W&B if no API key
    if not os.getenv("WANDB_API_KEY"):
        os.environ["WANDB_DISABLED"] = "true"

    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation,
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        warmup_ratio=0.05,
        weight_decay=0.01,
        fp16=not _gpu_supports_bf16(),
        bf16=_gpu_supports_bf16(),
        logging_steps=10,
        save_steps=args.save_steps,
        save_total_limit=3,
        eval_strategy="steps",
        eval_steps=args.save_steps,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        optim="adamw_8bit",
        seed=args.seed,
        report_to="wandb" if os.getenv("WANDB_API_KEY") else "none",
        gradient_checkpointing=True,
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        dataset_text_field="text",
        max_seq_length=args.max_seq_length,
        packing=True,  # Pack short examples together for efficiency
        args=training_args,
    )

    if args.resume_from:
        print(f"Resuming from checkpoint: {args.resume_from}")
        trainer.train(resume_from_checkpoint=args.resume_from)
    else:
        trainer.train()

    # Step 5: Save final model
    print("\n[5/5] Saving model...")
    final_dir = output_dir / "final"
    model.save_pretrained(final_dir)
    tokenizer.save_pretrained(final_dir)

    # Save training config for reproducibility
    config = {
        "base_model": args.base_model,
        "data_path": args.data_path,
        "train_records": len(train_data),
        "eval_records": len(eval_data),
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "gradient_accumulation": args.gradient_accumulation,
        "effective_batch_size": args.batch_size * args.gradient_accumulation,
        "learning_rate": args.lr,
        "lora_r": args.lora_r,
        "lora_alpha": args.lora_alpha,
        "max_seq_length": args.max_seq_length,
        "seed": args.seed,
    }
    with open(final_dir / "training_config.json", "w") as f:
        json.dump(config, f, indent=2)

    print(f"\nModel saved to: {final_dir}")
    print("=" * 60)
    print("Training complete!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
