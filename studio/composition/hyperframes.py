# HyperFrames composition builder: spec.json + timing -> HTML/GSAP project in <job>/build_<lang>/ (engine code, unchanged).
import html, json, os, re, shutil, subprocess, sys, datetime
from pathlib import Path
W, H = 1080, 1920
KIT = None          # channel kit folder, set by the caller (production/composition managers pass ctx.kit)
def jload(p): return json.load(open(p, encoding='utf-8'))
from .animations import diag, svg_wrap, radar_icon, GLOW

BASE_CSS = """
#root{position:absolute;inset:0;overflow:hidden;background:#03060E}
.shot{position:absolute;left:0;top:0;width:1080px;height:1920px;overflow:hidden}
.push{position:absolute;left:0;top:0;width:1080px;height:1920px}
.plate{position:absolute;left:0;top:0;width:1080px;height:1920px;object-fit:cover}
.cut{position:absolute;display:block}
.kw{position:absolute;left:60px;width:960px;text-align:center}
.kw span{display:inline-block}
.punch{font-family:Oswald,sans-serif;font-weight:700;font-size:150px;line-height:1.0;color:#FFFFFF;-webkit-text-stroke:6px #000;paint-order:stroke fill;text-shadow:0 6px 24px rgba(0,0,0,.6);text-transform:uppercase}
.wide{font-family:Montserrat,sans-serif;font-weight:700;font-size:92px;line-height:1.04;color:#FFFFFF;text-shadow:0 4px 18px rgba(0,0,0,.55);text-transform:uppercase}
.tag{position:absolute;font-family:Montserrat,sans-serif;font-weight:600;font-size:30px;letter-spacing:.02em;color:rgba(255,255,255,.92);text-transform:uppercase;white-space:nowrap}
.tag span{display:inline-block;padding:10px 18px;border:2px solid rgba(98,166,226,.9);border-radius:10px;background:rgba(3,6,14,.55);box-shadow:0 0 18px rgba(16,115,199,.6)}
.tag.warm span{border-color:rgba(239,136,10,.95);box-shadow:0 0 18px rgba(239,136,10,.6)}
.flash{position:absolute;left:0;top:0;width:1080px;height:1920px;background:#FFFFFF}
.streak{position:absolute;left:-200px;width:1480px;height:10px;background:linear-gradient(90deg,rgba(16,115,199,0),#62A6E2 40%,#FFFFFF 50%,#62A6E2 60%,rgba(16,115,199,0));box-shadow:0 0 40px 16px rgba(16,115,199,.75)}
"""

