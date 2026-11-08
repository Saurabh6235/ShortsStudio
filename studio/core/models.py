# Data models. Stages pass data through files in the job folder, so a job can stop and resume at any stage:
#
#   jobs/<job>/input.txt         the topic (one block of your .txt)
#   research.json   (intelligence/research)      {"facts": [...], "numbers": [...], "misconceptions": [...], "analogies": [...]}
#   script.json     (intelligence/script_writer) {"name", "images": {key: search}, "thumb": {...}, "twist", "payoff",
#                                                 "lines": [{"id": "L01", "<lang>": {"tts": voice text, "cap": [caption phrases]},
#                                                            "img": key, "kw": {"<lang>": "KEYWORD"} | null}],
#                                                 "meta": {"<lang>": {"title", "description", "hashtags", "instagram"}}}
#   fact_check.json (intelligence/fact_checker)  {"ok": bool, "issues": [{"id", "problem", "suggestion"}]}
#   storyboard.md   (intelligence/storyboard)    human-readable plan to read before rendering
#   audio/<lang>/lines/*.wav, narration.wav, timing.json   (production/voice + captions)
#   media/assets.json + .media/images/*          (production/images)
#   spec.json       (creative/scene_planner or director)  the composition spec - see docs/COMPOSITION_SPEC.md
#   build_<lang>/   (composition)                HyperFrames project, cues.json, final mix
#   state.json      (workflow/state)             which stages are done, attempts, errors
import json, re
from dataclasses import dataclass, field
from pathlib import Path
from .config import Config, ROOT
from .log import Log

def jload(p): return json.load(open(p, encoding='utf-8'))
def jsave(p, data): Path(p).parent.mkdir(parents=True, exist_ok=True); json.dump(data, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
def slugify(s): return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', s.lower())).strip('-')[:40] or 'video'

@dataclass
class Job:
    """Everything a stage needs: the job folder, the configuration, the log and the state."""
    id: str
    dir: Path
    cfg: Config
    log: Log = None
    state: object = None
    interactive: bool = True            # False for unattended runs: never wait for Enter
    data: dict = field(default_factory=dict)

    # convenience accessors used by every stage
    def path(self, *p): return self.dir.joinpath(*p)
    @property
    def langs(self): return self.cfg.lang_codes()
    @property
    def kit(self): return self.cfg.kit
    def has(self, name): return self.path(name).exists()
    def read(self, name): return jload(self.path(name))
    def write(self, name, data): jsave(self.path(name), data)

def open_job(job_id, cfg, interactive=True):
    from ..workflow.state import JobState
    d = ROOT / 'jobs' / job_id
    if not d.exists(): raise FileNotFoundError(f'no job folder jobs/{job_id}')
    return Job(job_id, d, cfg, Log(d / 'job.log'), JobState(d), interactive)
