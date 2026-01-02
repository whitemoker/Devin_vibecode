"""
Evaluation module for assessing labeling quality.
"""
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Results of evaluation."""
    accuracy: float
    macro_f1: float
    micro_f1: float
    per_class_metrics: Dict[str, Dict[str, float]]
    confusion_matrix: Dict[str, Dict[str, int]]
    hierarchical_accuracy: float  # Main status correct
    error_analysis: List[Dict]
    summary: str


class Evaluator:
    """Evaluates labeling quality against gold labels."""
    
    def __init__(self, taxonomy_manager=None):
        self.taxonomy_manager = taxonomy_manager
    
    def evaluate(
        self,
        predictions: List[Dict],  # List of {"id": ..., "predicted": ..., "gold": ...}
        include_error_analysis: bool = True,
        max_errors_to_show: int = 20
    ) -> EvaluationResult:
        """
        Evaluate predictions against gold labels.
        
        Args:
            predictions: List of dicts with "predicted" and "gold" sub_status codes
            include_error_analysis: Whether to include detailed error analysis
            max_errors_to_show: Maximum number of errors to include in analysis
        """
        # Initialize counters
        correct = 0
        total = 0
        main_correct = 0
        
        # Per-class counters
        true_positives = defaultdict(int)
        false_positives = defaultdict(int)
        false_negatives = defaultdict(int)
        
        # Confusion matrix
        confusion = defaultdict(lambda: defaultdict(int))
        
        # Error cases
        errors = []
        
        for pred in predictions:
            predicted = pred.get("predicted", "")
            gold = pred.get("gold", "")
            
            if not gold:
                continue
            
            total += 1
            
            # Check exact match
            if predicted == gold:
                correct += 1
                true_positives[gold] += 1
            else:
                false_positives[predicted] += 1
                false_negatives[gold] += 1
                
                if include_error_analysis and len(errors) < max_errors_to_show:
                    errors.append({
                        "id": pred.get("id", ""),
                        "predicted": predicted,
                        "gold": gold,
                        "trace_preview": pred.get("trace", "")[:200] + "..." if pred.get("trace") else "",
                        "confidence": pred.get("confidence", 0),
                    })
            
            # Update confusion matrix
            confusion[gold][predicted] += 1
            
            # Check hierarchical (main status) match
            if self.taxonomy_manager:
                pred_main = self.taxonomy_manager.get_main_for_sub(predicted)
                gold_main = self.taxonomy_manager.get_main_for_sub(gold)
                if pred_main and gold_main and pred_main == gold_main:
                    main_correct += 1
            else:
                # Infer main status from sub_status prefix
                pred_prefix = predicted.split("_")[0] if predicted else ""
                gold_prefix = gold.split("_")[0] if gold else ""
                if pred_prefix == gold_prefix:
                    main_correct += 1
        
        # Calculate metrics
        accuracy = correct / total if total > 0 else 0
        hierarchical_accuracy = main_correct / total if total > 0 else 0
        
        # Per-class precision, recall, F1
        per_class_metrics = {}
        all_classes = set(true_positives.keys()) | set(false_positives.keys()) | set(false_negatives.keys())
        
        macro_precision_sum = 0
        macro_recall_sum = 0
        macro_f1_sum = 0
        num_classes = 0
        
        for cls in all_classes:
            tp = true_positives[cls]
            fp = false_positives[cls]
            fn = false_negatives[cls]
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            
            per_class_metrics[cls] = {
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "support": tp + fn,
            }
            
            if tp + fn > 0:  # Only count classes with actual samples
                macro_precision_sum += precision
                macro_recall_sum += recall
                macro_f1_sum += f1
                num_classes += 1
        
        macro_f1 = macro_f1_sum / num_classes if num_classes > 0 else 0
        
        # Micro F1 (same as accuracy for single-label classification)
        total_tp = sum(true_positives.values())
        total_fp = sum(false_positives.values())
        total_fn = sum(false_negatives.values())
        
        micro_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
        micro_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
        micro_f1 = 2 * micro_precision * micro_recall / (micro_precision + micro_recall) if (micro_precision + micro_recall) > 0 else 0
        
        # Build summary
        summary = self._build_summary(
            accuracy, macro_f1, micro_f1, hierarchical_accuracy,
            total, correct, per_class_metrics
        )
        
        return EvaluationResult(
            accuracy=accuracy,
            macro_f1=macro_f1,
            micro_f1=micro_f1,
            per_class_metrics=per_class_metrics,
            confusion_matrix=dict(confusion),
            hierarchical_accuracy=hierarchical_accuracy,
            error_analysis=errors,
            summary=summary
        )
    
    def _build_summary(
        self,
        accuracy: float,
        macro_f1: float,
        micro_f1: float,
        hierarchical_accuracy: float,
        total: int,
        correct: int,
        per_class_metrics: Dict
    ) -> str:
        """Build a human-readable summary."""
        lines = [
            "=" * 60,
            "Evaluation Summary",
            "=" * 60,
            f"Total samples: {total}",
            f"Correct predictions: {correct}",
            "",
            "Overall Metrics:",
            f"  Accuracy: {accuracy:.2%}",
            f"  Macro F1: {macro_f1:.4f}",
            f"  Micro F1: {micro_f1:.4f}",
            f"  Hierarchical Accuracy (main status): {hierarchical_accuracy:.2%}",
            "",
            "Per-Class Performance (sorted by F1):",
        ]
        
        # Sort by F1 descending
        sorted_classes = sorted(
            per_class_metrics.items(),
            key=lambda x: x[1]["f1"],
            reverse=True
        )
        
        for cls, metrics in sorted_classes:
            lines.append(
                f"  {cls}: P={metrics['precision']:.2%} R={metrics['recall']:.2%} "
                f"F1={metrics['f1']:.4f} (n={metrics['support']})"
            )
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def print_confusion_matrix(self, confusion: Dict[str, Dict[str, int]], top_n: int = 10):
        """Print a readable confusion matrix."""
        # Get all classes
        all_classes = set()
        for gold, preds in confusion.items():
            all_classes.add(gold)
            all_classes.update(preds.keys())
        
        # Sort by frequency
        class_counts = defaultdict(int)
        for gold, preds in confusion.items():
            for pred, count in preds.items():
                class_counts[gold] += count
        
        sorted_classes = sorted(class_counts.keys(), key=lambda x: class_counts[x], reverse=True)[:top_n]
        
        # Print header
        header = "Gold\\Pred".ljust(20) + "".join(c[:8].ljust(10) for c in sorted_classes)
        print(header)
        print("-" * len(header))
        
        # Print rows
        for gold in sorted_classes:
            row = gold[:18].ljust(20)
            for pred in sorted_classes:
                count = confusion.get(gold, {}).get(pred, 0)
                row += str(count).ljust(10)
            print(row)


def load_gold_labels(file_path: str, id_column: str = "id", label_column: str = "label") -> Dict[str, str]:
    """Load gold labels from a file."""
    import csv
    
    labels = {}
    
    if file_path.endswith(".json"):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                labels[item.get(id_column, "")] = item.get(label_column, "")
    
    elif file_path.endswith(".jsonl"):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                item = json.loads(line)
                labels[item.get(id_column, "")] = item.get(label_column, "")
    
    elif file_path.endswith(".csv"):
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                labels[row.get(id_column, "")] = row.get(label_column, "")
    
    return labels
