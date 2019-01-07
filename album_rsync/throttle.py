# ------------------------------------
# Name: throttle
# Description:
#   Decorator to throttle calls to a function. Will only allow a function to be called once every 'delay_sec' seconds.
# Params:
#   - delay_sec: Minimum number of seconds between subsequent calls to the decorated function. May be a decimal number.
# ------------------------------------

import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)

class _HistoryItem:
    def __init__(self, func):
        self.func = func
        self.last_call = None

class Throttle:
    def __init__(self):
        self._history = []

    def throttle(self, delay_sec=0):
        def decorator(func):
            state = next((x for x in self._history if x.func == func), None)
            if state is None:
                state = _HistoryItem(func)
                self._history.append(state)
            @wraps(func)
            def wrapper(*args, **kwargs):
                delay_sec_ = self._maybe_call(delay_sec)
                if delay_sec_ > 0 and state.last_call is not None:
                    delay = delay_sec_ - (time.time() - state.last_call)
                    if delay > 0:
                        logger.debug('throttling function call, sleeping for %s seconds', delay)
                        time.sleep(delay)
                state.last_call = time.time()
                return func(*args, **kwargs)
            return wrapper
        return decorator

    def _maybe_call(self, func, *args, **kwargs):
        return func(*args, **kwargs) if callable(func) else func
