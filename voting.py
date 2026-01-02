"""
Voting and consensus mechanisms for multi-model labeling.
"""
import logging
from typing import Dict, List, Optional, Tuple, Any
from collections import Counter
from dataclasses import dataclass

from labeler import LabelPrediction, LabelResult

logger = logging.getLogger(__name__)


class VotingStrategy:
    """Base class for voting strategies."""
    
    def vote(
        self, 
        predictions: List[LabelPrediction],
        weights: Dict[str, float]
    ) -> LabelResult:
        """Aggregate predictions into a final result."""
        raise NotImplementedError


class MajorityVoting(VotingStrategy):
    """Simple majority voting."""
    
    def vote(
        self, 
        predictions: List[LabelPrediction],
        weights: Dict[str, float]
    ) -> LabelResult:
        # Filter valid predictions
        valid_predictions = [p for p in predictions if p.is_valid and p.sub_status]
        
        if not valid_predictions:
            return self._create_failed_result(predictions, "No valid predictions")
        
        # Count votes for each sub_status
        vote_counts = Counter(p.sub_status for p in valid_predictions)
        
        # Get the winner
        winner_sub_status, winner_count = vote_counts.most_common(1)[0]
        
        # Get the best prediction for the winner
        winner_predictions = [p for p in valid_predictions if p.sub_status == winner_sub_status]
        best_prediction = max(winner_predictions, key=lambda p: p.confidence)
        
        # Calculate confidence based on agreement
        agreement_ratio = winner_count / len(valid_predictions)
        final_confidence = best_prediction.confidence * agreement_ratio
        
        # Determine if human review is needed
        needs_review = False
        review_reason = ""
        
        if agreement_ratio < 0.5:
            needs_review = True
            review_reason = f"Low agreement: {agreement_ratio:.2%}"
        elif final_confidence < 0.6:
            needs_review = True
            review_reason = f"Low confidence: {final_confidence:.2f}"
        
        return LabelResult(
            main_status=best_prediction.main_status,
            sub_status=winner_sub_status,
            confidence=final_confidence,
            evidence=best_prediction.evidence,
            explanation=best_prediction.explanation,
            predictions=predictions,
            voting_details={
                "strategy": "majority",
                "vote_counts": dict(vote_counts),
                "agreement_ratio": agreement_ratio,
                "winner_count": winner_count,
                "total_valid": len(valid_predictions),
            },
            needs_human_review=needs_review,
            review_reason=review_reason
        )
    
    def _create_failed_result(self, predictions: List[LabelPrediction], reason: str) -> LabelResult:
        return LabelResult(
            main_status="",
            sub_status="",
            confidence=0.0,
            evidence=[],
            explanation="",
            predictions=predictions,
            voting_details={"error": reason},
            needs_human_review=True,
            review_reason=reason
        )


