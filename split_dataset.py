"""
Split sample_cases.json into few-shot examples and test dataset.
Each sub_status has 3 samples:
- 2 samples for few-shot (sample_cases_fewshot.json)
- 1 sample for testing (test_dataset.json)
"""
import json
from collections import defaultdict

# Load all samples
with open('sample_cases.json', 'r', encoding='utf-8') as f:
    all_samples = json.load(f)

# Group by sub_status
by_sub_status = defaultdict(list)
for sample in all_samples:
    by_sub_status[sample['sub_status']].append(sample)

# Split: 2 for few-shot, 1 for test
fewshot_samples = []
test_samples = []

for sub_status, samples in by_sub_status.items():
    if len(samples) >= 3:
        fewshot_samples.extend(samples[:2])  # First 2 for few-shot
        test_samples.append(samples[2])       # Last 1 for test
    elif len(samples) == 2:
        fewshot_samples.append(samples[0])
        test_samples.append(samples[1])
    else:
        fewshot_samples.append(samples[0])

# Save few-shot samples
with open('sample_cases_fewshot.json', 'w', encoding='utf-8') as f:
    json.dump(fewshot_samples, f, ensure_ascii=False, indent=2)

# Save test dataset
with open('test_dataset.json', 'w', encoding='utf-8') as f:
    json.dump(test_samples, f, ensure_ascii=False, indent=2)

print(f"Total samples: {len(all_samples)}")
print(f"Few-shot samples: {len(fewshot_samples)}")
print(f"Test samples: {len(test_samples)}")
print(f"\nSub-status distribution in test set:")
test_by_status = defaultdict(int)
for s in test_samples:
    test_by_status[s['sub_status']] += 1
for status, count in sorted(test_by_status.items()):
    print(f"  {status}: {count}")
