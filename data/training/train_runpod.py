#!/usr/bin/env python3
"""
Atlas NL-to-SQL Fine-tuning Script for RunPod

This script fine-tunes Qwen2.5 on Oracle Fusion NL-to-SQL data
using Unsloth for efficient training.

Usage on RunPod:
    python train_runpod.py --epochs 3 --batch_size 4
"""

import argparse
import os
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Atlas NL-to-SQL Fine-tuning")
    parser.add_argument("--model", default="unsloth/Qwen2.5-7B-bnb-4bit", help="Base model")
    parser.add_argument("--train_data", default="/workspace/Atlas/data/training/train.jsonl")
    parser.add_argument("--val_data", default="/workspace/Atlas/data/training/val.jsonl")
    parser.add_argument("--output_dir", default="/workspace/atlas_erp/models/atlas-qwen-oracle")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=4)
    parser.add_argument("--learning_rate", type=float, default=2e-4)
    parser.add_argument("--max_seq_length", type=int, default=2048)
    parser.add_argument("--lora_r", type=int, default=16)
    parser.add_argument("--lora_alpha", type=int, default=32)
    args = parser.parse_args()

    print("=" * 60)
    print("  Atlas NL-to-SQL Fine-tuning")
    print("  Powered by Unsloth + Qwen2.5")
    print("=" * 60)

    # Check for GPU
    import torch
    if not torch.cuda.is_available():
        print("ERROR: No GPU detected. This script requires CUDA.")
        return

    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

    # Import Unsloth
    try:
        from unsloth import FastLanguageModel
        from unsloth import is_bfloat16_supported
    except ImportError:
        print("Installing Unsloth...")
        os.system("pip install unsloth")
        from unsloth import FastLanguageModel
        from unsloth import is_bfloat16_supported

    # Load model
    print(f"\nLoading model: {args.model}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.model,
        max_seq_length=args.max_seq_length,
        dtype=None,
        load_in_4bit=True,
    )

    # Apply LoRA
    print(f"Applying LoRA (r={args.lora_r}, alpha={args.lora_alpha})")
    model = FastLanguageModel.get_peft_model(
        model,
        r=args.lora_r,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
        lora_alpha=args.lora_alpha,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=42,
    )

    # Load dataset
    from datasets import load_dataset

    print(f"\nLoading training data: {args.train_data}")
    dataset = load_dataset("json", data_files={
        "train": args.train_data,
        "validation": args.val_data,
    })

    # Format prompt
    alpaca_prompt = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{instruction}

### Input:
{input}

### Response:
{output}"""

    def formatting_prompts_func(examples):
        instructions = examples["instruction"]
        inputs = examples["input"]
        outputs = examples["output"]
        texts = []
        for instruction, input_text, output in zip(instructions, inputs, outputs):
            text = alpaca_prompt.format(
                instruction=instruction,
                input=input_text,
                output=output
            ) + tokenizer.eos_token
            texts.append(text)
        return {"text": texts}

    dataset = dataset.map(formatting_prompts_func, batched=True)

    # Training
    from trl import SFTTrainer
    from transformers import TrainingArguments

    print(f"\nStarting training...")
    print(f"  Epochs: {args.epochs}")
    print(f"  Batch size: {args.batch_size}")
    print(f"  Learning rate: {args.learning_rate}")

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        dataset_text_field="text",
        max_seq_length=args.max_seq_length,
        dataset_num_proc=2,
        packing=False,
        args=TrainingArguments(
            per_device_train_batch_size=args.batch_size,
            gradient_accumulation_steps=4,
            warmup_steps=5,
            num_train_epochs=args.epochs,
            learning_rate=args.learning_rate,
            fp16=not is_bfloat16_supported(),
            bf16=is_bfloat16_supported(),
            logging_steps=10,
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="linear",
            seed=42,
            output_dir=args.output_dir,
            save_strategy="epoch",
            evaluation_strategy="epoch",
        ),
    )

    trainer.train()

    # Save model
    print(f"\nSaving model to: {args.output_dir}/final")
    model.save_pretrained(f"{args.output_dir}/final")
    tokenizer.save_pretrained(f"{args.output_dir}/final")

    print("\n✅ Training complete!")
    print(f"Model saved to: {args.output_dir}/final")


if __name__ == "__main__":
    main()