class WeightedMajorityVoting(VotingStrategy):
    """Weighted majority voting based on model weights."""
    
    def vote(
        self, 
        predictions: List[LabelPrediction],
        weights: Dict[str, float]
    ) -> LabelResult:
        # Filter valid predictions
        valid_predictions = [p for p in predictions if p.is_valid and p.sub_status]
        
        if not valid_predictions:
            return self._create_failed_result(predictions, "No valid predictions")
        
        # Calculate weighted votes for each sub_status
        weighted_votes: Dict[str, float] = {}
        total_weight = 0.0
        
        for pred in valid_predictions:
            weight = weights.get(pred.model_name, 1.0)
            sub_status = pred.sub_status
            
            if sub_status not in weighted_votes:
                weighted_votes[sub_status] = 0.0
            
            # Weight by both model weight and prediction confidence
            vote_weight = weight * pred.confidence
            weighted_votes[sub_status] += vote_weight
            total_weight += vote_weight
        
        # Normalize and find winner
        if total_weight > 0:
            for sub_status in weighted_votes:
                weighted_votes[sub_status] /= total_weight
        
        winner_sub_status = max(weighted_votes, key=weighted_votes.get)
        winner_score = weighted_votes[winner_sub_status]
        
        # Get the best prediction for the winner
        winner_predictions = [p for p in valid_predictions if p.sub_status == winner_sub_status]
        best_prediction = max(winner_predictions, key=lambda p: p.confidence)
        
        # Calculate final confidence
        final_confidence = winner_score * best_prediction.confidence
        
        # Determine if human review is needed
        needs_review = False
        review_reason = ""
        
        if winner_score < 0.5:
            needs_review = True
            review_reason = f"Low weighted agreement: {winner_score:.2%}"
        elif final_confidence < 0.6:
            needs_review = True
            review_reason = f"Low confidence: {final_confidence:.2f}"
        
        # Check for close second place
        sorted_votes = sorted(weighted_votes.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_votes) > 1:
            second_score = sorted_votes[1][1]
            if winner_score - second_score < 0.1:
                needs_review = True
                review_reason = f"Close vote: {winner_sub_status}={winner_score:.2%} vs {sorted_votes[1][0]}={second_score:.2%}"
        
        return LabelResult(
            main_status=best_prediction.main_status,
            sub_status=winner_sub_status,
            confidence=final_confidence,
            evidence=best_prediction.evidence,
            explanation=best_prediction.explanation,
            predictions=predictions,
            voting_details={
                "strategy": "weighted_majority",
                "weighted_votes": weighted_votes,
                "winner_score": winner_score,
                "total_weight": total_weight,
            },
            needs_human_review=needs_review,
            review_reason=review_reason
        )
    
    def _create_failed_result(self, predictions: List[LabelPrediction], reason: str) -> LabelResult:
        return LabelResult(
            main_status="",
            sub_status="",
            confidence=0.0,
            evidence=[],
            explanation="",
            predictions=predictions,
            voting_details={"error": reason},
            needs_human_review=True,
            review_reason=reason
        )


class UnanimousVoting(VotingStrategy):
    """Requires unanimous agreement, otherwise marks for human review."""
    
    def vote(
        self, 
        predictions: List[LabelPrediction],
        weights: Dict[str, float]
    ) -> LabelResult:
        # Filter valid predictions
        valid_predictions = [p for p in predictions if p.is_valid and p.sub_status]
        
        if not valid_predictions:
            return self._create_failed_result(predictions, "No valid predictions")
        
        # Check for unanimous agreement
        sub_statuses = set(p.sub_status for p in valid_predictions)
        
        if len(sub_statuses) == 1:
            # Unanimous!
            winner_sub_status = list(sub_statuses)[0]
            best_prediction = max(valid_predictions, key=lambda p: p.confidence)
            
            # Average confidence
            avg_confidence = sum(p.confidence for p in valid_predictions) / len(valid_predictions)
            
            return LabelResult(
                main_status=best_prediction.main_status,
                sub_status=winner_sub_status,
                confidence=avg_confidence,
                evidence=best_prediction.evidence,
                explanation=best_prediction.explanation,
                predictions=predictions,
                voting_details={
                    "strategy": "unanimous",
                    "unanimous": True,
                    "num_voters": len(valid_predictions),
                },
                needs_human_review=False,
                review_reason=""
            )
        else:
            # Not unanimous - fall back to weighted majority but mark for review
            weighted_voting = WeightedMajorityVoting()
            result = weighted_voting.vote(predictions, weights)
            result.needs_human_review = True
            result.review_reason = f"Not unanimous: {sub_statuses}"
            result.voting_details["strategy"] = "unanimous_fallback"
            result.voting_details["unanimous"] = False
            return result
    
    def _create_failed_result(self, predictions: List[LabelPrediction], reason: str) -> LabelResult:
        return LabelResult(
            main_status="",
            sub_status="",
            confidence=0.0,
            evidence=[],
            explanation="",
            predictions=predictions,
            voting_details={"error": reason},
            needs_human_review=True,
            review_reason=reason
        )


class VotingFactory:
    """Factory for creating voting strategies."""
    
    STRATEGIES = {
        "majority": MajorityVoting,
        "weighted_majority": WeightedMajorityVoting,
        "unanimous": UnanimousVoting,
    }
    
    @classmethod
    def create(cls, strategy_name: str) -> VotingStrategy:
        """Create a voting strategy by name."""
        if strategy_name not in cls.STRATEGIES:
            raise ValueError(f"Unknown voting strategy: {strategy_name}")
        return cls.STRATEGIES[strategy_name]()
