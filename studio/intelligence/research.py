# CONTENT INTELLIGENCE / research (optional, "pipeline.research": true): the research LLM collects accurate facts,
# safe numbers, common misconceptions and everyday analogies for the topic -> research.json, which the script writer uses.
from ..core.services import ask, llm

SYSTEM = 'You are a careful researcher preparing notes for a 60-80 second explainer video on any subject (science, finance, history, tech...). Accuracy first. Reply with JSON only.'

def run(job):
    topic = job.path('input.txt').read_text(encoding='utf-8')
    R = ask(job, 'research', SYSTEM, f"""Topic file:
---
{topic}
---
Return {{"facts": [6-10 short, verified facts], "numbers": [figures with units and how sure they are],
"misconceptions": [2-4 common wrong beliefs], "analogies": [3 everyday analogies that match how it really works], "sources_to_check": [2-4 search phrases]}}.
If a number is uncertain, say "approximately" or give a range.""", max_tokens=4000)
    m = llm(job, 'research')                      # the model that actually answered (after any fallback)
    job.write('research.json', R)
    return f'{len(R.get("facts", []))} facts by {m.name}'
