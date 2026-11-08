# Kokoro-82M on this laptop through the HyperFrames CLI: free, offline, more robotic. voice_cfg: voice (hm_omega, am_michael...), speed
import os, subprocess, sys, tempfile
from pathlib import Path
from ...core.registry import register
from ...core.exceptions import ProviderError
from . import TTSProvider

@register('tts', 'kokoro')
class Kokoro(TTSProvider):
    def speak(self, text, out_wav, v):
        env = dict(os.environ, HYPERFRAMES_PYTHON=os.environ.get('HYPERFRAMES_PYTHON', sys.executable), HEYGEN_NO_ANALYTICS='1', CI='1')
        with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False, encoding='utf-8') as f: f.write(text); tf = f.name
        try:
            r = subprocess.run(f'npx --yes hyperframes@0.9.5 tts "{tf}" --voice {v["voice"]} --speed {v.get("speed", 1.0)} -o "{out_wav}"',
                               shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace', env=env)
        finally:
            os.unlink(tf)
        if r.returncode or not Path(out_wav).exists(): raise ProviderError(f'Kokoro failed: {(r.stderr or r.stdout)[-300:]}')
        return v['voice']
