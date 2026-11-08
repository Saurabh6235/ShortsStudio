# Command line:  py -3.12 -m studio <command>      (the .cmd launchers call these)
#   make   [file.txt] [--all]      topic file(s) from inbox -> finished videos (several topics per file: separate with ---)
#   write  [file.txt]              topic -> script.json + storyboard.md only (read/edit, then `build`)
#   build  <job> [--from STAGE] [--only STAGE]   run/resume a job; --from re-runs from a stage
#   status <job>                   stage-by-stage progress of a job
#   list                           all jobs and their progress
#   check                          configuration, keys and providers (changes nothing)
#   providers                      provider types available to name in config/studio.json
#   stages                         the pipeline stages and their areas
# Options: --channel <name> (default: config/studio.json "channel"), --unattended (never wait for Enter)
import argparse, shutil, sys
from pathlib import Path

def main():
    ap = argparse.ArgumentParser(prog='studio', description='ShortsStudio - faceless short-video factory')
    ap.add_argument('command', choices=['make', 'write', 'build', 'status', 'list', 'check', 'providers', 'stages'])
    ap.add_argument('target', nargs='?'); ap.add_argument('--all', action='store_true')
    ap.add_argument('--from', dest='from_stage'); ap.add_argument('--only')
    ap.add_argument('--channel'); ap.add_argument('--unattended', action='store_true')
    a = ap.parse_args()
    from .core.config import Config, ROOT
    from .core.exceptions import StudioError, UserActionNeeded
    interactive = sys.stdin.isatty() and not a.unattended
    try:
        if a.command == 'providers':
            from .core.registry import available
            for kind, t in available(): print(f'  {kind:<7} {t}')
            return 0
        if a.command == 'stages':
            from .workflow.pipeline import STAGES
            for n, area, *_ in STAGES: print(f'  {n:<16} {area}')
            return 0
        cfg = Config(a.channel)
        if a.command == 'check':
            from .core.doctor import check
            return check(cfg)
        if a.command == 'list':
            from .workflow.state import JobState
            from .workflow.pipeline import NAMES
            for d in sorted((ROOT / 'jobs').iterdir()):
                if d.is_dir():
                    st = JobState(d); done = sum(st.done(n) for n in NAMES)
                    failed = [n for n in NAMES if st.get(n)['status'] == 'failed']
                    print(f'  {d.name:<40} {done}/{len(NAMES)} stages{"  FAILED at " + failed[0] if failed else ""}')
            return 0
        if a.command in ('build', 'status'):
            if not a.target: print('Usage: build <job>   (job = folder name in jobs\\)'); return 2
            from .core.models import open_job
            from .workflow.pipeline import NAMES
            job = open_job(a.target, cfg, interactive)
            if a.command == 'status': print(job.state.summary(NAMES)); return 0
            from .workflow.orchestrator import run_job
            run_job(job, from_stage=a.from_stage, only=a.only); print(f'\nDone. Videos are in the export folder.'); return 0
        # make / write
        from .workflow.jobs import run_file
        from .workflow.pipeline import SCRIPT_STAGES
        inbox = ROOT / 'inbox'; (inbox / 'done').mkdir(parents=True, exist_ok=True)
        files = [Path(a.target)] if a.target else sorted([p for p in inbox.glob('*.txt') if p.name != 'TEMPLATE.txt'], key=lambda p: p.stat().st_mtime)
        if not files: print('Put a topic .txt file in the inbox folder first (copy inbox\\TEMPLATE.txt).'); return 2
        if not a.all and not a.target: files = files[-1:]
        until = SCRIPT_STAGES[-1] if a.command == 'write' else None
        for f in files:
            res = run_file(f, cfg, until=until, interactive=interactive)
            if a.command == 'make' and f.parent == inbox and all(r[1] == 'done' for r in res): shutil.move(str(f), str(inbox / 'done' / f.name))
        if a.command == 'write': print('\nScripts written: read jobs\\<job>\\storyboard.md, edit script.json if needed, then BUILD_VIDEO.cmd <job>')
        return 0
    except UserActionNeeded as e:
        print(f'\nACTION NEEDED: {e}'); return 3
    except StudioError as e:
        print(f'\nERROR: {e}\n(see jobs\\<job>\\job.log; fix and run again - finished stages are not repeated)'); return 1

if __name__ == '__main__':
    sys.exit(main())
