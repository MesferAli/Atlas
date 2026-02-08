"""
Training Pipeline for Atlas NL-to-SQL

Complete pipeline for:
1. Building Knowledge Graph from Oracle Schema
2. Generating synthetic training data
3. Preparing data for fine-tuning
4. Running training on RunPod/local GPU

Based on GraphGen: https://github.com/InternScience/GraphGen
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from atlas.training.data_generator import TrainingDataGenerator
from atlas.training.knowledge_graph import OracleKnowledgeGraph


@dataclass
class PipelineConfig:
    """Configuration for the training pipeline."""
    # Input paths
    schema_path: str = "data/oracle_fusion_schema.json"

    # Output paths
    output_dir: str = "data/training"
    kg_output: str = "knowledge_graph.json"
    train_output: str = "train.jsonl"
    val_output: str = "val.jsonl"

    # Data generation settings
    simple_per_table: int = 15
    aggregate_per_table: int = 8
    top_n_per_table: int = 5
    join_count: int = 50

    # Train/validation split
    val_ratio: float = 0.1

    # Output format
    output_format: str = "alpaca"  # alpaca, sharegpt, completion


class TrainingPipeline:
    """
    End-to-end pipeline for generating NL-to-SQL training data.

    Usage:
        pipeline = TrainingPipeline(config)
        pipeline.run()
    """

    def __init__(self, config: PipelineConfig | None = None):
        """
        Initialize the pipeline.

        Args:
            config: Pipeline configuration (uses defaults if None)
        """
        self.config = config or PipelineConfig()
        self.kg: OracleKnowledgeGraph | None = None
        self.generator: TrainingDataGenerator | None = None
        self.stats: dict[str, Any] = {}

    def setup_directories(self) -> None:
        """Create output directories if they don't exist."""
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"Output directory: {output_dir.absolute()}")

    def build_knowledge_graph(self) -> OracleKnowledgeGraph:
        """Build the Knowledge Graph from Oracle Schema."""
        print("\n📊 Building Knowledge Graph...")

        self.kg = OracleKnowledgeGraph(self.config.schema_path)
        self.kg.load_schema()
        self.kg.build_graph()

        # Export KG
        kg_path = Path(self.config.output_dir) / self.config.kg_output
        self.kg.to_json(kg_path)

        stats = self.kg.get_graph_stats()
        print(f"   Nodes: {stats['total_nodes']}")
        print(f"   Edges: {stats['total_edges']}")
        print(f"   Domains: {', '.join(stats['domains'])}")
        print(f"   Exported to: {kg_path}")

        self.stats["knowledge_graph"] = stats
        return self.kg

    def generate_training_data(self) -> list:
        """Generate synthetic training data."""
        if not self.kg:
            raise RuntimeError("Knowledge Graph not built. Call build_knowledge_graph() first.")

        print("\n🔧 Generating Training Data...")

        self.generator = TrainingDataGenerator(self.kg)
        examples = self.generator.generate_all(
            simple_per_table=self.config.simple_per_table,
            aggregate_per_table=self.config.aggregate_per_table,
            top_n_per_table=self.config.top_n_per_table,
            join_count=self.config.join_count,
        )

        stats = self.generator.get_stats()
        print(f"   Total examples: {stats['total_examples']}")
        print(f"   By complexity: {stats['by_complexity']}")
        print(f"   By domain: {stats['by_domain']}")

        self.stats["data_generation"] = stats
        return examples

    def split_and_export(self) -> tuple[Path, Path]:
        """Split data into train/validation and export to JSONL."""
        if not self.generator or not self.generator.examples:
            raise RuntimeError("No examples generated. Call generate_training_data() first.")

        print("\n💾 Splitting and Exporting Data...")

        import random
        examples = self.generator.examples.copy()
        random.shuffle(examples)

        # Split
        val_size = int(len(examples) * self.config.val_ratio)
        val_examples = examples[:val_size]
        train_examples = examples[val_size:]

        print(f"   Training examples: {len(train_examples)}")
        print(f"   Validation examples: {len(val_examples)}")

        # Export training data
        train_path = Path(self.config.output_dir) / self.config.train_output
        self._export_examples(train_examples, train_path)

        # Export validation data
        val_path = Path(self.config.output_dir) / self.config.val_output
        self._export_examples(val_examples, val_path)

        self.stats["export"] = {
            "train_examples": len(train_examples),
            "val_examples": len(val_examples),
            "train_path": str(train_path),
            "val_path": str(val_path),
        }

        return train_path, val_path

    def _export_examples(self, examples: list, output_path: Path) -> None:
        """Export examples to JSONL file."""
        with open(output_path, "w", encoding="utf-8") as f:
            for example in examples:
                if self.config.output_format == "alpaca":
                    record = {
                        "instruction": (
                            "أنت خبير في Oracle SQL. اكتب استعلام SQL للسؤال التالي.\n"
                            "You are an Oracle SQL expert. Write a SQL query for the following question."
                        ),
                        "input": f"Question (EN): {example.question_en}\nQuestion (AR): {example.question_ar}",
                        "output": example.sql,
                    }
                elif self.config.output_format == "sharegpt":
                    record = {
                        "conversations": [
                            {"from": "human", "value": f"{example.question_en}\n{example.question_ar}"},
                            {"from": "gpt", "value": example.sql},
                        ]
                    }
                else:
                    record = {
                        "prompt": f"Question: {example.question_en}\nسؤال: {example.question_ar}\n\nSQL:",
                        "completion": f" {example.sql}",
                    }

                f.write(json.dumps(record, ensure_ascii=False) + "\n")

        print(f"   Exported to: {output_path}")

    def generate_runpod_script(self) -> Path:
        """Generate a RunPod training script."""
        print("\n🚀 Generating RunPod Training Script...")

        script_path = Path(self.config.output_dir) / "train_runpod.py"

        script_content = '''#!/usr/bin/env python3
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
    print(f"\\nLoading model: {args.model}")
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

    print(f"\\nLoading training data: {args.train_data}")
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

    print(f"\\nStarting training...")
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
    print(f"\\nSaving model to: {args.output_dir}/final")
    model.save_pretrained(f"{args.output_dir}/final")
    tokenizer.save_pretrained(f"{args.output_dir}/final")

    print("\\n✅ Training complete!")
    print(f"Model saved to: {args.output_dir}/final")


if __name__ == "__main__":
    main()
'''

        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_content)

        # Make executable
        os.chmod(script_path, 0o755)

        print(f"   Script saved to: {script_path}")
        self.stats["runpod_script"] = str(script_path)

        return script_path

    def run(self) -> dict[str, Any]:
        """
        Run the complete pipeline.

        Returns:
            Dictionary with pipeline statistics
        """
        start_time = datetime.now()
        print("=" * 60)
        print("  Atlas Training Pipeline")
        print("  GraphGen-based NL-to-SQL Data Generation")
        print("=" * 60)

        # Setup
        self.setup_directories()

        # Build Knowledge Graph
        self.build_knowledge_graph()

        # Generate training data
        self.generate_training_data()

        # Split and export
        train_path, val_path = self.split_and_export()

        # Generate RunPod script
        self.generate_runpod_script()

        # Summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print("\n" + "=" * 60)
        print("  Pipeline Complete!")
        print("=" * 60)
        print(f"  Duration: {duration:.1f} seconds")
        print(f"  Training data: {train_path}")
        print(f"  Validation data: {val_path}")
        print("\n  Next steps:")
        print("  1. Upload data/training/ to RunPod")
        print("  2. Run: python train_runpod.py")
        print("  3. Download trained model")
        print("=" * 60)

        self.stats["duration_seconds"] = duration
        self.stats["completed_at"] = end_time.isoformat()

        # Save stats
        stats_path = Path(self.config.output_dir) / "pipeline_stats.json"
        with open(stats_path, "w", encoding="utf-8") as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)

        return self.stats


def run_pipeline(
    schema_path: str = "data/oracle_fusion_schema.json",
    output_dir: str = "data/training",
) -> dict[str, Any]:
    """
    Convenience function to run the complete pipeline.

    Args:
        schema_path: Path to Oracle Fusion schema JSON
        output_dir: Directory for output files

    Returns:
        Pipeline statistics
    """
    config = PipelineConfig(
        schema_path=schema_path,
        output_dir=output_dir,
    )
    pipeline = TrainingPipeline(config)
    return pipeline.run()
