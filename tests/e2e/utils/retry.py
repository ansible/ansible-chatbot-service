"""Test retry code mechanisms implementations."""

import time


def retry_until_timeout_or_success(attempts, interval, func):
    """Retry the function until timeout or success."""
    for attempt in range(1, attempts + 1):
        print(f"Attempt {attempt} of {attempts}")
        try:
            if func():
                return True
        except Exception as e:
            print(f"Attempt {attempt} failed with exception {e}")
        time.sleep(interval)
    return False