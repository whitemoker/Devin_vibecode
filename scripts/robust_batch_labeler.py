"""
Production-grade batch LLM labeling system with robust error handling.

Features:
- Custom httpx client with explicit connect/read/write timeouts
- Per-model circuit breaker with sliding window
- Inflight task journaling for crash recovery
- Incremental result saving
- Graceful shutdown with status report
- Error classification (recoverable/non-recoverable/parse)
- Heartbeat thread for visibility
- Global budget guard

Usage:
    python robust_batch_labeler.py --input predictions_long.jsonl --output-dir output/retry_run
    python robust_batch_labeler.py --retry-unknown --input predictions_long.jsonl
"""

import json
import os
import sys
import time
import re
import threading
import signal
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Deque
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError
from enum import Enum

import httpx
from openai import OpenAI
import yaml

# Unbuffered output
sys.stdout.reconfigure(line_buffering=True)


class ErrorClass(Enum):
    NONE = "none"
    # Non-recoverable - should halt or skip permanently
    QUOTA_EXHAUSTED = "quota_exhausted"
    AUTH_ERROR = "auth_error"
    INVALID_REQUEST = "invalid_request"
    # Recoverable - can retry with backoff
    RATE_LIMITED = "rate_limited"
    TRANSIENT_HTTP = "transient_http"
    TIMEOUT_SOFT = "timeout_soft"
    TIMEOUT_HARD = "timeout_hard"
    NETWORK_ERROR = "network_error"
    # Format/parse issues
    PARSE_ERROR = "parse_error"
    MODEL_OUTPUT_UNKNOWN = "model_output_unknown"
    # Circuit breaker
    CIRCUIT_OPEN = "circuit_open"


@dataclass
class CircuitBreaker:
    """Per-model circuit breaker with sliding window."""
    model: str
    window_size: int = 20
    failure_threshold: float = 0.20
    cooldown_seconds: float = 300.0  # 5 minutes
    
    outcomes: Deque[bool] = field(default_factory=deque)
    is_open: bool = False
    opened_at: Optional[float] = None
    total_calls: int = 0
    total_failures: int = 0
    
    def record(self, success: bool):
        """Record an outcome (True=success, False=failure)."""
        self.outcomes.append(success)
        self.total_calls += 1
        if not success:
            self.total_failures += 1
        
        # Keep only last window_size outcomes
        while len(self.outcomes) > self.window_size:
            self.outcomes.popleft()
        
        # Check if we should open the circuit
        if len(self.outcomes) >= self.window_size:
            failures = sum(1 for o in self.outcomes if not o)
            failure_rate = failures / len(self.outcomes)
            if failure_rate > self.failure_threshold:
                self.is_open = True
                self.opened_at = time.time()
                print(f"[CIRCUIT BREAKER] {self.model}: OPENED (failure rate {failure_rate:.1%} > {self.failure_threshold:.1%})", flush=True)
    
    def allow_request(self) -> bool:
        """Check if a request is allowed."""
        if not self.is_open:
            return True
        
        # Check if cooldown has passed
        if self.opened_at and (time.time() - self.opened_at) > self.cooldown_seconds:
            self.is_open = False
            self.outcomes.clear()
            print(f"[CIRCUIT BREAKER] {self.model}: CLOSED (cooldown passed)", flush=True)
            return True
        
        return False
    
    def get_stats(self) -> Dict:
        return {
            "model": self.model,
            "is_open": self.is_open,
            "total_calls": self.total_calls,
            "total_failures": self.total_failures,
            "recent_failure_rate": sum(1 for o in self.outcomes if not o) / len(self.outcomes) if self.outcomes else 0
        }


@dataclass
class InflightTask:
    """Track inflight tasks for crash recovery."""
    task_id: str
    model: str
    prompt_type: str
    sample_id: str
    start_ts: float
    
    def to_dict(self):
        return asdict(self)


