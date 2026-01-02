"""
Main pipeline orchestrator for logistics status labeling.
Handles batch processing, checkpointing, and result aggregation.
"""
import os
import json
import logging
import time
from typing import Dict, List, Optional, Any, Iterator
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from config import PipelineConfig, ModelConfig
from taxonomy_manager import TaxonomyManager
from few_shot_retriever import FewShotRetriever
from preprocessor import TracePreprocessor
from labeler import SingleModelLabeler, LabelPrediction, LabelResult
from llm_client import LLMClientFactory, MultiModelClient
from voting import VotingFactory

logger = logging.getLogger(__name__)


@dataclass
class LabelingTask:
    """A single labeling task."""
    id: str
    trace: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class LabelingOutput:
    """Output for a single labeling task."""
    task_id: str
    trace: str
    main_status: str
    sub_status: str
    confidence: float
    evidence: List[str]
    explanation: str
    needs_human_review: bool
    review_reason: str
    voting_details: Dict[str, Any]
    predictions: List[Dict]
    metadata: Dict[str, Any]
    timestamp: str


class LabelingPipeline:
    """Main pipeline for batch labeling of logistics traces."""
    
    def __init__(self, config: PipelineConfig, base_dir: str = "."):
        self.config = config
        self.base_dir = Path(base_dir)
        
        # Initialize components
        self.taxonomy_manager = TaxonomyManager(
            str(self.base_dir / config.taxonomy_path)
        )
        self.few_shot_retriever = FewShotRetriever(
            str(self.base_dir / config.sample_cases_path)
        )
        self.preprocessor = TracePreprocessor()
        
        # Initialize voting strategy
        self.voting_strategy = VotingFactory.create(config.voting_strategy)
        
        # Initialize model clients and labelers
        self.model_clients: Dict[str, Any] = {}
        self.labelers: Dict[str, SingleModelLabeler] = {}
        self.model_weights: Dict[str, float] = {}
        
        self._initialize_models()
        
        # Create output directories
        self.output_dir = self.base_dir / config.output_dir
        self.checkpoint_dir = self.base_dir / config.checkpoint_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.stats = {
            "total_processed": 0,
            "successful": 0,
            "needs_review": 0,
            "failed": 0,
            "by_status": {},
        }
    
    def _initialize_models(self):
        """Initialize LLM clients and labelers for each configured model."""
        for model_config in self.config.models:
            try:
                client = LLMClientFactory.create(
                    provider=model_config.provider,
                    model=model_config.model_id,
                    api_key_env=model_config.api_key_env,
                    base_url=model_config.base_url
                )
                
                labeler = SingleModelLabeler(
                    client=client,
                    model_name=model_config.name,
                    taxonomy_manager=self.taxonomy_manager,
                    few_shot_retriever=self.few_shot_retriever,
                    preprocessor=self.preprocessor,
                    num_few_shot=self.config.num_few_shot_examples,
                    use_retrieval=self.config.use_retrieval_few_shot,
                    temperature=model_config.temperature,
                    max_tokens=model_config.max_tokens,
                )
                
                self.model_clients[model_config.name] = client
                self.labelers[model_config.name] = labeler
                self.model_weights[model_config.name] = model_config.weight
                
                logger.info(f"Initialized model: {model_config.name}")
                
            except Exception as e:
                logger.warning(f"Failed to initialize model {model_config.name}: {e}")
    
    def label_single(self, task: LabelingTask) -> LabelingOutput:
        """Label a single trace using all configured models."""
        all_predictions: List[LabelPrediction] = []
        
        # Get predictions from each model
        for model_name, labeler in self.labelers.items():
            try:
                predictions = labeler.label(
                    task.trace, 
                    num_samples=self.config.num_samples_per_model
                )
                all_predictions.extend(predictions)
            except Exception as e:
                logger.error(f"Error from model {model_name} on task {task.id}: {e}")
        
        # Vote on the predictions
        result = self.voting_strategy.vote(all_predictions, self.model_weights)
        
        # Apply confidence threshold
        if result.confidence < self.config.min_confidence_threshold:
            result.needs_human_review = True
            if not result.review_reason:
                result.review_reason = f"Below confidence threshold: {result.confidence:.2f}"
        
        # Create output
        output = LabelingOutput(
            task_id=task.id,
            trace=task.trace,
            main_status=result.main_status,
            sub_status=result.sub_status,
            confidence=result.confidence,
            evidence=result.evidence,
            explanation=result.explanation,
            needs_human_review=result.needs_human_review,
            review_reason=result.review_reason,
            voting_details=result.voting_details,
            predictions=[
                {
                    "model": p.model_name,
                    "sub_status": p.sub_status,
                    "confidence": p.confidence,
                    "explanation": p.explanation,
                    "is_valid": p.is_valid,
                }
                for p in result.predictions
            ],
            metadata=task.metadata,
            timestamp=datetime.now().isoformat()
        )
        
        # Update statistics
        self._update_stats(output)
        
        return output
    
    def label_batch(
        self, 
        tasks: List[LabelingTask],
        checkpoint_name: Optional[str] = None,
        resume_from_checkpoint: bool = True
    ) -> Iterator[LabelingOutput]:
        """Label a batch of traces with checkpointing support."""
        
        # Load checkpoint if exists
        processed_ids = set()
        if checkpoint_name and resume_from_checkpoint:
            checkpoint_path = self.checkpoint_dir / f"{checkpoint_name}.json"
            if checkpoint_path.exists():
                with open(checkpoint_path, 'r', encoding='utf-8') as f:
                    checkpoint_data = json.load(f)
                    processed_ids = set(checkpoint_data.get("processed_ids", []))
                    self.stats = checkpoint_data.get("stats", self.stats)
                logger.info(f"Resumed from checkpoint: {len(processed_ids)} already processed")
        
        # Process tasks
        results = []
        for i, task in enumerate(tasks):
            # Skip if already processed
            if task.id in processed_ids:
                continue
            
            try:
                output = self.label_single(task)
                results.append(output)
                processed_ids.add(task.id)
                
                yield output
                
                # Save checkpoint periodically
                if checkpoint_name and (i + 1) % self.config.save_checkpoint_every == 0:
                    self._save_checkpoint(checkpoint_name, processed_ids, results)
                    logger.info(f"Checkpoint saved: {len(processed_ids)} processed")
                
            except Exception as e:
                logger.error(f"Error processing task {task.id}: {e}")
                self.stats["failed"] += 1
        
        # Final checkpoint
        if checkpoint_name:
            self._save_checkpoint(checkpoint_name, processed_ids, results)
    
    def _save_checkpoint(
        self, 
        checkpoint_name: str, 
        processed_ids: set,
        results: List[LabelingOutput]
    ):
        """Save checkpoint to disk."""
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_name}.json"
        
        checkpoint_data = {
            "processed_ids": list(processed_ids),
            "stats": self.stats,
            "last_updated": datetime.now().isoformat(),
        }
        
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
        
        # Also save results
        results_path = self.output_dir / f"{checkpoint_name}_results.jsonl"
        with open(results_path, 'a', encoding='utf-8') as f:
            for result in results:
                f.write(json.dumps(asdict(result), ensure_ascii=False) + '\n')
    
    def _update_stats(self, output: LabelingOutput):
        """Update statistics."""
        self.stats["total_processed"] += 1
        
        if output.sub_status:
            self.stats["successful"] += 1
            
            if output.sub_status not in self.stats["by_status"]:
                self.stats["by_status"][output.sub_status] = 0
            self.stats["by_status"][output.sub_status] += 1
        else:
            self.stats["failed"] += 1
        
        if output.needs_human_review:
            self.stats["needs_review"] += 1
    
    def get_stats(self) -> Dict:
        """Get current statistics."""
        return self.stats.copy()
    
    def save_results(
        self, 
        results: List[LabelingOutput], 
        output_name: str,
        format: str = "jsonl"
    ):
        """Save results to file."""
        if format == "jsonl":
            output_path = self.output_dir / f"{output_name}.jsonl"
            with open(output_path, 'w', encoding='utf-8') as f:
                for result in results:
                    f.write(json.dumps(asdict(result), ensure_ascii=False) + '\n')
        
        elif format == "csv":
            import csv
            output_path = self.output_dir / f"{output_name}.csv"
            
            fieldnames = [
                "task_id", "main_status", "sub_status", "confidence",
                "needs_human_review", "review_reason", "explanation", "timestamp"
            ]
            
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for result in results:
                    writer.writerow({
                        "task_id": result.task_id,
                        "main_status": result.main_status,
                        "sub_status": result.sub_status,
                        "confidence": result.confidence,
                        "needs_human_review": result.needs_human_review,
                        "review_reason": result.review_reason,
                        "explanation": result.explanation,
                        "timestamp": result.timestamp,
                    })
        
        logger.info(f"Results saved to {output_path}")
        return str(output_path)


def load_tasks_from_jsonl(file_path: str) -> List[LabelingTask]:
    """Load tasks from a JSONL file."""
    tasks = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            data = json.loads(line)
            task = LabelingTask(
                id=data.get("id", str(i)),
                trace=data.get("trace", data.get("text", "")),
                metadata=data.get("metadata", {})
            )
            tasks.append(task)
    return tasks


def load_tasks_from_csv(file_path: str, trace_column: str = "trace", id_column: str = "id") -> List[LabelingTask]:
    """Load tasks from a CSV file."""
    import csv
    tasks = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            task = LabelingTask(
                id=row.get(id_column, str(i)),
                trace=row.get(trace_column, ""),
                metadata={k: v for k, v in row.items() if k not in [id_column, trace_column]}
            )
            tasks.append(task)
    return tasks
