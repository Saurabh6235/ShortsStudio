# ASSET PRODUCTION / asset registry: media/assets.json maps every image key to its file, and image_kinds() tells the
# planners how each picture can be used: "cover" (tall photo, full bleed), "framed" (wide photo over its own blur)
# or "cut" (transparent PNG object with a glow).
from ..core.models import jload, jsave

def assets(job):
    p = job.path('media', 'assets.json')
    return jload(p) if p.exists() else {}

def save(job, A): jsave(job.path('media', 'assets.json'), A)

def image_kinds(job, keys):
    A = assets(job)
    if not A: return {k: 'framed' for k in keys}
    from PIL import Image
    kinds = {}
    for k in keys:
        if k not in A or not job.path(A[k]).exists(): continue        # not fetched: leave it out
        im = Image.open(job.path(A[k]))
        if im.mode in ('RGBA', 'LA') and im.getchannel('A').getextrema()[0] < 20: kinds[k] = 'cut'
        elif im.height >= im.width * 1.1: kinds[k] = 'cover'
        else: kinds[k] = 'framed'
    return kinds
