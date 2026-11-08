# QUALITY & DELIVERY / storage: where finished files go. config/studio.json "export":
#   "folder": "export"        every video gets its own new folder <folder>/<date>_<Name>_<Language>/
#   "copy_to": ""             optional second location (e.g. a Google Drive / OneDrive synced folder) - copied after export
import datetime, shutil
from pathlib import Path
from ..core.config import ROOT

def export_dir(job, name, lang):
    cfg = job.cfg.studio.get('export', {}); base_root = Path(cfg.get('folder', 'export'))
    base_root = base_root if base_root.is_absolute() else ROOT / base_root
    label = job.cfg.lang(lang).get('label', lang)
    base = base_root / f'{datetime.date.today().isoformat()}_{name}_{label}'; d = base; n = 2
    while d.exists() and (d / '.done').exists(): d = Path(f'{base}-{n}'); n += 1
    d.mkdir(parents=True, exist_ok=True); return d

def run(job):
    dest = job.cfg.studio.get('export', {}).get('copy_to')
    dirs = job.read('exports.json')['dirs'] if job.has('exports.json') else []
    if not dest: return 'kept in ' + ', '.join(Path(d).name for d in dirs) if dirs else 'nothing exported'
    for d in dirs:
        shutil.copytree(d, Path(dest) / Path(d).name, dirs_exist_ok=True)
    return f'copied {len(dirs)} folder(s) to {dest}'
