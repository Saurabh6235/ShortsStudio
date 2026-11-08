# CONTENT INTELLIGENCE / script: topic -> script.json in every channel language.
# Model: config/studio.json "use.script_llm". Style: the channel's prompts/script_brief.txt.
# Big-output models (max_output_tokens >= 12000) write the script in one pass; small ones (Sarvam pay-as-you-go: 4096)
# write an outline, then 4 lines at a time, then the upload text. Usual model slips are repaired afterwards.
import json, re
from ..core.services import ask, llm
from ..core.exceptions import StudioError

DEVANAGARI = re.compile('[ऀ-ॿ]')
CONVERT = 'You convert text between scripts exactly as asked. Reply with JSON only.'

def _brief(job):
    return (job.cfg.prompt('script_brief') or 'You write short, accurate, engaging explainer scripts.') + '\nReply with JSON only.'

def _lang_rules(job):
    """Per-language writing rules, built from the channel's language settings."""
    out = []
    for L in job.cfg.languages:
        c, name = L['code'], L.get('label', L['code'])
        if L.get('voice_text') == 'devanagari':
            out.append(f'- {c}.tts: the {name} line in DEVANAGARI script, never Roman letters (English science words also in Devanagari, '
                       f'numbers as words), 8-16 words, spoken and punchy. Example: "आसमान नीला क्यों दिखता है?"\n'
                       f'- {c}.cap: the same words romanized in lowercase, split into phrases of 3-6 words (max 30 characters each), numbers as digits, at least 2 phrases.')
        elif L.get('voice_text') == 'latin':
            out.append(f'- {c}.tts: the line in natural spoken {name}, 8-16 words; {c}.cap: its lowercase phrases of 3-6 words (at least 2).')
        else:
            out.append(f'- {c}.tts: the line in {name} written in its native script, 8-16 words; {c}.cap: the same words in phrases of 3-6 words (at least 2).')
    return '\n'.join(out)

def _schema_line(job):
    return '{"id": "L01", ' + ', '.join(f'"{c}": {{"tts": "...", "cap": [...]}}' for c in job.langs) + \
           ', "img": "<image key>", "kw": {' + ', '.join(f'"{c}": "..."' for c in job.langs) + '} or null}'

PLAN = """"name": 2-4 English words joined by hyphens for file names (e.g. "Plane-Window-Hole"),
"images": an object of 8-10 entries, key = short lowercase word, value = a stock-photo search phrase for a REAL PHOTOGRAPH of a concrete thing, ending with the word "photo" (never diagrams, charts, infographics, illustrations or anything with text; objects like a plane, dish or bird often come as transparent cut-outs),
"twist": the id of the twist line, "payoff": the id of the payoff line (the last line),
"thumb": {"img": an image key, "line1": {LANGS}, "line2": {LANGS}, "sub": {LANGS}} - thumbnail text in CAPS (romanized for Hindi): line1 2-3 words, line2 2-4 words ending with one emoji, sub a short hook question with one emoji."""
META = """"title": ONE title, max 70 characters, keyword first, a question works well, no emoji, no "|", no hashtags (use the user's title for English if the topic gives one),
"description": 2-3 short paragraphs naming the topic and the key science terms early, ending with a line asking viewers to subscribe to the channel,
"hashtags": 12-16 hashtags separated by commas, including #Shorts and the channel hashtag,
"instagram": a hook line, 2 short lines, a subscribe line and 8-10 hashtags separated by spaces."""

def _plan(job): return PLAN.replace('{LANGS}', '{' + ', '.join(f'"{c}": "..."' for c in job.langs) + '}')

def _context(job):
    topic = job.path('input.txt').read_text(encoding='utf-8')
    extra = ''
    if job.has('research.json'): extra = '\nResearch notes (use them, keep facts correct):\n' + json.dumps(job.read('research.json'), ensure_ascii=False)
    ch = job.cfg.channel
    return f'Channel: {ch.get("display_name", job.cfg.channel_name)} (hashtag {ch.get("hashtag", "")}).\nTopic file from the channel owner:\n---\n{topic}\n---{extra}'

