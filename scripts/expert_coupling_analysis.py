#!/usr/bin/env python3
"""
Expert Coupling Analysis for LLM Ensemble Labeling

Analyzes the correlation and redundancy between different expert combinations
(model × prompt) to identify which experts can be removed without losing accuracy.

Metrics computed:
1. Cohen's Kappa - Agreement between expert pairs (accounting for chance)
2. Error Coupling - How often experts make the same mistakes
3. Oracle Accuracy - Upper bound if we could always pick the correct expert
4. Greedy Expert Selection - Find minimal expert set with maximum accuracy
"""

import json
import argparse
from collections import defaultdict
from itertools import combinations
import numpy as np


def load_predictions(filepath: str) -> list[dict]:
    """Load predictions from JSONL file."""
    results = []
    with open(filepath, 'r') as f:
        for line in f:
            results.append(json.loads(line))
    return results


def compute_cohens_kappa(pred1: list, pred2: list) -> float:
    """
    Compute Cohen's Kappa between two prediction lists.
    Only considers samples where both experts have valid predictions.
    """
    valid_pairs = [(p1, p2) for p1, p2 in zip(pred1, pred2) 
                   if p1 != 'UNKNOWN' and p2 != 'UNKNOWN']
    
    if len(valid_pairs) < 5:
        return float('nan')
    
    labels = list(set([p[0] for p in valid_pairs] + [p[1] for p in valid_pairs]))
    n = len(valid_pairs)
    
    confusion = defaultdict(lambda: defaultdict(int))
    for p1, p2 in valid_pairs:
        confusion[p1][p2] += 1
    
    po = sum(confusion[l][l] for l in labels) / n
    
    pe = 0
    for l in labels:
        row_sum = sum(confusion[l].values()) / n
        col_sum = sum(confusion[l2][l] for l2 in labels) / n
        pe += row_sum * col_sum
    
    if pe == 1:
        return 1.0
    return (po - pe) / (1 - pe)


def compute_error_coupling(correct1: list, correct2: list) -> dict:
    """
    Compute error coupling metrics between two experts.
    """
    valid_pairs = [(c1, c2) for c1, c2 in zip(correct1, correct2) 
                   if c1 is not None and c2 is not None]
    
    if len(valid_pairs) < 5:
        return {'both_correct': float('nan'), 'both_wrong': float('nan'), 
                'complementary': float('nan'), 'q_statistic': float('nan')}
    
    n = len(valid_pairs)
    n11 = sum(1 for c1, c2 in valid_pairs if c1 and c2)
    n00 = sum(1 for c1, c2 in valid_pairs if not c1 and not c2)
    n10 = sum(1 for c1, c2 in valid_pairs if c1 and not c2)
    n01 = sum(1 for c1, c2 in valid_pairs if not c1 and c2)
    
    denom = n11 * n00 + n01 * n10
    if denom == 0:
        q_stat = 0
    else:
        q_stat = (n11 * n00 - n01 * n10) / denom
    
    return {
        'both_correct': n11 / n,
        'both_wrong': n00 / n,
        'complementary': (n10 + n01) / n,
        'q_statistic': q_stat,
        'coverage': n
    }


def compute_oracle_accuracy(predictions_by_expert: dict, true_labels: dict) -> float:
    """
    Compute oracle accuracy: accuracy if we could always pick the correct expert.
    """
    correct = 0
    total = 0
    
    for sample_id, true_label in true_labels.items():
        any_correct = False
        for expert_id, preds in predictions_by_expert.items():
            if sample_id in preds and preds[sample_id] == true_label:
                any_correct = True
                break
        
        if any_correct:
            correct += 1
        total += 1
    
    return correct / total if total > 0 else 0


def greedy_expert_selection(predictions_by_expert: dict, true_labels: dict, 
                            max_experts: int = 6) -> list[tuple[str, float]]:
    """
    Greedy selection of expert subset that maximizes ensemble accuracy.
    """
    selected = []
    remaining = set(predictions_by_expert.keys())
    
    def ensemble_accuracy(expert_set: set) -> float:
        correct = 0
        total = 0
        
        for sample_id, true_label in true_labels.items():
            votes = defaultdict(int)
            for expert_id in expert_set:
                if sample_id in predictions_by_expert[expert_id]:
                    pred = predictions_by_expert[expert_id][sample_id]
                    if pred != 'UNKNOWN':
                        votes[pred] += 1
            
            if votes:
                majority = max(votes.items(), key=lambda x: x[1])[0]
                if majority == true_label:
                    correct += 1
            total += 1
        
        return correct / total if total > 0 else 0
    
    current_acc = 0
    
    for _ in range(min(max_experts, len(remaining))):
        best_expert = None
        best_gain = -1
        
        for expert_id in remaining:
            test_set = set(e[0] for e in selected) | {expert_id}
            acc = ensemble_accuracy(test_set)
            gain = acc - current_acc
            
            if gain > best_gain:
                best_gain = gain
                best_expert = expert_id
                best_acc = acc
        
        if best_expert:
            selected.append((best_expert, best_gain))
            remaining.remove(best_expert)
            current_acc = best_acc
    
    return selected


