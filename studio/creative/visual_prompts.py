# CREATIVE DIRECTOR / visual prompts: cleans the picture searches in script.json before fetching. Stock searches ask
# for real photographs (no diagrams / charts / text); for AI image generation ("gemini_image") the search phrases become
# prompts, and the image provider adds the style sentence from its profile.
import re
BAD = r'\b(diagram|chart|infographic|graphic|illustration|vector|icon|labeled|labelled|text)\b'

def run(job):
    S = job.read('script.json'); changed = 0
    for k, q in S['images'].items():
        new = re.sub(r'\s+', ' ', re.sub(BAD, '', q, flags=re.I)).strip()
        if not new.lower().endswith('photo'): new += ' photo'
        if new != q: S['images'][k] = new; changed += 1
    job.write('script.json', S)
    return f'{changed} search phrase(s) cleaned'