def fix_caps(caps):
    """Re-chunk a line's caption words evenly: up to 6 words / 28 characters per phrase, no lone 1-word tail, at least 2 phrases."""
    words = ' '.join(' '.join(str(c).lower().split()) for c in caps).split()
    out, cur = [], []
    for w in words:
        if cur and (len(' '.join(cur + [w])) > 28 or len(cur) >= 6): out.append(cur); cur = []
        cur.append(w)
    if cur:
        if len(cur) == 1 and out and len(' '.join(out[-1] + cur)) <= 34: out[-1] += cur
        else: out.append(cur)
    if len(out) == 1 and len(out[0]) >= 2: h = (len(out[0]) + 1) // 2; out = [out[0][:h], out[0][h:]]
    return [' '.join(x) for x in out]

def spoken_caps(tts): return fix_caps([re.sub(r"[^\w\s'?%-]", ' ', tts.lower())])

def repair(job, lines):
    """Fix the usual slips: Devanagari voice text written in Roman letters, romanized captions written in Devanagari,
    shortened Latin captions (rebuilt from the spoken words)."""
    for L in job.cfg.languages:
        c = L['code']
        if L.get('voice_text') != 'devanagari': continue
        for i in range(0, len(lines), 8):
            chunk = lines[i:i + 8]
            roman = {l['id']: l[c]['tts'] for l in chunk if not DEVANAGARI.search(l[c].get('tts', ''))}
            if roman:
                D = ask(job, 'script', CONVERT, f'Rewrite each line in DEVANAGARI script, same words; English words also in Devanagari, numbers as words. '
                        f'Example: "Aasmaan neela kyun dikhta hai?" -> "आसमान नीला क्यों दिखता है?"\nLines: {json.dumps(roman, ensure_ascii=False)}\n'
                        'Return {"<id>": "<devanagari line>", ...}')
                for l in chunk:
                    if DEVANAGARI.search(str(D.get(l['id'], ''))): l[c]['tts'] = str(D[l['id']])
            dcaps = {l['id']: l[c]['cap'] for l in chunk if any(DEVANAGARI.search(str(x)) for x in l[c].get('cap', []))}
            if dcaps:
                D = ask(job, 'script', CONVERT, 'Rewrite these caption phrases in romanized lowercase (Latin letters only, same words, same number of phrases). '
                        f'Example: ["आसमान नीला क्यों", "दिखता है?"] -> ["aasmaan neela kyun", "dikhta hai?"]\nPhrases: {json.dumps(dcaps, ensure_ascii=False)}\n'
                        'Return {"<id>": ["...", "..."], ...}')
                for l in chunk:
                    caps = D.get(l['id'])
                    if isinstance(caps, list) and not any(DEVANAGARI.search(str(x)) for x in caps): l[c]['cap'] = caps
        # captions = exactly the spoken words: romanize every full voice line (models tend to shorten caption phrases)
        for i in range(0, len(lines), 8):
            chunk = lines[i:i + 8]
            R = ask(job, 'script', CONVERT, 'Romanize each Hindi/Hinglish line into lowercase Latin letters the way people type Hinglish on YouTube '
                    '(e.g. "aansoo", "kyun", "jaate hain"), SAME words in the same order, nothing left out; English words in normal English '
                    f'spelling; numbers as digits.\nLines: {json.dumps({l["id"]: l[c]["tts"] for l in chunk}, ensure_ascii=False)}\n'
                    'Return {"<id>": "<romanized line>", ...}')
            for l in chunk:
                t = R.get(l['id'])
                if isinstance(t, str) and t.strip() and not DEVANAGARI.search(t): l[c]['cap'] = spoken_caps(t)
        for l in lines:   # last chance, one line at a time
            if any(DEVANAGARI.search(str(x)) for x in l[c]['cap']):
                caps = ask(job, 'script', CONVERT, f'Romanize into lowercase Latin letters, same words: {json.dumps(l[c]["cap"], ensure_ascii=False)}\nReturn {{"cap": ["..."]}}').get('cap')
                if isinstance(caps, list) and not any(DEVANAGARI.search(str(x)) for x in caps): l[c]['cap'] = caps
            if not DEVANAGARI.search(l[c]['tts']): raise StudioError(f'{l["id"]}: {c} voice text is not in Devanagari - run the script stage again')
            if any(DEVANAGARI.search(str(x)) for x in l[c]['cap']): raise StudioError(f'{l["id"]}: {c} captions are still in Devanagari - run the script stage again')
    for L in job.cfg.languages:
        for l in lines:
            if L.get('voice_text') == 'latin': l[L['code']]['cap'] = spoken_caps(l[L['code']]['tts'])
            l[L['code']]['cap'] = fix_caps(l[L['code']]['cap'])

