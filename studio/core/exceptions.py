# Every error the app raises on purpose. Stages raise these; the orchestrator catches them, records them in the
# job's state.json and decides whether to retry (RetryableError) or stop with a clear message.
class StudioError(Exception):
    """Base class: anything the user should read as a plain message (no traceback needed)."""

class ConfigError(StudioError):
    """config/studio.json or a channel.json is missing a value or has a wrong one."""

class MissingKeyError(ConfigError):
    """An API key named by a provider is not in .env."""

class ProviderError(StudioError):
    """An outside service failed in a way retrying will not fix (bad key, bad model name, unsupported option)."""

class RetryableError(StudioError):
    """A temporary failure: rate limit (429), server error (5xx), timeout, empty reply. The retry manager retries these."""

class ValidationError(StudioError):
    """A script/spec failed validation. .errors holds the list of problems."""
    def __init__(self, msg, errors=None):
        super().__init__(msg); self.errors = errors or []

class StageError(StudioError):
    """A pipeline stage could not finish. Wraps the underlying error with the stage name."""
    def __init__(self, stage, cause):
        super().__init__(f'stage "{stage}" failed: {cause}'); self.stage = stage; self.cause = cause

class UserActionNeeded(StudioError):
    """The pipeline paused on purpose (manual script writing, manual review). The message says what to do next."""
