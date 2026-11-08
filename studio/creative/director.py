# CREATIVE DIRECTOR / AI director ("pipeline.scene_planner": "ai", model "use.director_llm"): a strong model designs
# the shot plan - storytelling beats, scene selection per line, timing of keywords, tags, number counters, diagrams,
# thumbnail and music - from the script + the fetched pictures, following docs/COMPOSITION_SPEC.md.
# The plan is validated; on errors the model gets 2 chances to fix it, then the rules plan is kept. A bad answer never
# breaks the video.
import json, shutil
from ..core.config import ROOT
from ..core.services import ask, llm
from ..core.exceptions import StudioError
from ..production.asset_manager import assets, image_kinds
from ..delivery.validator import check
from . import scene_planner

SYSTEM = """You are the video director of a faceless YouTube Shorts / Instagram Reels channel (1080x1920 explainers).
You turn a finished script into a shot plan for an HTML/GSAP rendering engine. Make it visually rich and on-brand:
a new shot every 2.5-4 s, a keyword overlay every 6-10 s, number counters for any figure in the script, small tags that
label what is on screen, diagrams where the engine has a matching type, a white flash on the twist and a light streak on the payoff.
Reply with JSON only."""

def run(job):
    import os
    from ..core.services import chain, pin
    from ..core.registry import get
    note = scene_planner.plan(job)                       # rules plan = base + fallback
    # from "use.director_llm" (one name or a list) take the first model that can write a whole plan and has its key
    usable = [n for n in chain(job, 'director') if get('llm', n, job.cfg).big
              and (not job.cfg.profiles('llm')[n].get('key_env') or os.environ.get(job.cfg.profiles('llm')[n]['key_env']))]
    if not usable:
        return f'AI director skipped: no model in "director_llm" has max_output_tokens >= 12000 and its key in .env; {note}'
    pin(job, 'director', usable[0]); m = llm(job, 'director')
    S = job.read('spec.json'); shutil.copy(job.path('spec.json'), job.path('spec_rules.json'))
    C = job.read('script.json'); kinds = image_kinds(job, list(C['images'])); A = assets(job)
    from PIL import Image
    imgs = {k: {'kind': kinds[k], 'size': '%dx%d' % Image.open(job.path(A[k])).size, 'search': C['images'][k]} for k in kinds if k in A}
    nphr = {l['id']: min(len(l[c]['cap']) for c in S['langs']) for l in S['lines']}
    lines = [{'id': l['id'], 'text': l[S['langs'][-1]]['tts'], 'phrases': nphr[l['id']]} for l in S['lines']]
    ex = json.load(open(ROOT / 'examples' / 'radar-rain.spec.json', encoding='utf-8'))
    guide = (ROOT / 'docs' / 'COMPOSITION_SPEC.md').read_text(encoding='utf-8')
    langs = ', '.join(f'"{c}"' for c in S['langs'])
    prompt = f"""ENGINE SPEC GUIDE:
{guide}

WORKED EXAMPLE (another topic) - plates/thumb/sections/music:
{json.dumps({k: ex[k] for k in ('plates', 'thumb', 'sections', 'music', 'payoff')}, ensure_ascii=False)}

THIS VIDEO
Languages: {S['langs']}. Twist: {C.get('twist')}. Payoff: {S['payoff']}. The LAST line ({S['lines'][-1]['id']}) is the subscribe CTA.
Lines (text, and how many caption phrases each has in its shortest language - a ref "Lxx:N" needs N < phrases):
{json.dumps(lines, ensure_ascii=False)}
Fetched images: {json.dumps(imgs, ensure_ascii=False)}
Use "cut" plates ONLY for images of kind "cut"; "cover" for kind "cover"; "framed" for kind "framed".
Thumbnail texts: {json.dumps(C['thumb'], ensure_ascii=False)}
Music tracks: {json.dumps(job.cfg.channel.get('music', {}))} (only these names).

Return JSON with exactly these keys: "plates", "thumb", "sections", "music", "payoff" - same format as the example.
Requirements: first shot at "L01"; every line has at least one shot; the last shot has "cta": true and "cta_at": "{S['lines'][-1]['id']}:1";
every kw/tag/data/diagram text is an object with {langs}; at most 3 sections with "dissolve": true; diagrams only of the types in the guide."""
    ask_prompt = prompt
    for attempt in range(3):
        try: P = ask(job, 'director', SYSTEM, ask_prompt, max_tokens=16000)
        except StudioError as e: job.log(f'  AI director failed: {e}'); break
        T = dict(S); T.update({k: P[k] for k in ('plates', 'thumb', 'sections', 'music', 'payoff') if k in P})
        for p in T.get('plates', {}).values():           # cut-outs only from real cut-out images
            if p.get('kind') == 'cut' and kinds.get(p.get('img')) != 'cut': p['kind'] = kinds.get(p.get('img'), 'framed')
        job.write('spec.json', T)
        errs, _ = check(job.dir)
        if not errs: return f'AI director ({m.name}): {len(T["sections"])} sections, {sum(len(s["shots"]) for s in T["sections"])} shots'
        job.log(f'  AI director plan has {len(errs)} problem(s) - asking for a fix ({attempt + 1}/3)')
        ask_prompt = prompt + '\n\nYOUR PREVIOUS ANSWER:\n' + json.dumps(P, ensure_ascii=False) + '\n\nIT HAS THESE ERRORS - return the corrected full JSON:\n' + '\n'.join(errs[:40])
    shutil.copy(job.path('spec_rules.json'), job.path('spec.json'))
    return f'AI director could not produce a valid plan - kept the rules plan ({note})'
