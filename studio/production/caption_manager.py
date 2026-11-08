# ASSET PRODUCTION / captions + timing: joins the voice lines into narration.wav (trims silence, shortens pauses,
# 0.25 s beat before the twist and payoff) and times every caption phrase -> audio/<lang>/timing.json. Free, local.
import json, re, subprocess
from pathlib import Path
import numpy as np

def spec_of(vd): return json.load(open(Path(vd) / 'spec.json', encoding='utf-8'))

def narrate(vd, lang):
    S = spec_of(vd); SR = 48000; beats = set(S.get('beats', []))
    base = Path(vd) / 'audio' / lang
    t = 0.05; out = [np.zeros(int(0.05 * SR), np.float32)]; timing = []
    for l in S['lines']:
        x = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', str(base / 'lines' / f"{l['id']}.wav"), '-ac', '1', '-ar', str(SR),
                                          '-af', 'silenceremove=stop_periods=-1:stop_duration=0.12:stop_threshold=-38dB', '-f', 'f32le', '-'],
                                         capture_output=True).stdout, np.float32)
        idx = np.where(np.abs(x) > 0.01)[0]; x = x[max(0, idx[0] - int(0.02 * SR)):idx[-1] + int(0.04 * SR)]
        if l['id'] in beats: out.append(np.zeros(int(0.25 * SR), np.float32)); t += 0.25
        timing.append({'id': l['id'], 'start': round(t, 3), 'end': round(t + len(x) / SR, 3), 'cap': l[lang]['cap']})
        out.append(x); t += len(x) / SR; out.append(np.zeros(int(0.10 * SR), np.float32)); t += 0.10
    raw = base / 'raw.f32'; np.concatenate(out).astype(np.float32).tofile(raw)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', str(raw), str(base / 'narration.wav')], check=True)
    raw.unlink()
    caps = []
    for s in timing:
        n = [max(1, len(re.sub(r'[^a-z0-9]', '', c.lower()))) for c in s['cap']]; T = s['end'] - s['start']; acc = s['start']
        for c, k in zip(s['cap'], n):
            d = T * k / sum(n); caps.append({'line': s['id'], 'text': c, 'start': round(acc, 3), 'end': round(acc + d, 3)}); acc += d
    for i in range(len(caps) - 1): caps[i]['end'] = caps[i + 1]['start']
    words = sum(len(' '.join(s['cap']).split()) for s in timing); speech = sum(s['end'] - s['start'] for s in timing)
    json.dump({'lines': timing, 'captions': caps, 'voice_end': timing[-1]['end'], 'words_per_sec': round(words / speech, 2)},
              open(base / 'timing.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print(lang, 'narration done; voice_end', timing[-1]['end'], 'wps', round(words / speech, 2))

def run(job):
    for lang in job.langs: narrate(job.dir, lang)
    T = json.load(open(job.path('audio', job.langs[0], 'timing.json'), encoding='utf-8'))
    return f"voice ends at {T['voice_end']} s, {T['words_per_sec']} words/s"