class RobustBatchLabeler:
    """Production-grade batch labeling system."""
    
    # Configuration
    API_KEY = os.environ.get("ABACUS_API_KEY", "s2_0186d9e4b8c74102b04cb60979b85088")
    API_BASE = "https://routellm.abacus.ai/v1"
    
    MODELS = {
        "grok-4": "grok-4-0709",
        "gpt-5.2": "gpt-5.2",
        "claude-opus-4.5": "claude-opus-4-5-20251101",
        "gemini-3": "gemini-3-pro-preview"
    }
    
    PRIMARY_CATEGORIES = [
        "INFO_RECEIVED", "IN_TRANSIT", "WAITING_DELIVERY",
        "DELIVERED", "DELIVERY_FAILED", "ABNORMAL"
    ]
    
    STRONG_RETURN_KEYWORDS = [
        "return to sender", "returned to sender", "back to sender", "back to shipper",
        "rto", "rts", "return shipment", "returned shipment",
        "zurück an absender", "retour à l'expéditeur", "devuelto al remitente",
        "退回发件人", "退回寄件人", "退件完成"
    ]
    
    def __init__(
        self,
        output_dir: str,
        max_workers: int = 2,
        max_retries: int = 3,
        connect_timeout: float = 10.0,
        read_timeout: float = 45.0,
        write_timeout: float = 10.0,
        pool_timeout: float = 10.0,
        heartbeat_interval: float = 10.0,
        max_consecutive_failures: int = 10,
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_workers = max_workers
        self.max_retries = max_retries
        self.heartbeat_interval = heartbeat_interval
        self.max_consecutive_failures = max_consecutive_failures
        
        # Create httpx client with explicit timeouts
        timeout = httpx.Timeout(
            connect=connect_timeout,
            read=read_timeout,
            write=write_timeout,
            pool=pool_timeout
        )
        http_client = httpx.Client(timeout=timeout)
        
        # Initialize OpenAI client with custom httpx client
        self.client = OpenAI(
            api_key=self.API_KEY,
            base_url=self.API_BASE,
            http_client=http_client
        )
        
        # Per-model circuit breakers
        self.circuit_breakers: Dict[str, CircuitBreaker] = {
            model: CircuitBreaker(model=model) for model in self.MODELS
        }
        
        # State tracking
        self.results: List[Dict] = []
        self.inflight_tasks: Dict[str, InflightTask] = {}
        self.completed_count = 0
        self.failed_count = 0
        self.consecutive_failures = 0
        self.should_halt = False
        self.halt_reason = None
        self.start_time = None
        
        # File paths
        self.results_file = self.output_dir / "results.jsonl"
        self.inflight_file = self.output_dir / "inflight.jsonl"
        self.failures_file = self.output_dir / "failures.jsonl"
        self.status_file = self.output_dir / "run_status.json"
        
        # Locks
        self.results_lock = threading.Lock()
        self.inflight_lock = threading.Lock()
        
        # Heartbeat thread
        self.heartbeat_thread = None
        self.heartbeat_stop = threading.Event()
        
        # Signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Load prompts
        self.prompts = self._load_prompts()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print(f"\n[SHUTDOWN] Received signal {signum}, initiating graceful shutdown...", flush=True)
        self.should_halt = True
        self.halt_reason = f"signal_{signum}"
    
    def _load_prompts(self) -> Dict[str, Dict]:
        """Load prompt templates."""
        prompts_dir = Path(__file__).parent.parent / "resources" / "prompts"
        prompts = {}
        for name in ["rule_based", "time_based", "evidence_based"]:
            path = prompts_dir / f"primary_{name}_v1.yaml"
            if path.exists():
                with open(path, 'r') as f:
                    prompts[name] = yaml.safe_load(f)
        return prompts
    
    def _start_heartbeat(self, total_tasks: int):
        """Start heartbeat thread for visibility."""
        def heartbeat():
            while not self.heartbeat_stop.is_set():
                elapsed = time.time() - self.start_time if self.start_time else 0
                inflight_count = len(self.inflight_tasks)
                print(
                    f"[HEARTBEAT] elapsed={elapsed:.0f}s, completed={self.completed_count}/{total_tasks}, "
                    f"inflight={inflight_count}, failures={self.failed_count}, "
                    f"consecutive_failures={self.consecutive_failures}",
                    flush=True
                )
                self.heartbeat_stop.wait(self.heartbeat_interval)
        
        self.heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
        self.heartbeat_thread.start()
    
    def _stop_heartbeat(self):
        """Stop heartbeat thread."""
        self.heartbeat_stop.set()
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=2)
    
    def _classify_error(self, response: str, exception: Optional[Exception] = None) -> ErrorClass:
        """Classify error type for appropriate handling."""
        if exception:
            exc_str = str(exception).lower()
            if "timeout" in exc_str or "timed out" in exc_str:
                return ErrorClass.TIMEOUT_SOFT
            if "401" in exc_str or "unauthorized" in exc_str or "invalid api key" in exc_str:
                return ErrorClass.AUTH_ERROR
            if "429" in exc_str or "rate limit" in exc_str:
                return ErrorClass.RATE_LIMITED
            if "400" in exc_str or "bad request" in exc_str:
                return ErrorClass.INVALID_REQUEST
            if "5" in exc_str and ("00" in exc_str or "02" in exc_str or "03" in exc_str):
                return ErrorClass.TRANSIENT_HTTP
            if "connect" in exc_str or "network" in exc_str or "reset" in exc_str:
                return ErrorClass.NETWORK_ERROR
            return ErrorClass.TRANSIENT_HTTP
        
        if not response:
            return ErrorClass.TIMEOUT_SOFT
        
        response_lower = response.lower()
        if "no remaining credits" in response_lower or "quota" in response_lower:
            return ErrorClass.QUOTA_EXHAUSTED
        if "unauthorized" in response_lower or "invalid api key" in response_lower:
            return ErrorClass.AUTH_ERROR
        if "rate limit" in response_lower:
            return ErrorClass.RATE_LIMITED
        
        return ErrorClass.NONE
    
    def _format_trace(self, events: List[Dict], max_events: int = 20) -> str:
        """Format trace events for LLM input."""
        if not events:
            return "No tracking events available."
        
        full_text = " ".join(str(e.get("details", [])) for e in events).lower()
        has_strong_return = any(kw in full_text for kw in self.STRONG_RETURN_KEYWORDS)
        
        if len(events) > max_events:
            events = events[-max_events:]
        
        lines = []
        for i, event in enumerate(events):
            ts = event.get("timestamp", "")
            details = event.get("details", [])
            detail_str = ", ".join(str(d) for d in details) if details else "No details"
            
            if i == len(events) - 1:
                lines.append(f">>> LATEST: [{ts}] {detail_str}")
            else:
                lines.append(f"[{ts}] {detail_str}")
        
        if has_strong_return:
            lines.insert(0, ">>> RETURN_EVIDENCE: Strong return evidence detected in trajectory (return to sender/RTO/RTS)")
        
        return "\n".join(lines)
    
    def _parse_response(self, response: str) -> tuple:
        """Parse LLM response to extract prediction."""
        if not response or response.startswith("ERROR:"):
            return "UNKNOWN", 0.0, response, ErrorClass.PARSE_ERROR
        
        # Strip markdown code blocks if present
        if "```" in response:
            code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
            if code_block_match:
                response = code_block_match.group(1).strip()
        
        try:
            data = json.loads(response)
            if isinstance(data, list) and len(data) > 0:
                data = data[0]
            
            if isinstance(data, dict):
                primary = data.get("primary_status") or data.get("status") or data.get("classification", "UNKNOWN")
                primary = primary.upper().replace(" ", "_")
                confidence = float(data.get("confidence", 0.0))
                explanation = data.get("explanation") or data.get("reason", "")
                
                if primary in self.PRIMARY_CATEGORIES:
                    return primary, confidence, explanation, ErrorClass.NONE
                elif primary == "UNKNOWN":
                    return "UNKNOWN", confidence, explanation, ErrorClass.MODEL_OUTPUT_UNKNOWN
        except json.JSONDecodeError:
            pass
        
        # Fallback: extract category from text
        for category in self.PRIMARY_CATEGORIES:
            if category in response.upper():
                return category, 0.5, "Extracted from text", ErrorClass.NONE
        
        return "UNKNOWN", 0.0, f"Parse error: {response[:200]}", ErrorClass.PARSE_ERROR
    
    def _call_llm(self, model_id: str, system_prompt: str, user_prompt: str) -> tuple:
        """Call LLM with proper error handling. Returns (content, latency_ms, error_class, exception)."""
        start_time = time.time()
        
        try:
            response = self.client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            latency_ms = (time.time() - start_time) * 1000
            
            if not content or content.strip() == "":
                return "", latency_ms, ErrorClass.TIMEOUT_SOFT, None
            
            # Check for quota exhaustion in response
            error_class = self._classify_error(content)
            return content, latency_ms, error_class, None
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            error_class = self._classify_error(str(e), e)
            return f"ERROR: {str(e)}", latency_ms, error_class, e
    
    def _save_result(self, result: Dict):
        """Save result incrementally."""
        with self.results_lock:
            with open(self.results_file, 'a') as f:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")
            self.results.append(result)
    
    def _save_failure(self, failure: Dict):
        """Save failure for manual review."""
        with self.results_lock:
            with open(self.failures_file, 'a') as f:
                f.write(json.dumps(failure, ensure_ascii=False) + "\n")
    
    def _record_inflight(self, task: InflightTask):
        """Record inflight task."""
        with self.inflight_lock:
            self.inflight_tasks[task.task_id] = task
            with open(self.inflight_file, 'a') as f:
                f.write(json.dumps(task.to_dict()) + "\n")
    
    def _complete_inflight(self, task_id: str):
        """Mark inflight task as complete."""
        with self.inflight_lock:
            if task_id in self.inflight_tasks:
                del self.inflight_tasks[task_id]
    
    def _save_status(self, final: bool = False):
        """Save run status."""
        status = {
            "timestamp": datetime.now().isoformat(),
            "completed": self.completed_count,
            "failed": self.failed_count,
            "halted": self.should_halt,
            "halt_reason": self.halt_reason,
            "elapsed_seconds": time.time() - self.start_time if self.start_time else 0,
            "circuit_breakers": {m: cb.get_stats() for m, cb in self.circuit_breakers.items()},
            "final": final
        }
        with open(self.status_file, 'w') as f:
            json.dump(status, f, indent=2)
    
    def process_task(
        self,
        task_id: str,
        sample: Dict,
        model_name: str,
        prompt_type: str,
        run_id: str = "batch_run"
    ) -> Optional[Dict]:
        """Process a single labeling task with full error handling."""
        
        # Check circuit breaker
        cb = self.circuit_breakers[model_name]
        if not cb.allow_request():
            return {
                "task_id": task_id,
                "sample_id": sample["tracking_no"],
                "model": model_name,
                "prompt_type": prompt_type,
                "pred_primary": "UNKNOWN",
                "error_class": ErrorClass.CIRCUIT_OPEN.value,
                "suggested_action": "retry_later"
            }
        
        # Record inflight
        inflight = InflightTask(
            task_id=task_id,
            model=model_name,
            prompt_type=prompt_type,
            sample_id=sample["tracking_no"],
            start_ts=time.time()
        )
        self._record_inflight(inflight)
        
        model_id = self.MODELS[model_name]
        prompt_data = self.prompts[prompt_type]
        
        trace = self._format_trace(sample.get("events", []))
        system_prompt = prompt_data["system_prompt"]
        user_prompt = prompt_data["user_prompt"].replace("$trace", trace)
        
        # Try with retries
        last_error_class = ErrorClass.NONE
        last_response = ""
        total_latency = 0
        
        for attempt in range(self.max_retries):
            if self.should_halt:
                break
            
            response, latency, error_class, exception = self._call_llm(model_id, system_prompt, user_prompt)
            total_latency += latency
            last_response = response
            last_error_class = error_class
            
            # Non-recoverable errors - don't retry
            if error_class in [ErrorClass.QUOTA_EXHAUSTED, ErrorClass.AUTH_ERROR]:
                self.should_halt = True
                self.halt_reason = error_class.value
                print(f"[HALT] Non-recoverable error: {error_class.value}", flush=True)
                break
            
            # Success or parse error - don't retry API call
            if error_class == ErrorClass.NONE or not response.startswith("ERROR:"):
                break
            
            # Recoverable error - retry with backoff
            if attempt < self.max_retries - 1:
                backoff = (2 ** attempt) + 1
                print(f"[RETRY] {task_id}: attempt {attempt+1}/{self.max_retries}, waiting {backoff}s", flush=True)
                time.sleep(backoff)
        
        # Parse response
        predicted, confidence, explanation, parse_error_class = self._parse_response(last_response)
        
        # Determine final error class
        final_error_class = last_error_class if last_error_class != ErrorClass.NONE else parse_error_class
        
        # Record circuit breaker outcome
        success = predicted != "UNKNOWN" and final_error_class == ErrorClass.NONE
        cb.record(success)
        
        # Update consecutive failures
        if not success:
            self.consecutive_failures += 1
            self.failed_count += 1
            if self.consecutive_failures >= self.max_consecutive_failures:
                self.should_halt = True
                self.halt_reason = f"consecutive_failures_{self.consecutive_failures}"
                print(f"[HALT] Too many consecutive failures: {self.consecutive_failures}", flush=True)
        else:
            self.consecutive_failures = 0
        
        # Build result
        events = sample.get("events", [])
        latest_event = ""
        true_sub_status = ""
        if events:
            last_evt = events[-1]
            true_sub_status = last_evt.get("transit_sub_status", "")
            details = last_evt.get("details", [])
            if details:
                latest_event = str(details[-1])[:200]
        
        result = {
            "run_id": run_id,
            "task_id": task_id,
            "sample_id": sample["tracking_no"],
            "tracking_no": sample["tracking_no"],
            "true_label": sample.get("true_label", ""),
            "true_sub_status": true_sub_status,
            "expert_id": f"{model_name}_{prompt_type}",
            "model": model_name,
            "prompt_type": prompt_type,
            "prompt_version": "v1",
            "pred_primary": predicted,
            "confidence": confidence,
            "explanation": explanation,
            "latency_ms": total_latency,
            "error_class": final_error_class.value,
            "retry_count": self.max_retries if last_error_class != ErrorClass.NONE else 0,
            "has_return_evidence": ">>> RETURN_EVIDENCE" in trace,
            "trace_char_len": len(trace),
            "latest_event": latest_event,
            "is_correct": predicted == sample.get("true_label", ""),
            "raw_response": last_response if final_error_class != ErrorClass.NONE else None,
            "suggested_action": "manual_review" if predicted == "UNKNOWN" else None
        }
        
        # Complete inflight
        self._complete_inflight(task_id)
        
        # Save result
        self._save_result(result)
        
        # Save to failures file if failed
        if predicted == "UNKNOWN" or final_error_class != ErrorClass.NONE:
            self._save_failure(result)
        
        self.completed_count += 1
        
        # Log progress
        status = "OK" if result["is_correct"] else "WRONG"
        if predicted == "UNKNOWN":
            status = "UNKNOWN"
        print(
            f"[{self.completed_count}] {model_name}/{prompt_type}: "
            f"{sample.get('true_label', '?')} -> {predicted} [{status}] ({total_latency:.0f}ms)",
            flush=True
        )
        
        return result
    
    def run_batch(
        self,
        tasks: List[Dict],
        run_id: str = "batch_run"
    ) -> Dict:
        """Run batch of labeling tasks."""
        self.start_time = time.time()
        total_tasks = len(tasks)
        
        print(f"[START] Running {total_tasks} tasks with {self.max_workers} workers", flush=True)
        print(f"[CONFIG] max_retries={self.max_retries}, heartbeat={self.heartbeat_interval}s", flush=True)
        print("-" * 80, flush=True)
        
        # Start heartbeat
        self._start_heartbeat(total_tasks)
        
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {}
                for task in tasks:
                    if self.should_halt:
                        break
                    
                    future = executor.submit(
                        self.process_task,
                        task["task_id"],
                        task["sample"],
                        task["model"],
                        task["prompt_type"],
                        run_id
                    )
                    futures[future] = task
                
                for future in as_completed(futures):
                    if self.should_halt:
                        # Cancel remaining futures
                        for f in futures:
                            f.cancel()
                        break
                    
                    try:
                        # Use timeout to detect stuck futures
                        result = future.result(timeout=120)
                    except FuturesTimeoutError:
                        task = futures[future]
                        print(f"[TIMEOUT_HARD] Task {task['task_id']} exceeded 120s", flush=True)
                        self._save_failure({
                            "task_id": task["task_id"],
                            "sample_id": task["sample"]["tracking_no"],
                            "model": task["model"],
                            "prompt_type": task["prompt_type"],
                            "error_class": ErrorClass.TIMEOUT_HARD.value,
                            "suggested_action": "retry_later"
                        })
                    except Exception as e:
                        task = futures[future]
                        print(f"[ERROR] Task {task['task_id']}: {e}", flush=True)
        
        finally:
            self._stop_heartbeat()
            self._save_status(final=True)
        
        # Generate summary
        elapsed = time.time() - self.start_time
        success_count = sum(1 for r in self.results if r.get("pred_primary") != "UNKNOWN")
        correct_count = sum(1 for r in self.results if r.get("is_correct", False))
        
        summary = {
            "total_tasks": total_tasks,
            "completed": self.completed_count,
            "successful": success_count,
            "correct": correct_count,
            "accuracy": correct_count / self.completed_count if self.completed_count > 0 else 0,
            "failed": self.failed_count,
            "halted": self.should_halt,
            "halt_reason": self.halt_reason,
            "elapsed_seconds": elapsed,
            "tasks_per_second": self.completed_count / elapsed if elapsed > 0 else 0,
            "circuit_breakers": {m: cb.get_stats() for m, cb in self.circuit_breakers.items()}
        }
        
        # Save summary
        with open(self.output_dir / "summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
        
        print("\n" + "=" * 80, flush=True)
        print(f"[COMPLETE] {self.completed_count}/{total_tasks} tasks in {elapsed:.1f}s", flush=True)
        print(f"[RESULTS] Successful: {success_count}, Correct: {correct_count} ({summary['accuracy']:.1%})", flush=True)
        if self.should_halt:
            print(f"[HALTED] Reason: {self.halt_reason}", flush=True)
        print("=" * 80, flush=True)
        
        return summary


def load_failed_predictions(predictions_file: str) -> List[Dict]:
    """Load predictions that need retry (UNKNOWN or error)."""
    failed = []
    with open(predictions_file, 'r') as f:
        for line in f:
            pred = json.loads(line)
            if pred.get("pred_primary") == "UNKNOWN" or pred.get("error_class") not in [None, "none"]:
                failed.append(pred)
    return failed


def load_test_samples(samples_file: str) -> Dict[str, Dict]:
    """Load test samples indexed by tracking_no."""
    with open(samples_file, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, dict) and "samples" in data:
        samples = data["samples"]
    else:
        samples = data
    
    return {s["tracking_no"]: s for s in samples}


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Production-grade batch LLM labeler")
    parser.add_argument("--input", required=True, help="Input predictions file (JSONL)")
    parser.add_argument("--samples", required=True, help="Test samples file (JSON)")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--retry-unknown", action="store_true", help="Only retry UNKNOWN predictions")
    parser.add_argument("--workers", type=int, default=2, help="Number of concurrent workers")
    parser.add_argument("--max-retries", type=int, default=3, help="Max retries per task")
    parser.add_argument("--run-id", default="retry_run", help="Run identifier")
    
    args = parser.parse_args()
    
    # Load samples
    samples_by_id = load_test_samples(args.samples)
    print(f"Loaded {len(samples_by_id)} test samples", flush=True)
    
    # Load predictions to retry
    failed_preds = load_failed_predictions(args.input)
    print(f"Found {len(failed_preds)} predictions to retry", flush=True)
    
    # Build task list
    tasks = []
    for pred in failed_preds:
        sample_id = pred.get("sample_id") or pred.get("tracking_no")
        if sample_id not in samples_by_id:
            print(f"Warning: Sample {sample_id} not found in samples file", flush=True)
            continue
        
        sample = samples_by_id[sample_id]
        expert_id = pred.get("expert_id", "")
        
        # Parse model and prompt from expert_id
        model_name = None
        prompt_type = None
        for m in RobustBatchLabeler.MODELS.keys():
            if expert_id.startswith(m + "_"):
                model_name = m
                prompt_type = expert_id[len(m)+1:]
                break
        
        if not model_name or not prompt_type:
            print(f"Warning: Could not parse expert_id {expert_id}", flush=True)
            continue
        
        tasks.append({
            "task_id": f"{sample_id}_{model_name}_{prompt_type}",
            "sample": sample,
            "model": model_name,
            "prompt_type": prompt_type
        })
    
    print(f"Created {len(tasks)} tasks to process", flush=True)
    
    # Run batch
    labeler = RobustBatchLabeler(
        output_dir=args.output_dir,
        max_workers=args.workers,
        max_retries=args.max_retries
    )
    
    summary = labeler.run_batch(tasks, run_id=args.run_id)
    
    return 0 if not summary.get("halted") else 1


if __name__ == "__main__":
    sys.exit(main())
