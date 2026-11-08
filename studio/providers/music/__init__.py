# Music + SFX providers. config/studio.json "use.music" names a profile in "providers.music".
# The composition engine expects these files: bgm_001/002/003.wav (tension / build / uplift beds) and sfx_001..005.mp3
# (whoosh, pop, impact, boom, riser). A provider's prepare() makes sure they exist and returns the folder.
class MusicProvider:
    def __init__(self, profile, cfg): self.p, self.cfg, self.name = profile, cfg, profile['name']
    def prepare(self, job): raise NotImplementedError
