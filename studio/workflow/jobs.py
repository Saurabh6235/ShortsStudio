# Job manager: one input .txt can hold several topics, separated by a line of --- (or ===). Each topic becomes a job
# folder jobs/<slug>/ and the jobs run one after another; a failed job does not stop the others. A summary is printed
# and saved to jobs/batch_<time>.txt.
import datetime, re, shutil
from pathlib import Path
from ..core.config import ROOT
from ..core.log import Log
from ..core.models import Job, slugify
from ..core.exceptions import StudioError, UserActionNeeded
from .state import JobState
from .orchestrator import run_job

def split_topics(text):
    blocks = [b.strip() for b in re.split(r'(?m)^\s*(?:-{3,}|={3,})\s*$', text)]
    return [b for b in blocks if b and not all(l.strip().startswith('#') for l in b.splitlines())]

def topic_slug(block, fallback):
    m = re.search(r'(?im)^\s*topic\s*:\s*(.+)$', block) or re.search(r'(?im)^\s*title\s*:\s*(.+)$', block)
    return slugify(m.group(1) if m else fallback)

def create_job(block, cfg, fallback, interactive=True):
    slug = topic_slug(block, fallback); d = ROOT / 'jobs' / slug; n = 2
    while d.exists() and (d / 'input.txt').exists() and (d / 'input.txt').read_text(encoding='utf-8').strip() != block.strip():
        d = ROOT / 'jobs' / f'{slug}-{n}'; n += 1                       # same slug, different topic: new folder
    d.mkdir(parents=True, exist_ok=True); (d / 'input.txt').write_text(block + '\n', encoding='utf-8')
    return Job(d.name, d, cfg, Log(d / 'job.log'), JobState(d), interactive)

def run_file(path, cfg, until=None, interactive=True):
    path = Path(path); topics = split_topics(path.read_text(encoding='utf-8'))
    if not topics: raise StudioError(f'{path.name} has no topic (see inbox/TEMPLATE.txt)')
    print(f'{path.name}: {len(topics)} topic(s)')
    results = []
    for i, block in enumerate(topics, 1):
        job = create_job(block, cfg, f'{path.stem}-{i}', interactive)
        try:
            run_job(job, until=until); results.append((job.id, 'done' if not until else f'stopped after {until}', ''))
        except UserActionNeeded as e:
            results.append((job.id, 'waiting for you', str(e)))
        except StudioError as e:
            results.append((job.id, 'FAILED', str(e)))
        print(f'[{i}/{len(topics)}] {job.id}: {results[-1][1]}')
    lines = [f'{p:<40} {s:<18} {m}' for p, s, m in results]
    rep = ROOT / 'jobs' / f'batch_{datetime.datetime.now():%Y%m%d_%H%M}.txt'
    rep.write_text(f'{path.name}\n' + '\n'.join(lines) + '\n', encoding='utf-8')
    print('\nSummary:\n' + '\n'.join(lines))
    return results
