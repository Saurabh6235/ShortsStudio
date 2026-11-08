# SVG/GSAP diagram library used by scenes ("diagram": {"type": ...}). Add new diagram types to diag() and DIAGRAMS.
import html, json, os, re, shutil, subprocess, sys, datetime
from pathlib import Path
W, H = 1080, 1920
KIT = None          # channel kit folder, set by the caller (production/composition managers pass ctx.kit)
def jload(p): return json.load(open(p, encoding='utf-8'))
GLOW = '<filter id="{id}" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="9" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'

DIAGRAMS = {'wave', 'pulses', 'bounce', 'distance', 'colorbar', 'doppler', 'couplet'}

def svg_wrap(sid, body, defs=''):
    return f'<svg style="position:absolute;left:0;top:0" width="1080" height="1920" viewBox="0 0 1080 1920"><defs>{GLOW.format(id=sid + "-g")}{defs}</defs>{body}</svg>'

def radar_icon(x, y, s=1.0, col='#62A6E2'):
    # simple radar tower: mast + dome
    return (f'<g transform="translate({x},{y}) scale({s})"><rect x="-14" y="0" width="28" height="210" fill="#1B3558"/>'
            f'<path d="M -90 0 A 90 90 0 0 1 90 0 Z" fill="#E8EEF6" stroke="{col}" stroke-width="5"/>'
            f'<line x1="-90" y1="0" x2="90" y2="0" stroke="{col}" stroke-width="5"/></g>')

