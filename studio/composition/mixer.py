# Audio mix: voice + music bed + SFX from cues.json, two-pass loudnorm to -14 LUFS / -1 dBTP (engine code, unchanged).
import html, json, os, re, shutil, subprocess, sys, datetime
from pathlib import Path
W, H = 1080, 1920
KIT = None          # channel kit folder, set by the caller (production/composition managers pass ctx.kit)
def jload(p): return json.load(open(p, encoding='utf-8'))

def mix(vd, lang, kit):
    global KIT; KIT = Path(kit)
    import numpy as np
    vd = Path(vd); out = vd / f'build_{lang}'; C = jload(out / 'cues.json'); KA = KIT / 'audio'
    SR = 48000; T = C['total']; N = int(T * SR)
    def load(f, ch=2):
        x = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', str(f), '-ac', str(ch), '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout, np.float32)
        return x.reshape(-1, ch).copy()
    def lufs(x):
        p = subprocess.run(['ffmpeg', '-v', 'info', '-f', 'f32le', '-ar', str(SR), '-ac', str(x.shape[1]), '-i', '-', '-af', 'ebur128', '-f', 'null', '-'], input=x.astype(np.float32).tobytes(), capture_output=True)
        return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', p.stderr.decode())[-1])
    db = lambda g: 10 ** (g / 20)
    mixed = np.zeros((N, 2), np.float32)
    vp = out / 'voice_proc.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(vd / 'audio' / lang / 'narration.wav'), '-af', 'highpass=f=80,deesser=i=0.4,acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=2,alimiter=limit=0.9', '-ar', str(SR), '-ac', '2', str(vp)], check=True)
    v = load(vp); v *= db(-16 - lufs(v)); mixed[:min(N, len(v))] += v[:N]; VL = -16.0
    def place(x, t, g=1.0):
        s = int(round(t * SR))
        if s < 0: x = x[-s:]; s = 0
        e = min(N, s + len(x)); mixed[s:e] += x[:e - s] * g
    def fade(x, fi=0.0, fo=0.0):
        x = x.copy(); n = len(x)
        if fi > 0: k = min(n, int(fi * SR)); x[:k] *= np.linspace(0, 1, k)[:, None]
        if fo > 0: k = min(n, int(fo * SR)); x[n - k:] *= np.linspace(1, 0, k)[:, None]
        return x
    M = C['music']; mus = np.zeros((N, 2), np.float32)
    for i, m in enumerate(M):
        a = m['at'] if i == 0 else m['at'] - 1.0; b = M[i + 1]['at'] + 0.5 if i + 1 < len(M) else T
        x = load(KA / f'{m["track"]}.wav'); x *= db(VL + m['gain'] - lufs(x))
        need = int((b - a) * SR)
        while len(x) < need: x = np.concatenate([x, x])
        x = fade(x[:need], 0 if i == 0 else 1.5, 1.5 if i + 1 < len(M) else 0.6)
        s = int(a * SR); mus[s:s + len(x)] += x[:N - s]
    for t in C['booms']:
        s = int((t - 0.02) * SR); k = min(int(0.35 * SR), N - s)
        if k > 0: env = np.ones(k); m1 = int(0.1 * SR); env[:m1] = db(-6); env[m1:] = np.linspace(db(-6), 1, k - m1); mus[s:s + k] *= env[:, None]
    mixed += mus
    pk = lambda x, p: x * db(p) / max(1e-6, np.abs(x).max())
    pop = load(KA / 'sfx_002.mp3'); whoosh = load(KA / 'sfx_001.mp3'); impact = load(KA / 'sfx_003.mp3'); boom = load(KA / 'sfx_004.mp3'); riser = load(KA / 'sfx_005.mp3')
    big = C['whooshes'] + C['booms']; pops = []
    for t in C['pops']:
        if (not pops or t - pops[-1] >= 5.5) and all(abs(t - b) > 1.5 for b in big): pops.append(t)
    for t in pops: place(pk(pop, -14), t - 0.12)
    place(pk(impact, -15), 0.45 - 0.75)
    for t in C['whooshes']: place(pk(fade(whoosh, 0, 0.8), -18), t - 0.63)
    for t in C['booms']: place(pk(boom, -12), t - 0.04)
    place(fade(pk(riser, -22), 1.5, 0.05)[:int(10 * SR)], C['riser_to'] - 10.0)
    mixed[-int(0.5 * SR):] *= np.linspace(1, 0, int(0.5 * SR))[:, None]
    f32 = out / 'mix.f32'; mixed.astype(np.float32).tofile(f32)
    p = subprocess.run(['ffmpeg', '-v', 'info', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', str(f32), '-af', 'loudnorm=I=-14:TP=-1.0:LRA=11:print_format=json', '-f', 'null', '-'], capture_output=True, text=True)
    j = json.loads(p.stderr[p.stderr.rfind('{'):p.stderr.rfind('}') + 1])
    af = f"loudnorm=I=-14:TP=-1.0:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true"
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', str(f32), '-af', af, '-ar', '48000', '-c:a', 'pcm_s16le', str(out / 'assets' / 'audio' / 'final_mix.wav')], check=True)
    f32.unlink(); vp.unlink()
    print(lang, 'mixed; pops at', pops)

