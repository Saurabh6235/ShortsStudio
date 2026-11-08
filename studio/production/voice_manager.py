# ASSET PRODUCTION / voice: one audio file per line and language with the TTS provider in "use.voice".
# Voice settings per language come from the channel profile ("voices" -> provider type -> language).
# audio/<lang>/lines/manifest.json remembers the text and voice of every file: unchanged lines are never paid for twice,
# edited lines (or a different voice) are voiced again automatically.
import json
from ..core.services import provider, call

def run(job):
    tts = provider(job, 'tts', 'voice'); S = job.read('spec.json'); made = 0
    for lang in job.langs:
        v = job.cfg.voice_for(tts.type_name, lang)
        out = job.path('audio', lang, 'lines'); out.mkdir(parents=True, exist_ok=True)
        mf = out / 'manifest.json'; man = json.load(open(mf, encoding='utf-8')) if mf.exists() else {}
        sig = f'{tts.name}|{json.dumps(v, sort_keys=True)}'
        for l in S['lines']:
            f = out / f"{l['id']}.wav"; want = {'text': l[lang]['tts'], 'voice': sig}
            if f.exists() and man.get(l['id']) in (want, None): man.setdefault(l['id'], want); continue
            used = call(job, tts.speak, l[lang]['tts'], f, v, what=f'voice {lang} {l["id"]}')
            man[l['id']] = want; json.dump(man, open(mf, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            job.log(f"  {lang} {l['id']} ok ({tts.name}: {used})"); made += 1
        json.dump(man, open(mf, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return f'{made} line(s) voiced with {tts.name}'
