# QUALITY & DELIVERY / rendering: each language's HyperFrames project -> renders/video.mp4 with the render provider
# in "use.render" (this laptop, or a cloud service). Already-rendered languages are kept unless the composition changed.
from ..core.services import provider

def run(job):
    r = provider(job, 'render', 'render'); done = []
    for lang in job.langs:
        out = job.path(f'build_{lang}')
        mp4 = out / 'renders' / 'video.mp4'; idx = out / 'index.html'
        if mp4.exists() and mp4.stat().st_mtime > idx.stat().st_mtime: job.log(f'  {lang}: already rendered'); continue
        job.log(f'  rendering {lang} with {r.name}...'); r.render(out); done.append(lang)
    return f'rendered {", ".join(done) or "nothing new"} ({r.name})'
