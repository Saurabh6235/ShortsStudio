# QUALITY & DELIVERY / metadata: ready-to-paste upload text next to each video:
#   <stem>_YouTube.txt   title, blank line, description, blank line, hashtags (no headers)
#   <stem>_Instagram.txt the Reel caption
from pathlib import Path

def run(job):
    S = job.read('spec.json'); n = 0
    for lang, (d, stem) in (job.read('exports.json')['stems'] if job.has('exports.json') else {}).items():
        m = S['meta'][lang]; d = Path(d)
        (d / f'{stem}_YouTube.txt').write_text(f"{m['title']}\n\n{m['description']}\n\n{m['hashtags']}\n", encoding='utf-8')
        if m.get('instagram'): (d / f'{stem}_Instagram.txt').write_text(m['instagram'] + '\n', encoding='utf-8')
        (d / '.done').write_text('ok'); n += 1
    return f'upload text for {n} video(s)'
