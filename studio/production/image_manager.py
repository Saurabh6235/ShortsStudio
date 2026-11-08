# ASSET PRODUCTION / images: fetches every picture in script.json "images" with the provider in "use.images"
# (stock search, your own folder, or AI generation) and makes media/sheet.jpg, a contact sheet for review.
# Already-fetched images are kept; delete a key from media/assets.json to fetch it again.
from ..core.services import provider, call
from . import asset_manager

def fetch(job):
    img = provider(job, 'image', 'images'); S = job.read('script.json'); A = asset_manager.assets(job); new = 0
    for key, query in S['images'].items():
        if key in A and job.path(A[key]).exists(): continue
        p = call(job, img.fetch, job, key, query, what=f'image {key}')
        if p: A[key] = p; new += 1; job.log(f'  {key} -> {p}')
        else: job.log(f'  {key}: nothing found for "{query}" (change the phrase in script.json)')
        asset_manager.save(job, A)
    contact_sheet(job)
    return f'{new} new image(s) with {img.name}, {len(A)} total'

def contact_sheet(job):
    from PIL import Image, ImageDraw
    A = asset_manager.assets(job)
    if not A: return
    sheet = Image.new('RGB', (1500, 1000 if len(A) <= 10 else 1500), (70, 70, 70)); d = ImageDraw.Draw(sheet)
    for k, (key, p) in enumerate(A.items()):
        i = Image.open(job.path(p)); sz = i.size; i = i.convert('RGBA'); bg = Image.new('RGBA', i.size, (70, 70, 70, 255)); bg.alpha_composite(i)
        i = bg.convert('RGB'); i.thumbnail((290, 440)); x = (k % 5) * 300; y = (k // 5) * 500
        sheet.paste(i, (x, y + 20)); d.text((x + 3, y + 3), f'{key} {sz[0]}x{sz[1]} {"PNG" if str(p).endswith(".png") else ""}', fill='yellow')
    sheet.save(job.path('media', 'sheet.jpg'))
