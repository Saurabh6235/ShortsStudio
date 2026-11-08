# CONTENT INTELLIGENCE / fact check (optional): "pipeline.fact_check": "off" | "report" | "fix".
#   report  the fact-check LLM lists problems in fact_check.json and the log; the script is not changed
#   fix     flagged lines are rewritten by the script writer with the checker's notes (voice is made after this stage)
import json
from ..core.services import ask, llm
from . import script_writer

SYSTEM = 'You are a strict fact-checker for short explainer videos on any subject. Flag only real errors or misleading statements. Reply with JSON only.'

def run(job):
    mode = job.cfg.switch('fact_check', 'off')
    S = job.read('script.json'); lang = job.langs[-1]
    R = ask(job, 'fact_check', SYSTEM, f"""Topic: {job.path('input.txt').read_text(encoding='utf-8')}
Script lines: {json.dumps({l['id']: l[lang]['tts'] for l in S['lines']}, ensure_ascii=False)}
Check every claim, number and analogy (an analogy must not reverse cause and effect).
Return {{"ok": true/false, "issues": [{{"id": "Lxx", "problem": "...", "suggestion": "a corrected version of the line, in English"}}]}}""", max_tokens=4000)
    m = llm(job, 'fact_check')                    # the model that actually answered (after any fallback)
    issues = [i for i in R.get('issues', []) if i.get('id') in {l['id'] for l in S['lines']}]
    job.write('fact_check.json', {'ok': not issues, 'issues': issues, 'checked_by': f'{m.name} ({m.model})'})
    for i in issues: job.log(f"  ! {i['id']}: {i.get('problem')}  ->  {i.get('suggestion')}")
    if not issues: return f'no problems found by {m.name}'
    if mode != 'fix': return f'{len(issues)} issue(s) reported (fact_check.json); script unchanged'
    ids = [i['id'] for i in issues]
    outline = [{'id': l['id'], 'idea': next(i['suggestion'] for i in issues if i['id'] == l['id']), 'img': l.get('img')} for l in S['lines'] if l['id'] in ids]
    notes = '; '.join(f"{i['id']}: {i.get('problem')}" for i in issues)
    new = {l['id']: l for l in script_writer.write_lines(job, outline, [l for l in S['lines'] if l['id'] not in ids], notes=notes)}
    script_writer.repair(job, list(new.values()))
    S['lines'] = [new.get(l['id'], l) for l in S['lines']]
    job.write('script.json', S)
    return f'{len(issues)} line(s) rewritten after fact check'
