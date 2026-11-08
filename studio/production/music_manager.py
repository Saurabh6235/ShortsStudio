# ASSET PRODUCTION / music + SFX: checks the music provider in "use.music" has every track the mix needs.
# Which track plays where is decided by the scene planner using the channel's "music" roles (tension / build / uplift).
from ..core.services import provider

def run(job):
    m = provider(job, 'music', 'music'); d = m.prepare(job)
    job.data['audio_kit'] = str(d)
    return f'music + SFX ready from {m.name} ({d})'
