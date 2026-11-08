# How a stage reaches an outside service: by ROLE, never by provider name.
#   ask(job, 'script', system, user)      -> the LLM named in config/studio.json "use.script_llm"
#   provider(job, 'tts', 'voice')         -> the TTS profile named in "use.voice"
# An LLM role may name ONE profile ("gemini") or a FALLBACK LIST (["gemini", "sarvam"]): the first one that works is used;
# if it fails (missing key, rate limit after retries, provider error) the next one takes over. Once a model has answered,
# it is pinned for the rest of the stage so one script / plan is never written by two different models.
# Every call goes through the retry manager with the "retry" settings.
from .registry import get
from .exceptions import StudioError
from ..workflow.retry import with_retry

def provider(job, kind, role):
    return get(kind, job.cfg.use(role), job.cfg)

def chain(job, role):
    """The LLM profile names for a role, in order (a single name becomes a one-item list)."""
    names = job.cfg.use(f'{role}_llm')
    return list(names) if isinstance(names, list) else [names]

def pin(job, role, name): job.data[f'pin_{role}'] = name

def llm(job, role):
    """The model a stage should plan around: the pinned one, else the first in the role's list."""
    return get('llm', job.data.get(f'pin_{role}') or chain(job, role)[0], job.cfg)

def ask(job, role, system, user, image=None, json_mode=True, max_tokens=None):
    pinned = job.data.get(f'pin_{role}')
    names = [pinned] if pinned else chain(job, role)
    if image: names = [n for n in names if get('llm', n, job.cfg).vision] or names   # only models that can see images
    r = job.cfg.retry(); last = None
    for i, name in enumerate(names):
        m = get('llm', name, job.cfg)
        try:
            out = with_retry(m.chat, system, user, image=image, json_mode=json_mode, max_tokens=max_tokens,
                             attempts=r.get('attempts', 3), backoff=r.get('backoff_seconds', 5), log=job.log, what=f'{role} ({m.name})')
            pin(job, role, name); return out
        except StudioError as e:
            last = e
            if i < len(names) - 1: job.log(f'  {role}: "{name}" failed ({str(e)[:140]}) - falling back to "{names[i + 1]}"')
    raise last

def call(job, fn, *a, what='', **kw):
    r = job.cfg.retry()
    return with_retry(fn, *a, attempts=r.get('attempts', 3), backoff=r.get('backoff_seconds', 5), log=job.log, what=what, **kw)
