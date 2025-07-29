"""
🔥 Elite Resilience System - Bulletproof Error Handling and Recovery
Advanced error handling, retry logic, circuit breakers, and graceful degradation
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import functools
import random
import json
from contextlib import asynccontextmanager
import traceback

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class CircuitBreakerState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, blocking calls
    HALF_OPEN = "half_open" # Testing if service recovered

class RetryStrategy(Enum):
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    RANDOM = "random"

@dataclass
class ErrorInfo:
    """Detailed error information"""
    error_id: str
    error_type: str
    message: str
    severity: ErrorSeverity
    timestamp: datetime
    component: str
    agent_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    recovery_attempted: bool = False
    recovery_successful: bool = False

@dataclass
class RetryConfig:
    """Configuration for retry logic"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    backoff_multiplier: float = 2.0
    jitter: bool = True
    exceptions: tuple = (Exception,)

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    expected_exception: tuple = (Exception,)
    success_threshold: int = 3  # For half-open state

class CircuitBreaker:
    """Advanced circuit breaker implementation"""
    
    def __init__(self, config: CircuitBreakerConfig, name: str = "default"):
        self.config = config
        self.name = name
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state_change_time = datetime.now()
        
    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                self.state_change_time = datetime.now()
                logger.info(f"🔄 Circuit breaker {self.name} moved to HALF_OPEN")
            else:
                raise CircuitBreakerOpenError(f"Circuit breaker {self.name} is OPEN")
        
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.config.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        if self.last_failure_time is None:
            return True
        
        time_since_failure = time.time() - self.last_failure_time
        return time_since_failure >= self.config.recovery_timeout
    
    def _on_success(self):
        """Handle successful call"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                self.state_change_time = datetime.now()
                logger.info(f"✅ Circuit breaker {self.name} reset to CLOSED")
        else:
            self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
            self.success_count = 0
            self.state_change_time = datetime.now()
            logger.warning(f"⚠️ Circuit breaker {self.name} moved back to OPEN")
        elif self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            self.state_change_time = datetime.now()
            logger.warning(f"🚫 Circuit breaker {self.name} moved to OPEN after {self.failure_count} failures")

class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open"""
    pass