def write_lines(job, outline, done_lines, notes=''):
    """Write the given outline items (4 at a time) in every language. Also used by the fact checker to rewrite lines."""
    out = []
    for i in range(0, len(outline), 4):
        batch = outline[i:i + 4]
        prev = '\n'.join(f"{l['id']}: {l[job.langs[0]]['tts']}" for l in (done_lines + out)[-4:]) or '(none yet)'
        job.log(f'  lines {batch[0]["id"]}-{batch[-1]["id"]}...')
        R = ask(job, 'script', _brief(job), f"""{_context(job)}
Full outline: {json.dumps(outline, ensure_ascii=False)}
Lines written so far (for continuity):
{prev}
{('Corrections to apply: ' + notes) if notes else ''}
Now write ONLY these lines: {json.dumps(batch, ensure_ascii=False)}
Return {{"lines": [{_schema_line(job)}]}}
Rules:
{_lang_rules(job)}
- img: the image key that fits the line best. kw: an on-screen keyword for roughly every second line, 1-3 words in CAPS plus one emoji, else null.""")
        got = {l['id']: l for l in R.get('lines', [])}
        for o in batch:
            l = got.get(o['id'])
            if not l or any(c not in l for c in job.langs): raise StudioError(f'the model skipped line {o["id"]} - run the script stage again')
            out.append({'id': o['id'], **{c: l[c] for c in job.langs}, 'img': l.get('img') or o.get('img'), 'kw': l.get('kw')})
    return out

def run(job):
    """Try each model in "use.script_llm" in order; a model that fails is replaced by the next one for the WHOLE script
    (one-pass and step-by-step writing differ, so a half-written script is never finished by another model)."""
    from ..core.services import chain, pin
    names = chain(job, 'script'); last = None
    for i, name in enumerate(names):
        pin(job, 'script', name)
        try:
            return _run(job)
        except StudioError as e:
            last = e
            if i < len(names) - 1: job.log(f'  script: "{name}" failed ({str(e)[:140]}) - starting again with "{names[i + 1]}"')
    raise last

def _run(job):
    m = llm(job, 'script')
    job.log(f'Writing the script with "{m.name}" ({m.model}), {"one pass" if m.big else "in steps"}...')
    if m.big:
        R = ask(job, 'script', _brief(job), f"""{_context(job)}
Write the complete short. Return JSON with exactly these keys:
{_plan(job)}
"lines": 16-18 lines from L01 (the hook) to the payoff, each {_schema_line(job)}
Line rules:
{_lang_rules(job)}
- kw: an on-screen keyword for roughly every second line, 1-3 words in CAPS plus one emoji, else null.
"meta": {{{', '.join(f'"{c}": {{...}}' for c in job.langs)}}} upload text, each with:
{META}""", max_tokens=16000)
        O, lines, M = R, [{'id': l['id'], **{c: l[c] for c in job.langs}, 'img': l.get('img'), 'kw': l.get('kw')} for l in R['lines']], R['meta']
    else:
        job.log('  outline...')
        O = ask(job, 'script', _brief(job), f"""{_context(job)}
Plan the short. Return JSON with exactly these keys:
{_plan(job)}
"outline": a list of 16-18 items {{"id": "L01".., "idea": one sentence in English of what this line says, "img": one of the image keys}}; L01 is the hook.""")
        lines = write_lines(job, O['outline'], [])
        job.log('  upload text...')
        M = ask(job, 'script', _brief(job), f"""The finished script: {json.dumps([l[job.langs[-1]]['tts'] for l in lines], ensure_ascii=False)}
{_context(job)}
Write upload text. Return {{{', '.join(f'"{c}": {{...}}' for c in job.langs)}}} where each has:
{META}""")
    repair(job, lines)
    ids = [l['id'] for l in lines]
    job.write('script.json', {'name': O.get('name', job.id), 'images': O['images'], 'thumb': O['thumb'], 'twist': O.get('twist'),
                              'payoff': O.get('payoff') if O.get('payoff') in ids else ids[-1], 'langs': job.langs, 'lines': lines,
                              'meta': {c: M[c] for c in job.langs}, 'written_by': f'{m.name} ({m.model})'})
    for l in lines: job.log(f"   {l['id']} {l[job.langs[0]]['tts'][:70]}")
    return f'{len(lines)} lines by {m.name}'
