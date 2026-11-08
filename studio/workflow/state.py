# Job state: jobs/<job>/state.json records each stage's status (pending/running/done/failed/skipped), attempts,
# timings and the last error. The orchestrator skips stages that are done, so a failed or stopped job resumes
# where it left off. `studio status <job>` prints it; `studio build <job> --from <stage>` re-runs from a stage.
import datetime, json
from pathlib import Path

def _now(): return datetime.datetime.now().isoformat(timespec='seconds')

class JobState:
    def __init__(self, job_dir):
        self.path = Path(job_dir) / 'state.json'
        self.data = json.load(open(self.path, encoding='utf-8')) if self.path.exists() else {'stages': {}}
    def save(self): json.dump(self.data, open(self.path, 'w', encoding='utf-8'), indent=1)
    def get(self, stage): return self.data['stages'].get(stage, {'status': 'pending', 'attempts': 0})
    def done(self, stage): return self.get(stage)['status'] in ('done', 'skipped')
    def _set(self, stage, **kw):
        s = self.get(stage); s.update(kw); self.data['stages'][stage] = s; self.save()
    def start(self, stage): self._set(stage, status='running', started=_now(), attempts=self.get(stage).get('attempts', 0) + 1, error=None)
    def finish(self, stage, note=None): self._set(stage, status='done', finished=_now(), note=note)
    def skip(self, stage, why): self._set(stage, status='skipped', note=why)
    def fail(self, stage, err): self._set(stage, status='failed', finished=_now(), error=str(err)[:1000])
    def reset_from(self, stages, first):
        hit = False
        for s in stages:
            hit = hit or s == first
            if hit: self.data['stages'].pop(s, None)
        self.save()
    def summary(self, stages):
        rows = []
        for s in stages:
            st = self.get(s); rows.append(f"  {s:<16} {st['status']:<8} {st.get('note') or st.get('error') or ''}"[:160])
        return '\n'.join(rows)