def diag(sc, sid, kind, t0, t1, P, txt):
    g = sid + '-g'; D = t1 - t0; L0 = sc.L(t0); A = sc.anim
    if kind == 'wave':
        pts = ' '.join(f'{x},{900 + 90 * __import__("math").sin(x / 60)}' for x in range(-200, 1300, 10))
        body = f'<polyline id="{sid}-w" points="{pts}" fill="none" stroke="#7FE7FF" stroke-width="10" filter="url(#{g})" stroke-dasharray="60 0"/>'
        A(f'tl.fromTo("#{sid}-w",{{x:-377}},{{x:0,duration:{round(D, 3)},ease:"none"}},{L0});')
        return svg_wrap(sid, body)
    if kind == 'pulses':
        x, y = P.get('x', 540), P.get('y', 1100)
        arcs = ''.join(f'<path id="{sid}-a{i}" d="M {x - 120} {y - 40} A 140 140 0 0 1 {x + 120} {y - 40}" fill="none" stroke="#7FE7FF" stroke-width="12" stroke-linecap="round" filter="url(#{g})" opacity="0"/>' for i in range(5))
        for i in range(5):
            A(f'tl.fromTo("#{sid}-a{i}",{{opacity:0.95,scale:0.4,svgOrigin:"{x} {y}"}},{{opacity:0,scale:5,svgOrigin:"{x} {y}",duration:1.6,ease:"none",repeat:{max(0, int(D / 1.6) - 1)}}},{round(L0 + i * 0.32, 3)});')
        return svg_wrap(sid, arcs + (radar_icon(x, y, 1.0) if P.get('icon', True) else ''))
    if kind == 'bounce':
        # radar left, small cloud droplets middle, big raindrops right; pulse goes out, echo comes back from big drops
        rx, ry = 150, 1040
        small = ''.join(f'<circle cx="{c[0]}" cy="{c[1]}" r="7" fill="#B9C7D8" opacity="0.8"/>' for c in [(430, 820), (480, 950), (520, 880), (450, 1060), (560, 1000), (500, 1150), (590, 860)])
        big = ''.join(f'<path d="M {c[0]} {c[1] - 34} C {c[0] + 22} {c[1] - 6}, {c[0] + 22} {c[1] + 22}, {c[0]} {c[1] + 22} C {c[0] - 22} {c[1] + 22}, {c[0] - 22} {c[1] - 6}, {c[0]} {c[1] - 34} Z" fill="#62A6E2" stroke="#BFE6FF" stroke-width="3"/>' for c in [(840, 840), (900, 960), (820, 1080), (930, 1150), (870, 760)])
        out = f'<path id="{sid}-out" d="M {rx + 60} 820 A 260 260 0 0 1 {rx + 60} 1260" fill="none" stroke="#7FE7FF" stroke-width="12" filter="url(#{g})" opacity="0"/>'
        back = f'<path id="{sid}-back" d="M 780 820 A 260 260 0 0 0 780 1260" fill="none" stroke="#F57700" stroke-width="12" filter="url(#{g})" opacity="0"/>'
        body = small + big + out + back + radar_icon(rx, ry, 0.8)
        loop = 2.2; n = max(1, int(D / loop))
        for k in range(n):
            t = round(L0 + 0.2 + k * loop, 3)
            A(f'tl.fromTo("#{sid}-out",{{opacity:1,x:0}},{{opacity:1,x:600,duration:1.0,ease:"none"}},{t});')
            A(f'tl.set("#{sid}-out",{{opacity:0}},{round(t + 1.0, 3)});')
            A(f'tl.fromTo("#{sid}-back",{{opacity:1,x:0}},{{opacity:1,x:-560,duration:1.0,ease:"none"}},{round(t + 1.0, 3)});')
            A(f'tl.set("#{sid}-back",{{opacity:0}},{round(t + 2.0, 3)});')
        return svg_wrap(sid, body)
    if kind == 'distance':
        body = (radar_icon(160, 1180, 0.7) + '<path d="M 760 760 C 700 700, 820 640, 880 700 C 940 650, 1040 700, 1010 770 C 1060 800, 1020 860, 960 850 L 780 850 C 720 850, 700 790, 760 760 Z" fill="#9FB3C8"/>'
                + ''.join(f'<line x1="{x}" y1="870" x2="{x - 14}" y2="930" stroke="#62A6E2" stroke-width="5"/>' for x in range(790, 1000, 40))
                + f'<line id="{sid}-go" x1="220" y1="1100" x2="840" y2="900" stroke="#7FE7FF" stroke-width="10" stroke-dasharray="1" pathLength="1" stroke-dashoffset="1"/>'
                + f'<line id="{sid}-ret" x1="840" y1="930" x2="220" y2="1130" stroke="#F57700" stroke-width="10" stroke-dasharray="1" pathLength="1" stroke-dashoffset="1"/>')
        A(f'tl.fromTo("#{sid}-go",{{strokeDashoffset:1}},{{strokeDashoffset:0,duration:0.8,ease:"none"}},{round(L0 + 0.2, 3)});')
        A(f'tl.fromTo("#{sid}-ret",{{strokeDashoffset:1}},{{strokeDashoffset:0,duration:0.8,ease:"none"}},{round(L0 + 1.0, 3)});')
        return svg_wrap(sid, body)
    if kind == 'colorbar':
        rows = P['rows']; body = ''
        for i, (col, key) in enumerate(rows):
            y = 760 + i * 170
            body += f'<g id="{sid}-r{i}" opacity="0"><rect x="200" y="{y}" width="150" height="120" rx="18" fill="{col}"/><text x="400" y="{y + 82}" font-family="Montserrat" font-weight="700" font-size="60" fill="#FFFFFF">{html.escape(txt[key])}</text></g>'
        for i, at in enumerate(P['_ats']):
            A(f'tl.fromTo("#{sid}-r{i}",{{opacity:0,x:-80}},{{opacity:1,x:0,duration:0.3,ease:"power3.out"}},{sc.L(at)});')
        return svg_wrap(sid, body)
    if kind == 'doppler':
        # moving source: circles emitted at successive positions -> bunched in front, spread behind
        cx0, cy = 300, 960; body = ''
        for i in range(7):
            r = 60 + i * 70; x = cx0 + (6 - i) * 45
            body += f'<circle id="{sid}-c{i}" cx="{x}" cy="{cy}" r="{r}" fill="none" stroke="#7FE7FF" stroke-width="6" opacity="0"/>'
        body += f'<circle cx="{cx0 + 6 * 45 + 20}" cy="{cy}" r="34" fill="#F57700" filter="url(#{g})"/>'
        for i in range(7):
            A(f'tl.fromTo("#{sid}-c{i}",{{opacity:0}},{{opacity:0.9,duration:0.25}},{round(L0 + 0.15 + (6 - i) * 0.18, 3)});')
        return svg_wrap(sid, body)
    if kind == 'couplet':
        cx, cy = 540, 900
        body = (f'<ellipse cx="{cx - 130}" cy="{cy}" rx="150" ry="230" fill="#21C55D" opacity="0.85" filter="url(#{g})"/>'
                f'<ellipse cx="{cx + 130}" cy="{cy}" rx="150" ry="230" fill="#E5322D" opacity="0.85" filter="url(#{g})"/>'
                f'<g id="{sid}-rot"><path d="M {cx} {cy - 330} A 330 330 0 0 1 {cx + 330} {cy}" fill="none" stroke="#FFFFFF" stroke-width="12"/>'
                f'<path d="M {cx + 330} {cy - 40} L {cx + 330} {cy + 30} L {cx + 280} {cy - 10} Z" fill="#FFFFFF"/>'
                f'<path d="M {cx} {cy + 330} A 330 330 0 0 1 {cx - 330} {cy}" fill="none" stroke="#FFFFFF" stroke-width="12"/>'
                f'<path d="M {cx - 330} {cy + 40} L {cx - 330} {cy - 30} L {cx - 280} {cy + 10} Z" fill="#FFFFFF"/></g>')
        A(f'tl.fromTo("#{sid}-rot",{{rotation:0,svgOrigin:"{cx} {cy}"}},{{rotation:200,svgOrigin:"{cx} {cy}",duration:{round(D, 3)},ease:"none"}},{L0});')
        return svg_wrap(sid, body)
    raise SystemExit(f'unknown diagram {kind}')

