"""Simple token-bucket rate limiter for HTTP requests.

Prevents overwhelming bookmaker endpoints and reduces risk of IP blocking.
"""
from __future__ import annotations

import time
from threading import Lock
from typing import Optional


class RateLimiter:
    """Thread-safe token bucket rate limiter."""
    
    def __init__(self, max_requests: int, period_seconds: int):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed in period
            period_seconds: Time period in seconds
        """
        self.max_requests = max_requests
        self.period = period_seconds
        self.tokens = max_requests
        self.last_refill = time.time()
        self.lock = Lock()
    
    def acquire(self, block: bool = True, timeout: Optional[float] = None) -> bool:
        """
        Acquire permission to make a request.
        
        Args:
            block: If True, wait until token available
            timeout: Max seconds to wait (None = infinite)
        
        Returns:
            True if permission granted, False if denied (non-blocking only)
        """
        deadline = None if timeout is None else time.time() + timeout
        
        while True:
            with self.lock:
                self._refill_tokens()
                
                if self.tokens >= 1:
                    self.tokens -= 1
                    return True
                
                if not block:
                    return False
                
                # Calculate wait time until next token
                time_since_refill = time.time() - self.last_refill
                time_until_next = self.period / self.max_requests - time_since_refill
                
                if deadline and time.time() + time_until_next > deadline:
                    return False
            
            # Sleep outside lock
            sleep_time = min(0.1, time_until_next) if time_until_next > 0 else 0.1
            time.sleep(sleep_time)
    
    def _refill_tokens(self):
        """Refill tokens based on elapsed time (must hold lock)."""
        now = time.time()
        elapsed = now - self.last_refill
        
        if elapsed >= self.period:
            # Full refill
            self.tokens = self.max_requests
            self.last_refill = now
        else:
            # Partial refill (linear)
            new_tokens = (elapsed / self.period) * self.max_requests
            self.tokens = min(self.max_requests, self.tokens + new_tokens)
            if new_tokens >= 1:
                self.last_refill = now
    
    def __enter__(self):
        """Context manager support."""
        self.acquire()
        return self
    
    def __exit__(self, *args):
        """Context manager cleanup (no-op)."""
        pass
