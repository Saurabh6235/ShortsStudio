# Provider registry: every provider class registers itself under (kind, type) with @register.
# Code asks for a provider by the name used in config, never by importing a concrete class:
#     llm = get('llm', 'gemini', ctx)      ->  profile "gemini" in config/studio.json -> its "type" -> class
# Adding a provider = one new file in providers/<kind>/ with a class decorated @register('<kind>', '<type>').
import importlib, pkgutil
from .exceptions import ConfigError

_REGISTRY = {}

def register(kind, type_name):
    def deco(cls):
        _REGISTRY[(kind, type_name)] = cls; cls.kind, cls.type_name = kind, type_name; return cls
    return deco

def _load_all():
    import studio.providers as pkg
    for sub in ('llm', 'tts', 'image', 'music', 'render'):
        sp = importlib.import_module(f'studio.providers.{sub}')
        for m in pkgutil.iter_modules(sp.__path__):
            if not m.name.startswith('_'): importlib.import_module(f'studio.providers.{sub}.{m.name}')

def available(kind=None):
    _load_all()
    return sorted(k for k in _REGISTRY if kind in (None, k[0]))

def get(kind, name, cfg):
    """kind: llm|tts|image|music|render. name: profile name from config. cfg: the Config object."""
    _load_all()
    profiles = cfg.profiles(kind)
    if name not in profiles: raise ConfigError(f'{kind} profile "{name}" is not defined in config/studio.json "{kind}" (have: {", ".join(profiles)})')
    p = dict(profiles[name]); p.setdefault('name', name)
    t = p.get('type')
    if (kind, t) not in _REGISTRY:
        raise ConfigError(f'{kind} profile "{name}" has type "{t}", but no such provider exists (have: {", ".join(x[1] for x in available(kind))})')
    return _REGISTRY[(kind, t)](p, cfg)