class Scene:
    def __init__(s, sid, start, end, fade_in=0.0, underlay=''):
        s.id, s.start, s.end, s.fade_in, s.underlay = sid, start, end, fade_in, underlay
        s.html, s.js, s.z = [], [], 1
    def L(s, t): return round(t - s.start, 3)
    def shot(s, name, t0, t1, plate=None, push=(1.0, 1.08), inner=''):
        sid = f'{s.id}-shot-{name}'
        img = f'<img class="plate" src="assets/plates/{plate}.jpg" alt="">' if plate else ''
        s.html.append(f'<div id="{sid}" class="clip shot" data-start="{s.L(t0)}" data-duration="{round(t1 - t0, 3)}" style="z-index:{s.z}"><div id="{sid}-push" class="push">{img}{inner}</div></div>')
        s.z += 1
        if push: s.js.append(f'tl.fromTo("#{sid}-push",{{scale:{push[0]}}},{{scale:{push[1]},duration:{round(t1 - t0, 3)},ease:"none"}},{s.L(t0)});')
        return sid
    def kw(s, kid, text, t0, t1, cls='wide', top=420):
        eid = f'{s.id}-{kid}'
        s.html.append(f'<div id="{eid}" class="clip kw {cls}" data-start="{s.L(t0)}" data-duration="{round(t1 - t0, 3)}" style="top:{top}px;z-index:{s.z + 20}"><span id="{eid}-in">{html.escape(text)}</span></div>')
        s.js.append(f'tl.fromTo("#{eid}-in",{{opacity:0,scale:0.85}},{{opacity:1,scale:1,duration:0.25,ease:"back.out(1.7)"}},{s.L(t0)});')
        s.js.append(f'tl.to("#{eid}-in",{{opacity:0,duration:0.2,ease:"power2.in"}},{round(s.L(t1) - 0.22, 3)});')
    def tag(s, kid, text, t0, t1, x, y, warm=False):
        eid = f'{s.id}-{kid}'
        s.html.append(f'<div id="{eid}" class="clip tag{" warm" if warm else ""}" data-start="{s.L(t0)}" data-duration="{round(t1 - t0, 3)}" style="left:{x}px;top:{y}px;z-index:{s.z + 20}"><span id="{eid}-in">{html.escape(text)}</span></div>')
        s.js.append(f'tl.fromTo("#{eid}-in",{{opacity:0,y:16}},{{opacity:1,y:0,duration:0.3,ease:"power3.out"}},{s.L(t0)});')
    def raw(s, h): s.html.append(h)
    def anim(s, js): s.js.append(js)
    def write(s, outdir):
        fade = f'tl.fromTo("#{s.id}-wrap",{{opacity:0}},{{opacity:1,duration:{s.fade_in},ease:"sine.inOut"}},0);' if s.fade_in else ''
        under = (f'<div id="{s.id}-under" class="clip" data-start="0" data-duration="{s.fade_in + 0.05}" style="position:absolute;inset:0;z-index:0">{s.underlay}</div>') if s.underlay else ''
        doc = f'''<template>
<style>{BASE_CSS}</style>
<div id="root" data-composition-id="{s.id}" data-width="1080" data-height="1920">
{under}
<div id="{s.id}-wrap" style="position:absolute;inset:0;z-index:1">
{chr(10).join(s.html)}
</div>
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
{fade}
{chr(10).join(s.js)}
window.__timelines["{s.id}"] = tl;
</script>
</template>
'''
        open(outdir / 'compositions' / f'{s.id}.html', 'w', encoding='utf-8').write(doc)

# ---------- diagram library (SVG drawn in code, animated with GSAP). Each returns inner html; anims added to the scene.

