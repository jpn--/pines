# source: 
# https://stackoverflow.com/questions/20643184/using-python-threads-to-make-thousands-of-calls-to-a-slow-api-with-a-rate-limit

from collections import Iterator
from threading import Lock
import time

class RateLimiter(Iterator):
    """Iterator that yields a value at most once every 'interval' seconds."""
    def __init__(self, interval):
        self.lock = Lock()
        self.interval = interval
        self.next_yield = 0

    def __next__(self):
        with self.lock:
            t = time.monotonic()
            if t < self.next_yield:
                time.sleep(self.next_yield - t)
                t = time.monotonic()
            self.next_yield = t + self.interval


_global_rate_limiters = {}

def GlobalRateLimiter(tag, interval=1):
    global _global_rate_limiters
    if tag not in _global_rate_limiters:
        _global_rate_limiters[tag] = RateLimiter(interval)
    return next(_global_rate_limiters[tag])