def main():
    parser = argparse.ArgumentParser(description='Expert Coupling Analysis')
    parser.add_argument('--input', type=str, required=True,
                        help='Path to predictions JSONL file')
    parser.add_argument('--output', type=str, default='output/expert_coupling_analysis.json',
                        help='Path to output JSON file')
    args = parser.parse_args()
    
    predictions = load_predictions(args.input)
    
    experts = set()
    predictions_by_expert = defaultdict(dict)
    correctness_by_expert = defaultdict(dict)
    true_labels = {}
    
    for pred in predictions:
        expert_id = f"{pred['model']}_{pred['prompt_type']}"
        sample_id = pred['sample_id']
        experts.add(expert_id)
        
        predictions_by_expert[expert_id][sample_id] = pred.get('pred_primary', 'UNKNOWN')
        correctness_by_expert[expert_id][sample_id] = pred.get('is_correct')
        true_labels[sample_id] = pred['true_label']
    
    experts = sorted(experts)
    samples = sorted(true_labels.keys())
    
    print(f"Loaded {len(predictions)} predictions from {len(experts)} experts on {len(samples)} samples")
    
    print("\n" + "=" * 80)
    print("1. Cohen's Kappa (Prediction Agreement)")
    print("=" * 80)
    
    kappa_matrix = {}
    for e1, e2 in combinations(experts, 2):
        pred1 = [predictions_by_expert[e1].get(s, 'UNKNOWN') for s in samples]
        pred2 = [predictions_by_expert[e2].get(s, 'UNKNOWN') for s in samples]
        kappa = compute_cohens_kappa(pred1, pred2)
        kappa_matrix[(e1, e2)] = kappa
        if not np.isnan(kappa):
            print(f"  {e1} vs {e2}: kappa = {kappa:.3f}")
    
    print("\n" + "=" * 80)
    print("2. Error Coupling Analysis")
    print("=" * 80)
    
    error_coupling = {}
    for e1, e2 in combinations(experts, 2):
        correct1 = [correctness_by_expert[e1].get(s) for s in samples]
        correct2 = [correctness_by_expert[e2].get(s) for s in samples]
        coupling = compute_error_coupling(correct1, correct2)
        error_coupling[(e1, e2)] = coupling
        
        if not np.isnan(coupling['q_statistic']):
            print(f"  {e1} vs {e2}:")
            print(f"    Both correct: {coupling['both_correct']:.1%}")
            print(f"    Both wrong: {coupling['both_wrong']:.1%}")
            print(f"    Complementary: {coupling['complementary']:.1%}")
            print(f"    Q-statistic: {coupling['q_statistic']:.3f} ({'similar' if coupling['q_statistic'] > 0.5 else 'diverse'})")
    
    print("\n" + "=" * 80)
    print("3. Oracle Accuracy (Upper Bound)")
    print("=" * 80)
    
    oracle_acc = compute_oracle_accuracy(predictions_by_expert, true_labels)
    print(f"  Oracle accuracy (any expert correct): {oracle_acc:.1%}")
    
    print("\n" + "=" * 80)
    print("4. Greedy Expert Selection")
    print("=" * 80)
    
    selected = greedy_expert_selection(predictions_by_expert, true_labels, max_experts=8)
    cumulative_acc = 0
    print("  Expert selection order (by marginal gain):")
    for i, (expert_id, gain) in enumerate(selected):
        cumulative_acc += gain
        print(f"    {i+1}. {expert_id}: +{gain:.1%} (cumulative: {cumulative_acc:.1%})")
    
    print("\n" + "=" * 80)
    print("5. Redundant Expert Pairs (High Coupling)")
    print("=" * 80)
    
    redundant_pairs = []
    for (e1, e2), kappa in kappa_matrix.items():
        if not np.isnan(kappa) and kappa > 0.7:
            q_stat = error_coupling.get((e1, e2), {}).get('q_statistic', 0)
            if q_stat > 0.5:
                redundant_pairs.append((e1, e2, kappa, q_stat))
                print(f"  {e1} vs {e2}: kappa={kappa:.3f}, Q={q_stat:.3f}")
    
    if not redundant_pairs:
        print("  No highly redundant pairs found (kappa > 0.7 and Q > 0.5)")
    
    results = {
        'num_experts': len(experts),
        'num_samples': len(samples),
        'experts': experts,
        'oracle_accuracy': oracle_acc,
        'greedy_selection': [{'expert': e, 'marginal_gain': g} for e, g in selected],
        'kappa_matrix': {f"{e1}|{e2}": k for (e1, e2), k in kappa_matrix.items() if not np.isnan(k)},
        'error_coupling': {f"{e1}|{e2}": c for (e1, e2), c in error_coupling.items() if not np.isnan(c.get('q_statistic', float('nan')))},
        'redundant_pairs': [{'expert1': e1, 'expert2': e2, 'kappa': k, 'q_statistic': q} 
                           for e1, e2, k, q in redundant_pairs]
    }
    
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {args.output}")


if __name__ == '__main__':
    main()
