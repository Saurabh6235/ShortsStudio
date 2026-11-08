# Graded 1080x1920 background plates and cut-outs from the fetched images (engine code, unchanged).
import html, json, os, re, shutil, subprocess, sys, datetime
from pathlib import Path
W, H = 1080, 1920
KIT = None          # channel kit folder, set by the caller (production/composition managers pass ctx.kit)
def jload(p): return json.load(open(p, encoding='utf-8'))

def plates(vd, kit):
    global KIT; KIT = Path(kit)
    import numpy as np
    from PIL import Image, ImageFilter, ImageEnhance, ImageDraw
    vd = Path(vd); S = jload(vd / 'spec.json'); A = jload(vd / 'media' / 'assets.json')
    out = vd / 'plates'; out.mkdir(exist_ok=True)
    rng = np.random.default_rng(7)
    def hexrgb(h): return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
    def src(key): return Image.open(vd / A[key])
    def navy_bg(glow=(0.5, 0.42), glow_col='#1073C7', glow2=None, glow2_col='#EF880A'):
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt(((x - W / 2) / W) ** 2 + ((y - H * 0.42) / H) ** 2)
        c0 = np.array(hexrgb('#0A2A5A'), np.float32); c1 = np.array(hexrgb('#03060E'), np.float32)
        t = np.clip(d / 0.62, 0, 1)[..., None]; img = c0 * (1 - t) + c1 * t
        for g, col in [(glow, glow_col), (glow2, glow2_col)]:
            if g:
                dd = np.sqrt(((x - g[0] * W) / W) ** 2 + ((y - g[1] * H) / W) ** 2); a = np.exp(-(dd / 0.39) ** 2)[..., None] * 0.5
                img = img + np.array(hexrgb(col), np.float32) * a
        xs = rng.integers(0, W, 420); ys = rng.integers(0, H, 420); b = rng.uniform(60, 220, 420)
        for xx, yy, bb in zip(xs, ys, b): img[yy, xx] = np.maximum(img[yy, xx], bb)
        return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    def grade(im, sat=1.2, con=1.08, navy=0.35, bright=1.0):
        im = ImageEnhance.Color(im.convert('RGB')).enhance(sat); im = ImageEnhance.Contrast(im).enhance(con)
        if bright != 1.0: im = ImageEnhance.Brightness(im).enhance(bright)
        a = np.asarray(im).astype(np.float32); l = (0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]) / 255
        sh = np.clip(1 - l * 2.2, 0, 1)[..., None] * navy; a = a * (1 - sh) + np.array(hexrgb('#03132E'), np.float32) * sh
        hl = np.clip((l - 0.6) * 2.5, 0, 1)[..., None] * 0.08; a = a * (1 - hl) + np.array(hexrgb('#FFB060'), np.float32) * hl
        a = np.minimum(a, 0.78 * 255 + (a - 0.78 * 255).clip(0) * 0.4)
        return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    def vignette(im, s=0.55):
        y, x = np.mgrid[0:H, 0:W].astype(np.float32); d = np.sqrt(((x - W / 2) / (W * 0.75)) ** 2 + ((y - H / 2) / (H * 0.7)) ** 2)
        v = (1 - np.clip(d - 0.45, 0, 1) * s)[..., None]
        return Image.fromarray(np.clip(np.asarray(im).astype(np.float32) * v, 0, 255).astype(np.uint8))
    def cover(im, fx=0.5, fy=0.5):
        r = max(W / im.width, H / im.height); im = im.resize((int(im.width * r + 1), int(im.height * r + 1)), Image.LANCZOS)
        l = int((im.width - W) * fx); t = int((im.height - H) * fy); return im.crop((l, t, l + W, t + H))
    def framed(im, fy=0.42, p=None):
        g = grade(im, **p) if p else grade(im)
        bg = ImageEnhance.Brightness(cover(g).filter(ImageFilter.GaussianBlur(40))).enhance(0.55)
        r = W / im.width; fg = g.resize((W, int(im.height * r)), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 60, 2))
        fh = fg.height; f = 80; ma = np.ones((fh, W), np.float32); ramp = np.linspace(0, 1, f); ma[:f] *= ramp[:, None]; ma[-f:] *= ramp[::-1][:, None]
        bg.paste(fg, (0, int(H * fy - fh / 2)), Image.fromarray((ma * 255).astype(np.uint8))); return vignette(bg)
    def cutout(im, w):
        c = im.convert('RGBA'); c = c.crop(c.getbbox()); r = w / c.width; c = c.resize((int(c.width * r), int(c.height * r)), Image.LANCZOS)
        rgb = grade(c.convert('RGB'), sat=1.15, con=1.05, navy=0.2).convert('RGBA'); rgb.putalpha(c.getchannel('A'))
        pad = 60; o = Image.new('RGBA', (c.width + 2 * pad, c.height + 2 * pad), (0, 0, 0, 0))
        gl = Image.new('RGBA', o.size, hexrgb('#EF880A') + (0,)); ga = Image.new('L', o.size, 0); ga.paste(c.getchannel('A'), (pad, pad))
        gl.putalpha(ga.filter(ImageFilter.GaussianBlur(26)).point(lambda v: int(v * 0.5))); o.alpha_composite(gl); o.alpha_composite(rgb, (pad, pad)); return o
    for pid, p in S['plates'].items():
        k = p['kind']; gp = p.get('grade')
        if k == 'navy': im = navy_bg(tuple(p.get('glow', (0.5, 0.42))), p.get('glow_col', '#1073C7'), tuple(p['glow2']) if p.get('glow2') else None, p.get('glow2_col', '#EF880A'))
        elif k == 'framed': im = framed(src(p['img']), p.get('fy', 0.42), gp)
        elif k == 'cover':
            g = grade(src(p['img']), **gp) if gp else grade(src(p['img']))
            im = cover(g, p.get('fx', 0.5), p.get('fy', 0.5)).filter(ImageFilter.UnsharpMask(2, 50, 2))
            if p.get('blur'): im = im.filter(ImageFilter.GaussianBlur(p['blur']))
            im = vignette(im)
        elif k == 'cut': cutout(src(p['img']), p.get('w', 900)).save(out / f'{pid}.png'); continue
        im.convert('RGB').save(out / f'{pid}.jpg', quality=92)
        print('plate', pid)
    shutil.copy(KIT / 'brand' / 'seal.png', out / 'seal.png')

