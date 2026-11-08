# CONTENT INTELLIGENCE / storyboard: a human-readable plan (storyboard.md) to read before anything is paid for or rendered:
# every line with its voice text, captions, picture and on-screen keyword, plus thumbnail and upload title. No AI, no cost.
def run(job):
    S = job.read('script.json'); langs = job.langs
    out = [f"# {S['name']}  (script by {S.get('written_by', 'hand')})", '',
           f"Twist: {S.get('twist')}   Payoff: {S.get('payoff')}", '',
           '| Line | ' + ' | '.join(f'{c} voice' for c in langs) + ' | Picture | Keyword |', '|' + '---|' * (len(langs) + 3)]
    for l in S['lines']:
        kw = (l.get('kw') or {}).get(langs[0], '') if isinstance(l.get('kw'), dict) else ''
        out.append(f"| {l['id']} | " + ' | '.join(l[c]['tts'].replace('|', '/') for c in langs) + f" | {l.get('img') or ''} | {kw} |")
    th = S['thumb']
    out += ['', '## Thumbnail'] + [f"- {c}: {th['line1'].get(c, '')} / {th['line2'].get(c, '')} / {th['sub'].get(c, '')}" for c in langs]
    out += ['', '## Pictures'] + [f'- {k}: {v}' for k, v in S['images'].items()]
    out += ['', '## Upload titles'] + [f"- {c}: {S['meta'][c]['title']}" for c in langs]
    job.path('storyboard.md').write_text('\n'.join(out) + '\n', encoding='utf-8')
    return 'storyboard.md written'
