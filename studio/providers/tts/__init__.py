# Voice providers. config/studio.json "use.voice" names a profile in "providers.tts"; the voice settings per language
# (speaker, pace...) come from the channel profile: channels/<name>/channel.json "voices": {"<type>": {"<lang>": {...}}}.
class TTSProvider:
    def __init__(self, profile, cfg): self.p, self.cfg, self.name = profile, cfg, profile['name']
    def speak(self, text, out_wav, voice_cfg):   # write out_wav, return a short label of the voice used
        raise NotImplementedError
