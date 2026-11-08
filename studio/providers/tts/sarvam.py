# Sarvam Bulbul text-to-speech (pay per use; natural Hindi/Indian-English and 9 more Indian languages).
# voice_cfg: speaker, language (hi-IN, en-IN, ta-IN...), pace, [model, fallback_speakers]
import base64, os
from pathlib import Path
from ...core.registry import register
from ...core.exceptions import MissingKeyError, ProviderError, RetryableError
from . import TTSProvider

@register('tts', 'sarvam')
class Sarvam(TTSProvider):
    used = {}
    def speak(self, text, out_wav, v):
        key = os.environ.get(self.p.get('key_env', 'SARVAM_API_KEY'), '')
        if not key: raise MissingKeyError('SARVAM_API_KEY is missing from .env')
        from sarvamai import SarvamAI
        client = SarvamAI(api_subscription_key=key); lang = v['language']
        speakers = [self.used[lang]] if lang in self.used else [v['speaker']] + v.get('fallback_speakers', [])
        last = None
        for sp in speakers:                 # remember the first speaker that works for this language
            try:
                r = client.text_to_speech.convert(text=text, language_code=lang, model=v.get('model', self.p.get('model', 'bulbul:v4-flash')),
                                                  speaker=sp, pace=v.get('pace', 1.2), speech_sample_rate=44100)
                Path(out_wav).write_bytes(base64.b64decode(''.join(r.audios))); self.used[lang] = sp; return sp
            except Exception as e:
                last = e; msg = str(e)
                if '429' in msg or '503' in msg or 'timeout' in msg.lower(): raise RetryableError(f'Sarvam TTS: {msg[:200]}')
        raise ProviderError(f'Sarvam TTS failed for every speaker {speakers}: {str(last)[:300]}')
