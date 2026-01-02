"""
Multi-language NER-based anonymizer for person names.
Uses Hugging Face transformers with bert-base-multilingual-cased-ner-hrl model.
"""
import json
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class AnonymizeResult:
    """Result of anonymization."""
    original_text: str
    anonymized_text: str
    detected_names: List[Dict]
    replacement_token: str = "[PERSON]"


class NameAnonymizer:
    """
    Anonymize person names in text using multi-language NER.
    
    Usage:
        anonymizer = NameAnonymizer()
        result = anonymizer.anonymize("Delivered to: John Smith")
        print(result.anonymized_text)  # "Delivered to: [PERSON]"
    """
    
    def __init__(
        self,
        model_name: str = "Davlan/bert-base-multilingual-cased-ner-hrl",
        replacement_token: str = "[PERSON]",
        confidence_threshold: float = 0.8,
    ):
        self.model_name = model_name
        self.replacement_token = replacement_token
        self.confidence_threshold = confidence_threshold
        self._pipeline = None
    
    def _load_model(self):
        """Lazy load the NER model."""
        if self._pipeline is None:
            from transformers import pipeline
            print(f"Loading NER model: {self.model_name}...")
            self._pipeline = pipeline(
                "ner",
                model=self.model_name,
                aggregation_strategy="simple"
            )
            print("NER model loaded.")
    
    def detect_names(self, text: str) -> List[Dict]:
        """
        Detect person names in text.
        
        Returns:
            List of detected names with position and confidence.
        """
        self._load_model()
        
        entities = self._pipeline(text)
        
        # Filter for PER (person) entities above threshold
        names = []
        for ent in entities:
            if ent["entity_group"] == "PER" and ent["score"] >= self.confidence_threshold:
                names.append({
                    "name": ent["word"].replace(" ", ""),  # Remove tokenizer spaces
                    "original": text[ent["start"]:ent["end"]],
                    "start": ent["start"],
                    "end": ent["end"],
                    "confidence": float(ent["score"])
                })
        
        return names
    
    def anonymize(self, text: str) -> AnonymizeResult:
        """
        Anonymize person names in text.
        
        Args:
            text: Input text containing person names.
            
        Returns:
            AnonymizeResult with original and anonymized text.
        """
        names = self.detect_names(text)
        
        if not names:
            return AnonymizeResult(
                original_text=text,
                anonymized_text=text,
                detected_names=[],
                replacement_token=self.replacement_token
            )
        
        # Sort by position (reverse) to replace from end to start
        names_sorted = sorted(names, key=lambda x: x["start"], reverse=True)
        
        anonymized = text
        for name_info in names_sorted:
            start = name_info["start"]
            end = name_info["end"]
            anonymized = anonymized[:start] + self.replacement_token + anonymized[end:]
        
        return AnonymizeResult(
            original_text=text,
            anonymized_text=anonymized,
            detected_names=names,
            replacement_token=self.replacement_token
        )
    
    def anonymize_batch(self, texts: List[str]) -> List[AnonymizeResult]:
        """Anonymize multiple texts."""
        return [self.anonymize(text) for text in texts]
    
    def anonymize_trace(self, trace: str) -> AnonymizeResult:
        """
        Anonymize a logistics trace (multi-line text).
        Process line by line for better accuracy.
        """
        lines = trace.split("\n")
        all_names = []
        anonymized_lines = []
        
        for line in lines:
            result = self.anonymize(line)
            anonymized_lines.append(result.anonymized_text)
            all_names.extend(result.detected_names)
        
        return AnonymizeResult(
            original_text=trace,
            anonymized_text="\n".join(anonymized_lines),
            detected_names=all_names,
            replacement_token=self.replacement_token
        )


def test_anonymizer():
    """Test the anonymizer with the test dataset."""
    # Load test data
    with open("test_data_with_names.json", "r", encoding="utf-8") as f:
        test_data = json.load(f)
    
    # Create anonymizer
    anonymizer = NameAnonymizer()
    
    print("=" * 60)
    print("Testing NameAnonymizer with multi-language data")
    print("=" * 60)
    
    total = len(test_data)
    detected_count = 0
    
    for item in test_data:
        print(f"\n--- Test {item['id']} ({item['language']}) ---")
        
        result = anonymizer.anonymize_trace(item["trace"])
        
        detected_names = [n["original"] for n in result.detected_names]
        expected_names = item["expected_names"]
        
        # Check if expected names were detected
        found = sum(1 for name in expected_names if any(name in d for d in detected_names))
        
        print(f"Expected: {expected_names}")
        print(f"Detected: {detected_names}")
        print(f"Found: {found}/{len(expected_names)}")
        
        if found > 0:
            detected_count += 1
        
        # Show anonymized text (first 200 chars)
        print(f"Anonymized (preview): {result.anonymized_text[:200]}...")
    
    print("\n" + "=" * 60)
    print(f"Summary: {detected_count}/{total} test cases had at least one name detected")
    print("=" * 60)


if __name__ == "__main__":
    test_anonymizer()
