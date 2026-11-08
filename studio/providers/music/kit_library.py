# The channel's own music/SFX kit: channels/<name>/kit/audio (royalty-free tracks shipped with the channel profile).
from ...core.registry import register
from ...core.exceptions import ConfigError
from . import MusicProvider

NEEDED = ['bgm_001.wav', 'bgm_002.wav', 'bgm_003.wav', 'sfx_001.mp3', 'sfx_002.mp3', 'sfx_003.mp3', 'sfx_004.mp3', 'sfx_005.mp3']

@register('music', 'kit_library')
class KitLibrary(MusicProvider):
    def prepare(self, job):
        d = self.cfg.kit / 'audio'
        missing = [f for f in NEEDED if not (d / f).exists()]
        if missing: raise ConfigError(f'channel kit {d} is missing: {", ".join(missing)}')
        return d
