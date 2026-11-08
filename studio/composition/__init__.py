# COMPOSITION ENGINE: plates (graded backgrounds/cut-outs) -> HyperFrames layout + animation (HTML/GSAP) -> audio mix (FFmpeg).
# The engine modules (plates.py, hyperframes.py, animations.py, mixer.py) read spec.json + timing; these wrappers are the stages.
from . import plates as _plates, hyperframes as _hf, mixer as _mix

def run_plates(job):
    _plates.plates(job.dir, job.kit); return 'plates made'

def run_compose(job):
    for lang in job.langs: _hf.compose(job.dir, lang, job.kit)
    return f'HyperFrames projects: {", ".join(f"build_{l}" for l in job.langs)}'

def run_mix(job):
    for lang in job.langs: _mix.mix(job.dir, lang, job.kit)
    return 'mixed to -14 LUFS'
