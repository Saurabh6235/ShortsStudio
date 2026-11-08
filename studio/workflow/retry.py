# Retry manager: retries only temporary failures (RetryableError: rate limits, 5xx, timeouts, empty/invalid replies)
# with a growing pause. Config errors and bad keys fail at once with their message. Settings: config/studio.json "retry".
import time
from ..core.exceptions import RetryableError

def with_retry(fn, *args, attempts=3, backoff=5, log=print, what='', **kw):
    last = None
    for i in range(attempts):
        try:
            return fn(*args, **kw)
        except RetryableError as e:
            last = e
            if i < attempts - 1:
                wait = backoff * (i + 1)
                log(f'  {what or fn.__name__}: {str(e)[:160]} - retrying in {wait}s ({i + 2}/{attempts})'); time.sleep(wait)
    raise last
