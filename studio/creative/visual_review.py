# CREATIVE DIRECTOR / visual review of the fetched pictures: "pipeline.image_review": "manual" | "ai" | "off".
#   manual  opens media/sheet.jpg and waits for Enter (skipped in unattended runs)
#   ai      a vision model ("use.review_llm") rejects pictures with text/diagrams/watermarks or the wrong subject;
#           they get a new search phrase and are fetched again (one round)
import json, os
from ..core.services import ask, llm
from ..core.exceptions import StudioError
from ..production import image_manager, asset_manager

def run(job):
    mode = job.cfg.switch('image_review', 'manual')
    if mode == 'manual':
        if not job.interactive: return 'manual review skipped (unattended run)'
        os.startfile(job.path('media', 'sheet.jpg'))
        job.log('Look at the pictures that opened. To swap one: change its phrase in script.json "images", delete its line in')
        job.log(f'media/assets.json, then run BUILD_VIDEO.cmd {job.id} again.')
        try: input('If they look fine, press Enter to continue... ')
        except EOFError: pass
        return 'reviewed by you'
    m = llm(job, 'review'); C = job.read('script.json'); A = asset_manager.assets(job)
    story = [l[job.langs[-1]]['tts'] for l in C['lines']]
    try:
        R = ask(job, 'review', 'You check pictures for a short explainer video. Reply with JSON only.', f"""The contact sheet shows the pictures; each is labelled with its key.
Keys and the search phrase used: {json.dumps(C['images'], ensure_ascii=False)}
The script: {json.dumps(story, ensure_ascii=False)}
Reject pictures that contain text, labels, charts, diagrams, watermarks or logos, and pictures that do not match their purpose.
Return {{"replace": {{"<key>": "<a better search phrase for a real photograph, ending with 'photo'>"}}}} (empty object if all are fine).""",
                image=job.path('media', 'sheet.jpg'), max_tokens=2000)
    except StudioError as e:
        return f'AI review skipped: {e}'
    rep = {k: v for k, v in (R.get('replace') or {}).items() if k in C['images']}
    if not rep: return f'AI review ({m.name}): all pictures OK'
    for k, v in rep.items(): job.log(f'  swap {k}: "{C["images"][k]}" -> "{v}"'); C['images'][k] = v; A.pop(k, None)
    job.write('script.json', C); asset_manager.save(job, A)
    image_manager.fetch(job)
    return f'AI review ({m.name}): swapped {", ".join(rep)}'