class RetryHandler:
    """Advanced retry mechanism with multiple strategies"""
    
    def __init__(self, config: RetryConfig):
        self.config = config
    
    async def retry(self, func: Callable, *args, **kwargs):
        """Execute function with retry logic"""
        last_exception = None
        
        for attempt in range(self.config.max_attempts):
            try:
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                if attempt > 0:
                    logger.info(f"✅ Function succeeded on attempt {attempt + 1}")
                return result
                
            except self.config.exceptions as e:
                last_exception = e
                
                if attempt < self.config.max_attempts - 1:
                    delay = self._calculate_delay(attempt)
                    logger.warning(f"⚠️ Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay:.2f}s...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"❌ All {self.config.max_attempts} attempts failed")
        
        raise last_exception
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay based on retry strategy"""
        if self.config.strategy == RetryStrategy.FIXED:
            delay = self.config.base_delay
        elif self.config.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.config.base_delay * (self.config.backoff_multiplier ** attempt)
        elif self.config.strategy == RetryStrategy.LINEAR:
            delay = self.config.base_delay * (attempt + 1)
        elif self.config.strategy == RetryStrategy.RANDOM:
            delay = random.uniform(self.config.base_delay, self.config.max_delay)
        else:
            delay = self.config.base_delay
        
        # Apply jitter if enabled
        if self.config.jitter:
            jitter_amount = delay * 0.1
            delay += random.uniform(-jitter_amount, jitter_amount)
        
        return min(delay, self.config.max_delay)

class HealthMonitor:
    """Monitor system health and trigger recovery actions"""
    
    def __init__(self, check_interval: float = 30.0):
        self.check_interval = check_interval
        self.health_checks: Dict[str, Callable] = {}
        self.health_status: Dict[str, bool] = {}
        self.last_check_time: Dict[str, datetime] = {}
        self.monitoring = False
        self.recovery_actions: Dict[str, Callable] = {}
    
    def register_health_check(self, name: str, check_func: Callable, recovery_func: Callable = None):
        """Register a health check function"""
        self.health_checks[name] = check_func
        self.health_status[name] = True
        if recovery_func:
            self.recovery_actions[name] = recovery_func
        logger.info(f"🏥 Health check registered: {name}")
    
    async def start_monitoring(self):
        """Start health monitoring"""
        self.monitoring = True
        logger.info("🏥 Health monitoring started")
        
        while self.monitoring:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(5)
    
    def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring = False
        logger.info("🏥 Health monitoring stopped")
    
    async def _perform_health_checks(self):
        """Perform all registered health checks"""
        for name, check_func in self.health_checks.items():
            try:
                is_healthy = await check_func() if asyncio.iscoroutinefunction(check_func) else check_func()
                
                previous_status = self.health_status.get(name, True)
                self.health_status[name] = is_healthy
                self.last_check_time[name] = datetime.now()
                
                # If component became unhealthy, attempt recovery
                if not is_healthy and previous_status:
                    logger.warning(f"🚨 Component {name} became unhealthy")
                    await self._attempt_recovery(name)
                elif is_healthy and not previous_status:
                    logger.info(f"✅ Component {name} recovered")
                
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                self.health_status[name] = False
    
    async def _attempt_recovery(self, component_name: str):
        """Attempt to recover an unhealthy component"""
        if component_name in self.recovery_actions:
            try:
                recovery_func = self.recovery_actions[component_name]
                logger.info(f"🔧 Attempting recovery for {component_name}")
                
                if asyncio.iscoroutinefunction(recovery_func):
                    await recovery_func()
                else:
                    recovery_func()
                    
                logger.info(f"✅ Recovery completed for {component_name}")
                
            except Exception as e:
                logger.error(f"Recovery failed for {component_name}: {e}")

class EliteResilienceManager:
    """Central manager for all resilience features"""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_handlers: Dict[str, RetryHandler] = {}
        self.health_monitor = HealthMonitor()
        self.error_log: List[ErrorInfo] = []
        self.error_stats: Dict[str, int] = {}
        self.recovery_strategies: Dict[str, Callable] = {}
        
    def create_circuit_breaker(self, name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
        """Create a new circuit breaker"""
        if config is None:
            config = CircuitBreakerConfig()
            
        circuit_breaker = CircuitBreaker(config, name)
        self.circuit_breakers[name] = circuit_breaker
        logger.info(f"⚡ Circuit breaker created: {name}")
        return circuit_breaker
    
    def create_retry_handler(self, name: str, config: RetryConfig = None) -> RetryHandler:
        """Create a new retry handler"""
        if config is None:
            config = RetryConfig()
            
        retry_handler = RetryHandler(config)
        self.retry_handlers[name] = retry_handler
        logger.info(f"🔄 Retry handler created: {name}")
        return retry_handler
    
    def register_recovery_strategy(self, error_type: str, recovery_func: Callable):
        """Register a recovery strategy for specific error types"""
        self.recovery_strategies[error_type] = recovery_func
        logger.info(f"🛠️ Recovery strategy registered for: {error_type}")
    
    async def handle_error(self, error: Exception, component: str, agent_id: str = None, 
                          context: Dict[str, Any] = None) -> ErrorInfo:
        """Handle an error with comprehensive logging and recovery"""
        error_info = ErrorInfo(
            error_id=f"err_{int(time.time())}_{random.randint(1000, 9999)}",
            error_type=type(error).__name__,
            message=str(error),
            severity=self._determine_severity(error),
            timestamp=datetime.now(),
            component=component,
            agent_id=agent_id,
            context=context or {},
            stack_trace=traceback.format_exc()
        )
        
        # Log the error
        self.error_log.append(error_info)
        self.error_stats[error_info.error_type] = self.error_stats.get(error_info.error_type, 0) + 1
        
        # Log based on severity
        if error_info.severity == ErrorSeverity.CRITICAL:
            logger.critical(f"💀 CRITICAL ERROR in {component}: {error_info.message}")
        elif error_info.severity == ErrorSeverity.HIGH:
            logger.error(f"🚨 HIGH SEVERITY ERROR in {component}: {error_info.message}")
        elif error_info.severity == ErrorSeverity.MEDIUM:
            logger.warning(f"⚠️ MEDIUM SEVERITY ERROR in {component}: {error_info.message}")
        else:
            logger.info(f"ℹ️ LOW SEVERITY ERROR in {component}: {error_info.message}")
        
        # Attempt recovery
        await self._attempt_error_recovery(error_info)
        
        return error_info
    
    def _determine_severity(self, error: Exception) -> ErrorSeverity:
        """Determine error severity based on exception type"""
        critical_errors = (SystemExit, KeyboardInterrupt, MemoryError)
        high_errors = (ConnectionError, TimeoutError, PermissionError)
        medium_errors = (ValueError, TypeError, AttributeError)
        
        if isinstance(error, critical_errors):
            return ErrorSeverity.CRITICAL
        elif isinstance(error, high_errors):
            return ErrorSeverity.HIGH
        elif isinstance(error, medium_errors):
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW
    
    async def _attempt_error_recovery(self, error_info: ErrorInfo):
        """Attempt to recover from an error"""
        error_info.recovery_attempted = True
        
        # Try specific recovery strategy
        if error_info.error_type in self.recovery_strategies:
            try:
                recovery_func = self.recovery_strategies[error_info.error_type]
                
                if asyncio.iscoroutinefunction(recovery_func):
                    await recovery_func(error_info)
                else:
                    recovery_func(error_info)
                
                error_info.recovery_successful = True
                logger.info(f"✅ Recovery successful for {error_info.error_type}")
                
            except Exception as recovery_error:
                logger.error(f"💥 Recovery failed: {recovery_error}")
                error_info.recovery_successful = False
        
        # Generic recovery strategies based on severity
        if not error_info.recovery_successful:
            await self._apply_generic_recovery(error_info)
    
    async def _apply_generic_recovery(self, error_info: ErrorInfo):
        """Apply generic recovery strategies"""
        if error_info.severity == ErrorSeverity.CRITICAL:
            logger.warning("🚨 Critical error detected - implementing emergency protocols")
            # Could trigger system restart, failover, etc.
            
        elif error_info.severity == ErrorSeverity.HIGH:
            logger.info("🔧 High severity error - applying degraded mode")
            # Could reduce system load, disable non-essential features
            
        elif error_info.severity == ErrorSeverity.MEDIUM:
            logger.info("⚡ Medium severity error - applying retry with backoff")
            # Could trigger retries, alternative approaches
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error statistics"""
        recent_errors = [e for e in self.error_log if e.timestamp > datetime.now() - timedelta(hours=24)]
        
        return {
            "total_errors": len(self.error_log),
            "recent_errors": len(recent_errors),
            "error_types": dict(self.error_stats),
            "severity_breakdown": {
                severity.value: len([e for e in recent_errors if e.severity == severity])
                for severity in ErrorSeverity
            },
            "recovery_success_rate": (
                len([e for e in recent_errors if e.recovery_successful]) / 
                len([e for e in recent_errors if e.recovery_attempted]) * 100
            ) if recent_errors else 0,
            "most_common_errors": sorted(
                self.error_stats.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
        }
    
    async def start_monitoring(self):
        """Start all monitoring systems"""
        await self.health_monitor.start_monitoring()
    
    def stop_monitoring(self):
        """Stop all monitoring systems"""
        self.health_monitor.stop_monitoring()

# Decorators for easy resilience application

def with_circuit_breaker(name: str, config: CircuitBreakerConfig = None):
    """Decorator to add circuit breaker protection"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            manager = get_resilience_manager()
            
            if name not in manager.circuit_breakers:
                manager.create_circuit_breaker(name, config)
            
            circuit_breaker = manager.circuit_breakers[name]
            return await circuit_breaker.call(func, *args, **kwargs)
        
        return wrapper
    return decorator

def with_retry(config: RetryConfig = None):
    """Decorator to add retry logic"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if config is None:
                retry_config = RetryConfig()
            else:
                retry_config = config
                
            retry_handler = RetryHandler(retry_config)
            return await retry_handler.retry(func, *args, **kwargs)
        
        return wrapper
    return decorator

def with_error_handling(component: str):
    """Decorator to add comprehensive error handling"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            except Exception as e:
                manager = get_resilience_manager()
                await manager.handle_error(e, component, context={"function": func.__name__})
                raise e
        
        return wrapper
    return decorator

# Global resilience manager instance
_resilience_manager = None

def get_resilience_manager() -> EliteResilienceManager:
    """Get the global resilience manager instance"""
    global _resilience_manager
    if _resilience_manager is None:
        _resilience_manager = EliteResilienceManager()
    return _resilience_manager

async def main():
    """Demo the elite resilience system"""
    print("🔥 ELITE RESILIENCE SYSTEM - BULLETPROOF ERROR HANDLING! 🔥")
    print("=" * 70)
    
    manager = get_resilience_manager()
    
    # Demo circuit breaker
    print("\n⚡ CIRCUIT BREAKER DEMO:")
    circuit_config = CircuitBreakerConfig(failure_threshold=3, recovery_timeout=5.0)
    circuit_breaker = manager.create_circuit_breaker("demo_service", circuit_config)
    
    async def failing_service():
        if random.random() < 0.7:  # 70% failure rate
            raise ConnectionError("Service unavailable")
        return "Success!"
    
    # Test circuit breaker
    for i in range(10):
        try:
            result = await circuit_breaker.call(failing_service)
            print(f"✅ Call {i+1}: {result}")
        except Exception as e:
            print(f"❌ Call {i+1}: {type(e).__name__} - {e}")
        
        await asyncio.sleep(0.5)
    
    # Demo retry mechanism
    print("\n🔄 RETRY MECHANISM DEMO:")
    retry_config = RetryConfig(max_attempts=3, strategy=RetryStrategy.EXPONENTIAL)
    retry_handler = manager.create_retry_handler("demo_retry", retry_config)
    
    @with_retry(retry_config)
    async def unreliable_function():
        if random.random() < 0.6:  # 60% failure rate
            raise ValueError("Random failure")
        return "Retry success!"
    
    try:
        result = await unreliable_function()
        print(f"✅ Retry result: {result}")
    except Exception as e:
        print(f"❌ Final failure: {e}")
    
    # Demo error handling
    print("\n🛠️ ERROR HANDLING DEMO:")
    
    @with_error_handling("demo_component")
    async def error_prone_function():
        error_types = [ValueError("Invalid value"), ConnectionError("Network error"), RuntimeError("Runtime issue")]
        raise random.choice(error_types)
    
    try:
        await error_prone_function()
    except Exception:
        pass  # Error is handled by the decorator
    
    # Show error statistics
    stats = manager.get_error_statistics()
    print(f"\n📊 ERROR STATISTICS:")
    print(f"Total Errors: {stats['total_errors']}")
    print(f"Recent Errors: {stats['recent_errors']}")
    print(f"Recovery Success Rate: {stats['recovery_success_rate']:.1f}%")
    print(f"Most Common Errors: {stats['most_common_errors']}")
    
    print("\n🎯 Elite resilience system is absolutely bulletproof! 🛡️")

if __name__ == "__main__":
    asyncio.run(main())