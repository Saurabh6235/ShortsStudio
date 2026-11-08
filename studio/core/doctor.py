# `studio check`: shows which provider each role uses, whether its key is in .env, and pipeline switches. Changes nothing.
import os
from .registry import get, available
from .exceptions import StudioError

def check(cfg):
    bad = 0; S = cfg.studio; P = S.get('pipeline', {})
    print(f'Channel: {cfg.channel_name} ({cfg.channel.get("display_name", "")}) - languages: {", ".join(l.get("label", l["code"]) for l in cfg.languages)}')
    roles = [('script_llm', 'llm', P.get('script', 'llm') == 'llm'), ('research_llm', 'llm', bool(P.get('research'))),
             ('fact_check_llm', 'llm', P.get('fact_check', 'off') != 'off'), ('director_llm', 'llm', P.get('scene_planner', 'rules') == 'ai'),
             ('review_llm', 'llm', P.get('image_review', 'manual') == 'ai'), ('voice', 'tts', True), ('images', 'image', True),
             ('music', 'music', True), ('render', 'render', True)]
    for role, kind, used in roles:
        if not used: print(f'  [--] {role:<15} not used (switched off in "pipeline")'); continue
        names = cfg.use(role)
        if isinstance(names, list):          # fallback list: check every entry; OK if at least one is usable
            print(f'  [..] {role:<15} fallback list: {" -> ".join(names)}'); ok = 0
            for n in names:
                p = cfg.profiles(kind).get(n, {}); env = p.get('key_env', '')
                why = ('not defined' if n not in cfg.profiles(kind) else f'missing {env} in .env' if env and not os.environ.get(env)
                       else 'no vision' if role == 'review_llm' and not p.get('vision') else '')
                print(f'       {"OK" if not why else "--"} {n} ({p.get("model", p.get("type", "?"))}){"  - skipped: " + why if why else ""}')
                ok += not why
            if not ok:
                soft = {'director_llm': 'the video is still made with the rules scene plan',
                        'review_llm': 'pictures are not AI-reviewed'}.get(role)
                if soft: print(f'  [!!] {role}: no usable entry yet - {soft} (add the key to use it)')
                else: print(f'  [X ] {role}: no usable entry in the list'); bad += 0 if soft else 1
            continue
        try:
            name = names; p = cfg.profiles(kind).get(name, {}); get(kind, name, cfg)
            env = p.get('key_env', 'SARVAM_API_KEY' if p.get('type') == 'sarvam' else '')
            miss = env and not os.environ.get(env)
            extra = []
            if role == 'director_llm' and int(p.get('max_output_tokens', 0)) < 12000: extra.append('max_output_tokens < 12000: rules plan will be used')
            if role == 'review_llm' and not p.get('vision'): extra.append('"vision": false - cannot review images'); miss = True
            print(f'  [{"X " if miss else "OK"}] {role:<15} {name} ({p.get("type")}{": " + p["model"] if p.get("model") else ""})'
                  f'{"  MISSING " + env + " in .env" if miss and env else ""}{"  (" + "; ".join(extra) + ")" if extra else ""}')
            bad += bool(miss)
        except StudioError as e:
            print(f'  [X ] {role:<15} {e}'); bad += 1
    print('Pipeline: ' + ', '.join(f'{k}={v}' for k, v in P.items()))
    print('All good.' if not bad else f'{bad} problem(s) - fix config/studio.json or .env')
    return 1 if bad else 0
