# Configuration lives outside the code:
#   config/studio.json            which provider each role uses, provider profiles, pipeline switches, retry, export
#   channels/<name>/channel.json  the channel profile: languages, voices, CTA, prompts, brand kit, music roles
#   .env                          API keys (never printed)
import json, os
from pathlib import Path
from .exceptions import ConfigError

ROOT = Path(__file__).resolve().parents[2]

def load_env():
    env = ROOT / '.env'
    for line in env.read_text(encoding='utf-8').splitlines() if env.exists() else []:
        k, sep, v = line.partition('=')
        if sep and k.strip() and not k.strip().startswith('#'): os.environ.setdefault(k.strip(), v.strip())

def _read(p):
    try: return json.load(open(p, encoding='utf-8'))
    except FileNotFoundError: raise ConfigError(f'missing file: {p}')
    except json.JSONDecodeError as e: raise ConfigError(f'{p.name} is not valid JSON (line {e.lineno}, column {e.colno}): {e.msg} - check commas and quotes')

class Config:
    def __init__(self, channel=None):
        load_env()
        self.studio = _read(ROOT / 'config' / 'studio.json')
        self.channel_name = channel or self.studio.get('channel', 'default')
        self.channel_dir = ROOT / 'channels' / self.channel_name
        self.channel = _read(self.channel_dir / 'channel.json')
        self.root = ROOT

    # ---- providers and roles
    def profiles(self, kind): return self.studio.get('providers', {}).get(kind, {})
    def use(self, role):
        name = self.studio.get('use', {}).get(role)
        if not name: raise ConfigError(f'config/studio.json "use" has no "{role}"')
        return name
    def switch(self, name, default=None): return self.studio.get('pipeline', {}).get(name, default)

    # ---- channel
    @property
    def languages(self): return self.channel['languages']                       # list of language dicts
    def lang(self, code): return next(l for l in self.languages if l['code'] == code)
    def lang_codes(self): return [l['code'] for l in self.languages]
    def voice_for(self, provider_type, code):
        v = self.channel.get('voices', {}).get(provider_type, {}).get(code)
        if not v: raise ConfigError(f'channel "{self.channel_name}" has no voice for provider "{provider_type}", language "{code}" (channel.json "voices")')
        return v
    @property
    def kit(self): return self.channel_dir / self.channel.get('kit', 'kit')
    def prompt(self, key):
        p = self.channel.get('prompts', {}).get(key)
        return (self.channel_dir / p).read_text(encoding='utf-8') if p and (self.channel_dir / p).exists() else ''
    def retry(self): return self.studio.get('retry', {'attempts': 3, 'backoff_seconds': 5})
