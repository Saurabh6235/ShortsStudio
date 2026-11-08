# Orchestrator: runs a job's stages in order, records each in state.json, skips finished stages (resume after a
# failure or a stop), and re-runs downstream stages automatically when you edit script.json by hand.
import hashlib, time
from ..core.exceptions import StudioError, StageError, UserActionNeeded
from .pipeline import STAGES, NAMES

def _script_hash(job):
    return hashlib.md5(job.path('script.json').read_bytes()).hexdigest() if job.has('script.json') else ''

def run_job(job, until=None, from_stage=None, only=None):
    st = job.state
    if from_stage: st.reset_from(NAMES, from_stage)
    # hand edits to script.json after the draft plan -> redo everything from the draft plan (voice only re-buys changed lines)
    if st.done('scene_draft') and st.data.get('script_hash') and st.data['script_hash'] != _script_hash(job):
        job.log('script.json changed since the last run - re-planning from "scene_draft"'); st.reset_from(NAMES, 'scene_draft')
    job.log.section(f'job {job.id}  (channel: {job.cfg.channel_name})')
    for name, area, fn, enabled in STAGES:
        if only and name != only: continue
        if not enabled(job):
            if st.get(name)['status'] != 'skipped': st.skip(name, 'switched off in config')
        elif st.done(name) and not only:
            pass
        elif name == 'script' and job.has('script.json'):
            st.finish(name, 'script.json already present (hand-written or earlier run)')
        elif name == 'script' and job.cfg.switch('script', 'llm') == 'manual':
            raise UserActionNeeded(f'"pipeline.script" is "manual": write jobs/{job.id}/script.json (copy examples/radar-rain.script.json), '
                                   f'then run BUILD_VIDEO.cmd {job.id}')
        else:
            job.data = {k: v for k, v in job.data.items() if not k.startswith('pin_')}   # each stage picks its model afresh
            job.log(f'\n[{area}] {name}'); st.start(name); t = time.time()
            try:
                note = fn(job) or ''
            except UserActionNeeded:
                raise
            except StudioError as e:
                st.fail(name, e); raise StageError(name, e)
            except Exception as e:                       # unexpected bug: keep the traceback in the log
                import traceback; job.log(traceback.format_exc()); st.fail(name, repr(e)); raise StageError(name, repr(e))
            st.finish(name, note); job.log(f'  -> {note}  ({time.time() - t:.0f}s)')
            if name == 'scene_draft': st.data['script_hash'] = _script_hash(job); st.save()
        if until and name == until: break
    return st
