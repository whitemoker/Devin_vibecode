#!/usr/bin/env python3
"""
Main script for running the logistics status labeling pipeline.
Supports batch processing with checkpointing.
"""
import os
import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import DEFAULT_CONFIG, SINGLE_MODEL_CONFIG, PipelineConfig, ModelConfig
from pipeline import LabelingPipeline, LabelingTask, load_tasks_from_jsonl, load_tasks_from_csv
from evaluator import Evaluator, load_gold_labels


def create_config_from_args(args) -> PipelineConfig:
    """Create pipeline config from command line arguments."""
    models = []
    
    # Add OpenAI model if key is available
    if os.environ.get("OPENAI_API_KEY"):
        if args.model in ["gpt-4o", "all"]:
            models.append(ModelConfig(
                name="gpt-4o",
                provider="openai",
                model_id="gpt-4o",
                api_key_env="OPENAI_API_KEY",
                temperature=0.0,
                weight=1.2
            ))
        if args.model in ["gpt-4o-mini", "all"]:
            models.append(ModelConfig(
                name="gpt-4o-mini",
                provider="openai",
                model_id="gpt-4o-mini",
                api_key_env="OPENAI_API_KEY",
                temperature=0.0,
                weight=1.0
            ))
    
    # Add Anthropic model if key is available
    if os.environ.get("ANTHROPIC_API_KEY"):
        if args.model in ["claude", "all"]:
            models.append(ModelConfig(
                name="claude-sonnet",
                provider="anthropic",
                model_id="claude-sonnet-4-20250514",
                api_key_env="ANTHROPIC_API_KEY",
                temperature=0.0,
                weight=1.2
            ))
    
    if not models:
        raise ValueError("No API keys found! Set OPENAI_API_KEY or ANTHROPIC_API_KEY")
    
    return PipelineConfig(
        models=models,
        num_samples_per_model=args.num_samples,
        voting_strategy=args.voting,
        min_confidence_threshold=args.confidence_threshold,
        num_few_shot_examples=args.num_few_shot,
        use_retrieval_few_shot=True,
        enable_rule_validation=True,
        mark_low_confidence_for_human=True,
        batch_size=args.batch_size,
        save_checkpoint_every=args.checkpoint_every,
    )


def run_labeling(args):
    """Run the labeling pipeline."""
    logger.info("Starting labeling pipeline...")
    
    # Create config
    config = create_config_from_args(args)
    logger.info(f"Using models: {[m.name for m in config.models]}")
    
    # Initialize pipeline
    pipeline = LabelingPipeline(config, base_dir=str(project_root))
    
    # Load tasks
    input_path = Path(args.input)
    if input_path.suffix == ".jsonl":
        tasks = load_tasks_from_jsonl(str(input_path))
    elif input_path.suffix == ".csv":
        tasks = load_tasks_from_csv(
            str(input_path), 
            trace_column=args.trace_column,
            id_column=args.id_column
        )
    else:
        raise ValueError(f"Unsupported input format: {input_path.suffix}")
    
    logger.info(f"Loaded {len(tasks)} tasks from {input_path}")
    
    # Run labeling
    checkpoint_name = args.checkpoint or f"labeling_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    results = []
    for output in pipeline.label_batch(
        tasks,
        checkpoint_name=checkpoint_name,
        resume_from_checkpoint=args.resume
    ):
        results.append(output)
        
        if len(results) % 10 == 0:
            logger.info(f"Processed {len(results)} tasks...")
    
    # Save final results
    output_name = args.output or checkpoint_name
    output_path = pipeline.save_results(results, output_name, format=args.format)
    
    # Print statistics
    stats = pipeline.get_stats()
    logger.info("=" * 60)
    logger.info("Labeling Complete!")
    logger.info("=" * 60)
    logger.info(f"Total processed: {stats['total_processed']}")
    logger.info(f"Successful: {stats['successful']}")
    logger.info(f"Needs review: {stats['needs_review']}")
    logger.info(f"Failed: {stats['failed']}")
    logger.info(f"Results saved to: {output_path}")
    
    # Run evaluation if gold labels provided
    if args.gold_labels:
        logger.info("\nRunning evaluation...")
        gold_labels = load_gold_labels(
            args.gold_labels,
            id_column=args.id_column,
            label_column=args.label_column
        )
        
        eval_data = []
        for result in results:
            if result.task_id in gold_labels:
                eval_data.append({
                    'id': result.task_id,
                    'predicted': result.sub_status,
                    'gold': gold_labels[result.task_id],
                    'trace': result.trace[:200]
                })
        
        if eval_data:
            evaluator = Evaluator(taxonomy_manager=pipeline.taxonomy_manager)
            eval_result = evaluator.evaluate(eval_data)
            print(eval_result.summary)


def main():
    parser = argparse.ArgumentParser(
        description="Logistics Status Labeling Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Label a JSONL file with single model
  python run_labeling.py --input data.jsonl --model gpt-4o-mini

  # Label with multiple models and voting
  python run_labeling.py --input data.jsonl --model all --voting weighted_majority

  # Resume from checkpoint
  python run_labeling.py --input data.jsonl --checkpoint my_job --resume

  # Label and evaluate
  python run_labeling.py --input data.jsonl --gold-labels labels.csv
        """
    )
    
    # Input/Output
    parser.add_argument("--input", "-i", required=True, help="Input file (JSONL or CSV)")
    parser.add_argument("--output", "-o", help="Output name (default: auto-generated)")
    parser.add_argument("--format", choices=["jsonl", "csv"], default="jsonl", help="Output format")
    
    # Column names for CSV
    parser.add_argument("--trace-column", default="trace", help="Column name for trace text")
    parser.add_argument("--id-column", default="id", help="Column name for task ID")
    
    # Model settings
    parser.add_argument(
        "--model", 
        choices=["gpt-4o", "gpt-4o-mini", "claude", "all"],
        default="gpt-4o-mini",
        help="Model to use (or 'all' for multi-model voting)"
    )
    parser.add_argument("--num-samples", type=int, default=1, help="Samples per model for self-consistency")
    parser.add_argument("--num-few-shot", type=int, default=3, help="Number of few-shot examples")
    
    # Voting settings
    parser.add_argument(
        "--voting",
        choices=["majority", "weighted_majority", "unanimous"],
        default="weighted_majority",
        help="Voting strategy for multi-model"
    )
    parser.add_argument("--confidence-threshold", type=float, default=0.6, help="Min confidence threshold")
    
    # Checkpointing
    parser.add_argument("--checkpoint", help="Checkpoint name")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    parser.add_argument("--checkpoint-every", type=int, default=100, help="Save checkpoint every N tasks")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size")
    
    # Evaluation
    parser.add_argument("--gold-labels", help="Gold labels file for evaluation")
    parser.add_argument("--label-column", default="label", help="Column name for gold labels")
    
    args = parser.parse_args()
    
    try:
        run_labeling(args)
    except Exception as e:
        logger.error(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