def compose(vd, lang, kit):
    global KIT; KIT = Path(kit)
    vd = Path(vd); S = jload(vd / 'spec.json'); T = jload(vd / 'audio' / lang / 'timing.json')
    LS = {l['id']: l for l in T['lines']}
    def R(ref):  # "L05", "L05:2", "L05:2+0.3", "L05-0.2", "end"
        if isinstance(ref, (int, float)): return float(ref)
        m = re.match(r'(L\d+|end)(?::(\d+))?([+-][\d.]+)?$', ref)
        lid, ci, off = m.group(1), m.group(2), float(m.group(3) or 0)
        if lid == 'end': base = END_START
        elif ci is None: base = LS[lid]['start']
        else: base = [c for c in T['captions'] if c['line'] == lid][int(ci)]['start']
        return round(base + off, 3)
    def tx(v): return v[lang] if isinstance(v, dict) else v
    END_START = round(T['voice_end'] + 0.22, 3); TOTAL = round(END_START + 1.35, 3)
    out = vd / f'build_{lang}'; (out / 'compositions').mkdir(parents=True, exist_ok=True)
    (out / 'assets' / 'plates').mkdir(parents=True, exist_ok=True); (out / 'assets' / 'brand').mkdir(parents=True, exist_ok=True); (out / 'assets' / 'audio').mkdir(parents=True, exist_ok=True)
    for f in (vd / 'plates').iterdir(): shutil.copy(f, out / 'assets' / 'plates' / f.name)
    shutil.copy(KIT / 'brand' / 'endcard.mp4', out / 'assets' / 'brand' / 'endcard.mp4')
    for f in ['hyperframes.json', 'package.json']:
        if (KIT / 'brand' / f).exists(): shutil.copy(KIT / 'brand' / f, out / f)
    json.dump({'id': f'{S["slug"]}-{lang}', 'name': f'{S["slug"]}-{lang}'}, open(out / 'meta.json', 'w'))
    secs = S['sections']; scenes = []; pops = []; whooshes = []; booms = []
    # ---- thumbnail card 0 - 0.55
    th = S['thumb']; sc = Scene('thumb', 0.0, 0.55)
    sc.raw(f'<img class="plate" src="assets/plates/{th["plate"]}.jpg" alt="" style="z-index:0">')
    for c in th.get('cuts', []): sc.raw(f'<img class="cut" src="assets/plates/{c["png"]}.png" style="left:{c["x"]}px;top:{c["y"]}px;width:{c["w"]}px;z-index:2" alt="">')
    sc.raw('<img class="cut" src="assets/plates/seal.png" style="left:860px;top:80px;width:150px;z-index:4" alt="">')
    TT = 'font-family:Montserrat,sans-serif;font-weight:800;paint-order:stroke fill;-webkit-text-stroke:10px #6B1000;text-shadow:0 0 24px rgba(239,136,10,.6)'
    h1, h2 = tx(th['line1']), tx(th['line2']); sub = tx(th['sub'])
    sc.raw(f'<div style="position:absolute;left:30px;top:290px;width:1020px;text-align:center;z-index:5;transform:skewX(-6deg)"><div style="{TT};font-size:{th.get("size1", 140)}px;line-height:1.0;color:#FFFFFF;text-transform:uppercase">{html.escape(h1)}</div><div style="{TT};font-size:{th.get("size2", 88)}px;line-height:1.05;color:#FBE414;text-transform:uppercase">{html.escape(h2)}</div></div>')
    sc.raw(f'<div style="position:absolute;left:30px;top:1560px;width:1020px;text-align:center;z-index:5;transform:skewX(-6deg)"><div style="{TT};font-size:66px;line-height:1.05;color:#FBE414">{html.escape(sub)}</div></div>')
    scenes.append((sc, 0.0, 0.55, 20))
    # ---- sections
    starts = [R(s['at']) if i else 0.40 for i, s in enumerate(secs)]
    for i, s in enumerate(secs):
        a = starts[i]; b = starts[i + 1] if i + 1 < len(secs) else END_START
        dis = s.get('dissolve', False) and i > 0
        a0 = round(a - 0.5, 3) if dis else a
        under = ''
        if dis:
            prev = secs[i - 1]['shots'][-1]
            if prev.get('plate'): under += f'<img class="plate" src="assets/plates/{prev["plate"]}.jpg" alt="">'
            if prev.get('cut'): c = prev['cut']; under += f'<img class="cut" src="assets/plates/{c["png"]}.png" alt="" style="left:{c["x"]}px;top:{c["y"]}px;width:{c["w"]}px">'
            whooshes.append(a)
        sc = Scene(s['id'], a0, b, fade_in=1.0 if dis else 0.0, underlay=under)
        shots = s['shots']; sts = [a0] + [R(sh['at']) for sh in shots[1:]]
        for j, sh in enumerate(shots):
            t0 = sts[j]; t1 = sts[j + 1] if j + 1 < len(shots) else b
            inner = ''
            if sh.get('cut'):
                c = sh['cut']; cid = f'{s["id"]}-{sh["name"]}-cut'
                inner += f'<img id="{cid}" class="cut" src="assets/plates/{c["png"]}.png" style="left:{c["x"]}px;top:{c["y"]}px;width:{c["w"]}px" alt="">'
                if c.get('move'):
                    x0, y0, x1, y1, r0, r1 = (c['move'] + [0, 0])[:6]
                    sc.anim(f'tl.fromTo("#{cid}",{{x:{x0},y:{y0},rotation:{r0}}},{{x:{x1},y:{y1},rotation:{r1},duration:{round(t1 - t0, 3)},ease:"sine.inOut"}},{sc.L(t0)});')
            if sh.get('diagram'):
                d = dict(sh['diagram']); d['_ats'] = [R(x) for x in d.get('ats', [])]
                inner += diag(sc, f'{s["id"]}-{sh["name"]}-d', d['type'], t0, t1, d, {k: tx(v) for k, v in d.get('text', {}).items()})
            if sh.get('cta'):
                inner += ('<img id="cta-seal" class="cut" src="assets/plates/seal.png" style="left:300px;top:560px;width:480px" alt="">'
                          '<div id="cta-btn" style="position:absolute;left:250px;top:1120px;width:580px;height:130px;border-radius:65px;background:#E62117;box-shadow:0 0 40px rgba(230,33,23,.7);display:flex;align-items:center;justify-content:center;font-family:Montserrat,sans-serif;font-weight:800;font-size:58px;color:#FFFFFF">🔔 SUBSCRIBE</div>'
                          '<div id="cta-hand" style="position:absolute;left:700px;top:1190px;font-size:110px">👆</div>')
                ct = R(sh['cta_at']) if sh.get('cta_at') else t0 + 0.8
                sc.anim(f'tl.fromTo("#cta-seal",{{scale:0.6,opacity:0,rotation:-20}},{{scale:1,opacity:1,rotation:0,duration:0.5,ease:"back.out(1.8)"}},{sc.L(t0)});')
                sc.anim(f'tl.fromTo("#cta-btn",{{scale:0.5,opacity:0}},{{scale:1,opacity:1,duration:0.4,ease:"back.out(2)"}},{sc.L(ct)});')
                sc.anim(f'tl.fromTo("#cta-hand",{{opacity:0,x:120,y:120}},{{opacity:1,x:0,y:0,duration:0.4,ease:"power3.out"}},{round(sc.L(ct) + 0.4, 3)});')
                sc.anim(f'tl.to("#cta-btn",{{scale:0.92,duration:0.12,yoyo:true,repeat:1}},{round(sc.L(ct) + 0.85, 3)});')
                sc.anim(f'tl.set("#cta-btn",{{background:"#3A3A3A"}},{round(sc.L(ct) + 1.1, 3)});')
            sc.shot(sh['name'], t0, t1, sh.get('plate'), push=tuple(sh['push']) if 'push' in sh else (1.0, 1.08), inner=inner)
            if sh.get('flash'):
                sc.raw(f'<div id="{s["id"]}-flash" class="clip flash" data-start="{sc.L(t0)}" data-duration="0.3" style="z-index:90"></div>')
                sc.anim(f'tl.fromTo("#{s["id"]}-flash",{{opacity:1}},{{opacity:0,duration:0.28,ease:"power2.out"}},{sc.L(t0)});'); booms.append(t0)
            if sh.get('streak'):
                sc.raw(f'<div id="{s["id"]}-sw" class="clip" data-start="{sc.L(t0)}" data-duration="0.5" style="position:absolute;inset:0;z-index:80"><div id="{s["id"]}-streak" class="streak" style="top:900px"></div></div>')
                sc.anim(f'tl.fromTo("#{s["id"]}-streak",{{opacity:1,scaleX:0.2}},{{opacity:0,scaleX:1.2,duration:0.45,ease:"power2.out"}},{sc.L(t0)});'); booms.append(t0)
            for k, kwd in enumerate(sh.get('kw', [])):
                k0 = R(kwd['at']); k1 = R(kwd['until']) if kwd.get('until') else t1 - 0.05
                sc.kw(f'{sh["name"]}-k{k}', tx(kwd['text']), k0, k1, kwd.get('cls', 'wide'), kwd.get('top', 420)); pops.append(k0)
            for k, tg in enumerate(sh.get('tags', [])):
                sc.tag(f'{sh["name"]}-t{k}', tx(tg['text']), R(tg['at']), R(tg['until']) if tg.get('until') else t1, tg['x'], tg['y'], tg.get('warm', False))
            if sh.get('data'):
                dd = sh['data']; d0 = R(dd['at']); nid = f'{s["id"]}-{sh["name"]}-num'
                sc.raw(f'<div id="{nid}-box" class="clip" data-start="{sc.L(d0)}" data-duration="{round(t1 - d0, 3)}" style="position:absolute;left:0;width:1080px;top:1225px;text-align:center;z-index:60;font-family:Montserrat,sans-serif;color:rgba(255,255,255,.92)"><span style="font-weight:700;font-size:64px">{html.escape(dd.get("prefix", ""))}</span><span id="{nid}" style="font-weight:700;font-size:64px">0</span><span style="font-weight:500;font-size:34px"> {html.escape(dd.get("unit", ""))}</span><span style="font-weight:500;font-size:28px"> {html.escape(tx(dd.get("label", "")))}</span></div>')
                sc.anim(f'(function(){{const o={{v:0}};tl.fromTo(o,{{v:0}},{{v:{dd["to"]},duration:0.6,ease:"power2.out",onUpdate:function(){{document.querySelector("#{nid}").textContent=Math.round(o.v);}}}},{sc.L(d0)});}})();')
                pops.append(d0)
        scenes.append((sc, a0, b, 2 + i))
    for sc, *_ in scenes: sc.write(out)
    # ---- captions
    caps = T['captions']; groups = []
    for i, c in enumerate(caps):
        st = max(0.45, c['start']); en = min(END_START, c['end'] if i < len(caps) - 1 else T['voice_end'] + 0.15)
        if en - st < 0.2: continue
        fs = 58 if len(c['text']) <= 27 else (52 if len(c['text']) <= 31 else 46)
        groups.append(f'<div id="cap-{i}" class="clip cap" data-start="{round(st, 3)}" data-duration="{round(en - st, 3)}"><div class="bar"><span style="font-size:{fs}px">{html.escape(c["text"])}</span></div></div>')
    open(out / 'compositions' / 'captions.html', 'w', encoding='utf-8').write(f'''<template>
<style>
#root{{position:absolute;inset:0}}
.cap{{position:absolute;left:0;top:0;width:1080px;height:1920px}}
.bar{{position:absolute;left:0;top:1357px;width:1080px;box-sizing:border-box;padding:19px 60px 13px;background:#151F31;text-align:center}}
.bar span{{font-family:Montserrat,sans-serif;font-weight:600;line-height:0.92;color:#FFFFFF;white-space:nowrap}}
</style>
<div id="root" data-composition-id="captions" data-width="1080" data-height="1920">
{chr(10).join(groups)}
</div>
<script>window.__timelines["captions"] = gsap.timeline({{ paused: true }});</script>
</template>''')
    hosts = ''.join(f'<div id="{sc.id}" data-composition-id="{sc.id}" data-composition-src="compositions/{sc.id}.html" data-start="{a}" data-duration="{round(b - a, 3)}" data-track-index="{z}" data-track-kind="graphics" data-width="1080" data-height="1920" style="z-index:{z}"></div>\n' for sc, a, b, z in scenes)
    open(out / 'index.html', 'w', encoding='utf-8').write(f'''<!doctype html>
<html><head><meta charset="utf-8"><title>{html.escape(S["name"])} {lang} - Merit Mantra</title>
<style>html,body{{margin:0;background:#03060E}}</style>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js"></script></head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1080" data-height="1920" data-fps="30">
<div id="bgfill" style="position:absolute;inset:0;background:#03060E;z-index:0"></div>
{hosts}<div id="captions" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0" data-duration="{END_START}" data-track-index="30" data-track-kind="captions" data-width="1080" data-height="1920" style="z-index:30"></div>
<video id="endcard" class="clip" src="assets/brand/endcard.mp4" data-start="{END_START}" data-duration="1.35" data-media-start="0.45" data-track-index="40" muted playsinline style="position:absolute;left:0;top:0;width:1080px;height:1920px;object-fit:cover;z-index:40"></video>
<audio id="mix" class="clip" src="assets/audio/final_mix.wav" data-start="0" data-duration="{TOTAL}" data-track-index="50" data-volume="1"></audio>
</div>
<script>window.__timelines["main"] = gsap.timeline({{ paused: true }});</script>
</body></html>''')
    payoff = R(S.get('payoff', 'end'))
    mus = [{'track': m['track'], 'at': R(m['at']) if m['at'] != 'L01' else 0.0, 'gain': m['gain']} for m in S['music']]
    json.dump({'pops': sorted(pops), 'whooshes': whooshes, 'booms': sorted(set(booms)), 'riser_to': payoff, 'music': mus,
               'voice_end': T['voice_end'], 'end_start': END_START, 'total': TOTAL}, open(out / 'cues.json', 'w'), indent=1)
    print(lang, 'composed', len(scenes), 'scenes,', len(groups), 'captions, total', TOTAL)

