"""Prometheus metrics for Gemini key usage and system health."""

from prometheus_client import Counter, Histogram, Gauge, Info
from typing import Dict, Any
import time


# Gemini API metrics
gemini_requests_total = Counter(
    'gemini_requests_total',
    'Total Gemini API requests',
    ['key_id', 'status', 'model']
)

gemini_tokens_used_total = Counter(
    'gemini_tokens_used_total',
    'Total tokens used in Gemini requests',
    ['key_id', 'model', 'type']
)

gemini_errors_total = Counter(
    'gemini_errors_total',
    'Total Gemini API errors',
    ['key_id', 'error_type']
)

gemini_circuit_breaker_state = Gauge(
    'gemini_circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=open)',
    ['key_id']
)

gemini_key_quota_remaining = Gauge(
    'gemini_key_quota_remaining',
    'Estimated quota remaining for key',
    ['key_id']
)

gemini_request_duration = Histogram(
    'gemini_request_duration_seconds',
    'Gemini request duration',
    ['key_id', 'model']
)

# System metrics
session_operations_total = Counter(
    'session_operations_total',
    'Total session operations',
    ['operation', 'status']
)

vector_operations_total = Counter(
    'vector_operations_total',
    'Total vector store operations',
    ['operation', 'backend']
)

kg_operations_total = Counter(
    'kg_operations_total',
    'Total knowledge graph operations',
    ['operation', 'backend']
)

# System info
system_info = Info(
    'ai_story_system_info',
    'System information'
)

system_info.info({
    'version': '1.0.0',
    'python_version': '3.11',
    'fastapi_version': '0.104.0'
})


class MetricsCollector:
    def __init__(self):
        self.start_time = time.time()
    
    def record_gemini_request(self, key_id: str, status: str, model: str, duration: float):
        """Record Gemini API request metrics"""
        gemini_requests_total.labels(key_id=key_id, status=status, model=model).inc()
        gemini_request_duration.labels(key_id=key_id, model=model).observe(duration)
    
    def record_gemini_tokens(self, key_id: str, model: str, input_tokens: int, output_tokens: int):
        """Record token usage"""
        gemini_tokens_used_total.labels(key_id=key_id, model=model, type='input').inc(input_tokens)
        gemini_tokens_used_total.labels(key_id=key_id, model=model, type='output').inc(output_tokens)
    
    def record_gemini_error(self, key_id: str, error_type: str):
        """Record Gemini API error"""
        gemini_errors_total.labels(key_id=key_id, error_type=error_type).inc()
    
    def update_circuit_breaker(self, key_id: str, is_open: bool):
        """Update circuit breaker state"""
        gemini_circuit_breaker_state.labels(key_id=key_id).set(1 if is_open else 0)
    
    def update_quota_remaining(self, key_id: str, remaining: int):
        """Update estimated quota remaining"""
        gemini_key_quota_remaining.labels(key_id=key_id).set(remaining)
    
    def record_session_operation(self, operation: str, status: str):
        """Record session operation"""
        session_operations_total.labels(operation=operation, status=status).inc()
    
    def record_vector_operation(self, operation: str, backend: str):
        """Record vector store operation"""
        vector_operations_total.labels(operation=operation, backend=backend).inc()
    
    def record_kg_operation(self, operation: str, backend: str):
        """Record knowledge graph operation"""
        kg_operations_total.labels(operation=operation, backend=backend).inc()
    
    def get_uptime(self) -> float:
        """Get system uptime in seconds"""
        return time.time() - self.start_time


# Global metrics collector
_metrics_collector: MetricsCollector = None

def get_metrics_collector() -> MetricsCollector:
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector
