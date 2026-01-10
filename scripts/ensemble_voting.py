#!/usr/bin/env python3
"""
Ensemble Voting Strategy for LLM Labeling

Implements multiple voting strategies for combining predictions from multiple experts:
1. Simple Majority Vote - Each expert gets one vote
2. Weighted Vote - Experts weighted by their per-class accuracy
3. Confidence-Weighted Vote - Experts weighted by their confidence scores
4. Selective Ensemble - Use only top-K experts from greedy selection

Also outputs:
- Consensus level for each sample (unanimous, majority, split)
- Samples needing manual review (no consensus or all UNKNOWN)
"""

import json
import argparse
from collections import defaultdict
from typing import Optional


def load_predictions(filepath: str) -> list[dict]:
    """Load predictions from JSONL file."""
    results = []
    with open(filepath, 'r') as f:
        for line in f:
            results.append(json.loads(line))
    return results


def load_expert_weights(filepath: str) -> dict:
    """Load per-expert per-class accuracy weights from JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def simple_majority_vote(predictions: list[dict], tie_breaker: Optional[str] = None) -> tuple[str, str, int]:
    """
    Simple majority vote - each expert gets one vote.
    
    Returns: (predicted_label, consensus_level, num_votes)
    consensus_level: 'unanimous', 'majority', 'split', 'no_consensus'
    """
    votes = defaultdict(int)
    valid_count = 0
    
    for pred in predictions:
        label = pred.get('pred_primary', 'UNKNOWN')
        if label != 'UNKNOWN':
            votes[label] += 1
            valid_count += 1
    
    if not votes:
        return 'UNKNOWN', 'no_consensus', 0
    
    sorted_votes = sorted(votes.items(), key=lambda x: -x[1])
    winner = sorted_votes[0][0]
    winner_count = sorted_votes[0][1]
    
    # Determine consensus level
    if winner_count == valid_count:
        consensus = 'unanimous'
    elif len(sorted_votes) > 1 and sorted_votes[0][1] == sorted_votes[1][1]:
        # Tie - use tie breaker if available
        if tie_breaker:
            for pred in predictions:
                if pred.get('model') + '_' + pred.get('prompt_type') == tie_breaker:
                    if pred.get('pred_primary') != 'UNKNOWN':
                        winner = pred.get('pred_primary')
                        break
        consensus = 'split'
    elif winner_count > valid_count / 2:
        consensus = 'majority'
    else:
        consensus = 'split'
    
    return winner, consensus, winner_count


def weighted_vote(predictions: list[dict], expert_weights: dict, 
                  true_label_hint: Optional[str] = None) -> tuple[str, str, float]:
    """
    Weighted vote - experts weighted by their per-class accuracy.
    
    expert_weights: {expert_id: {class: accuracy}}
    true_label_hint: If provided, use class-specific weights; otherwise use overall accuracy
    
    Returns: (predicted_label, consensus_level, total_weight)
    """
    weighted_votes = defaultdict(float)
    total_weight = 0
    
    for pred in predictions:
        label = pred.get('pred_primary', 'UNKNOWN')
        if label == 'UNKNOWN':
            continue
        
        expert_id = f"{pred['model']}_{pred['prompt_type']}"
        
        # Get weight for this expert
        if expert_id in expert_weights:
            if true_label_hint and true_label_hint in expert_weights[expert_id]:
                weight = expert_weights[expert_id][true_label_hint]
            else:
                # Use overall accuracy
                weight = expert_weights[expert_id].get('overall', 0.5)
        else:
            weight = 0.5  # Default weight
        
        weighted_votes[label] += weight
        total_weight += weight
    
    if not weighted_votes:
        return 'UNKNOWN', 'no_consensus', 0
    
    sorted_votes = sorted(weighted_votes.items(), key=lambda x: -x[1])
    winner = sorted_votes[0][0]
    winner_weight = sorted_votes[0][1]
    
    # Determine consensus level based on weight distribution
    if len(sorted_votes) == 1:
        consensus = 'unanimous'
    elif winner_weight > total_weight * 0.7:
        consensus = 'majority'
    else:
        consensus = 'split'
    
    return winner, consensus, winner_weight


def confidence_weighted_vote(predictions: list[dict]) -> tuple[str, str, float]:
    """
    Confidence-weighted vote - experts weighted by their confidence scores.
    
    Returns: (predicted_label, consensus_level, total_confidence)
    """
    weighted_votes = defaultdict(float)
    total_conf = 0
    
    for pred in predictions:
        label = pred.get('pred_primary', 'UNKNOWN')
        if label == 'UNKNOWN':
            continue
        
        confidence = pred.get('confidence', 0.5)
        weighted_votes[label] += confidence
        total_conf += confidence
    
    if not weighted_votes:
        return 'UNKNOWN', 'no_consensus', 0
    
    sorted_votes = sorted(weighted_votes.items(), key=lambda x: -x[1])
    winner = sorted_votes[0][0]
    winner_conf = sorted_votes[0][1]
    
    if len(sorted_votes) == 1:
        consensus = 'unanimous'
    elif winner_conf > total_conf * 0.7:
        consensus = 'majority'
    else:
        consensus = 'split'
    
    return winner, consensus, winner_conf


def selective_ensemble_vote(predictions: list[dict], selected_experts: list[str]) -> tuple[str, str, int]:
    """
    Selective ensemble - only use predictions from selected experts.
    
    Returns: (predicted_label, consensus_level, num_votes)
    """
    filtered_preds = []
    for pred in predictions:
        expert_id = f"{pred['model']}_{pred['prompt_type']}"
        if expert_id in selected_experts:
            filtered_preds.append(pred)
    
    return simple_majority_vote(filtered_preds)


def compute_expert_class_weights(predictions: list[dict]) -> dict:
    """
    Compute per-expert per-class accuracy weights from predictions.
    
    Returns: {expert_id: {class: accuracy, 'overall': accuracy}}
    """
    expert_stats = defaultdict(lambda: defaultdict(lambda: {'correct': 0, 'total': 0}))
    
    for pred in predictions:
        if pred.get('pred_primary') == 'UNKNOWN':
            continue
        
        expert_id = f"{pred['model']}_{pred['prompt_type']}"
        true_label = pred['true_label']
        is_correct = pred.get('is_correct', False)
        
        expert_stats[expert_id][true_label]['total'] += 1
        if is_correct:
            expert_stats[expert_id][true_label]['correct'] += 1
        
        expert_stats[expert_id]['overall']['total'] += 1
        if is_correct:
            expert_stats[expert_id]['overall']['correct'] += 1
    
    weights = {}
    for expert_id, class_stats in expert_stats.items():
        weights[expert_id] = {}
        for class_name, stats in class_stats.items():
            if stats['total'] > 0:
                # Laplace smoothing to avoid extreme weights
                weights[expert_id][class_name] = (stats['correct'] + 1) / (stats['total'] + 2)
            else:
                weights[expert_id][class_name] = 0.5
    
    return weights


def main():
    parser = argparse.ArgumentParser(description='Ensemble Voting Strategy')
    parser.add_argument('--input', type=str, required=True,
                        help='Path to predictions JSONL file')
    parser.add_argument('--output', type=str, default='output/ensemble_voting_results.json',
                        help='Path to output JSON file')
    parser.add_argument('--selected-experts', type=str, nargs='+',
                        default=['gpt-5.2_time_based', 'grok-4_rule_based', 'claude-opus-4.5_evidence_based'],
                        help='List of selected experts for selective ensemble')
    parser.add_argument('--tie-breaker', type=str, default='gpt-5.2_time_based',
                        help='Expert to use as tie breaker')
    args = parser.parse_args()
    
    predictions = load_predictions(args.input)
    
    # Group predictions by sample
    samples = defaultdict(list)
    true_labels = {}
    for pred in predictions:
        sample_id = pred['sample_id']
        samples[sample_id].append(pred)
        true_labels[sample_id] = pred['true_label']
    
    print(f"Loaded {len(predictions)} predictions for {len(samples)} samples")
    
    # Compute expert weights
    expert_weights = compute_expert_class_weights(predictions)
    
    # Apply voting strategies
    results = {
        'simple_majority': {'correct': 0, 'total': 0, 'predictions': []},
        'weighted': {'correct': 0, 'total': 0, 'predictions': []},
        'confidence': {'correct': 0, 'total': 0, 'predictions': []},
        'selective': {'correct': 0, 'total': 0, 'predictions': []},
    }
    
    needs_review = []
    
    for sample_id, preds in samples.items():
        true_label = true_labels[sample_id]
        
        # Simple majority vote
        pred_simple, consensus_simple, votes_simple = simple_majority_vote(preds, args.tie_breaker)
        results['simple_majority']['predictions'].append({
            'sample_id': sample_id,
            'true_label': true_label,
            'pred_label': pred_simple,
            'consensus': consensus_simple,
            'votes': votes_simple,
            'is_correct': pred_simple == true_label
        })
        if pred_simple != 'UNKNOWN':
            results['simple_majority']['total'] += 1
            if pred_simple == true_label:
                results['simple_majority']['correct'] += 1
        
        # Weighted vote
        pred_weighted, consensus_weighted, weight_weighted = weighted_vote(preds, expert_weights)
        results['weighted']['predictions'].append({
            'sample_id': sample_id,
            'true_label': true_label,
            'pred_label': pred_weighted,
            'consensus': consensus_weighted,
            'weight': weight_weighted,
            'is_correct': pred_weighted == true_label
        })
        if pred_weighted != 'UNKNOWN':
            results['weighted']['total'] += 1
            if pred_weighted == true_label:
                results['weighted']['correct'] += 1
        
        # Confidence-weighted vote
        pred_conf, consensus_conf, conf_conf = confidence_weighted_vote(preds)
        results['confidence']['predictions'].append({
            'sample_id': sample_id,
            'true_label': true_label,
            'pred_label': pred_conf,
            'consensus': consensus_conf,
            'confidence': conf_conf,
            'is_correct': pred_conf == true_label
        })
        if pred_conf != 'UNKNOWN':
            results['confidence']['total'] += 1
            if pred_conf == true_label:
                results['confidence']['correct'] += 1
        
        # Selective ensemble vote
        pred_selective, consensus_selective, votes_selective = selective_ensemble_vote(preds, args.selected_experts)
        results['selective']['predictions'].append({
            'sample_id': sample_id,
            'true_label': true_label,
            'pred_label': pred_selective,
            'consensus': consensus_selective,
            'votes': votes_selective,
            'is_correct': pred_selective == true_label
        })
        if pred_selective != 'UNKNOWN':
            results['selective']['total'] += 1
            if pred_selective == true_label:
                results['selective']['correct'] += 1
        
        # Check if needs manual review
        if consensus_simple in ['split', 'no_consensus']:
            needs_review.append({
                'sample_id': sample_id,
                'true_label': true_label,
                'consensus': consensus_simple,
                'predictions': {f"{p['model']}_{p['prompt_type']}": p.get('pred_primary', 'UNKNOWN') for p in preds}
            })
    
    # Print summary
    print("\n" + "=" * 80)
    print("Ensemble Voting Results")
    print("=" * 80)
    
    for strategy, data in results.items():
        if data['total'] > 0:
            acc = data['correct'] / data['total'] * 100
            print(f"\n{strategy}:")
            print(f"  Accuracy: {data['correct']}/{data['total']} ({acc:.1f}%)")
            
            # Consensus distribution
            consensus_dist = defaultdict(int)
            for pred in data['predictions']:
                consensus_dist[pred['consensus']] += 1
            print(f"  Consensus distribution: {dict(consensus_dist)}")
    
    print(f"\nSamples needing manual review: {len(needs_review)}")
    
    # Save results
    output = {
        'summary': {
            strategy: {
                'accuracy': data['correct'] / data['total'] if data['total'] > 0 else 0,
                'correct': data['correct'],
                'total': data['total']
            }
            for strategy, data in results.items()
        },
        'expert_weights': expert_weights,
        'selected_experts': args.selected_experts,
        'needs_review': needs_review,
        'predictions': {strategy: data['predictions'] for strategy, data in results.items()}
    }
    
    with open(args.output, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nResults saved to: {args.output}")


if __name__ == '__main__':
    main()
