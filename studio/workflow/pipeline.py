# The pipeline: an ordered list of stages, each owned by one area. A stage is (name, area, function, enabled(job)).
# Switches in config/studio.json "pipeline" turn optional stages on/off. To add a stage: write run(job) somewhere,
# add one line here. The orchestrator handles state, skipping, resuming and errors.
from ..intelligence import research, script_writer, fact_checker, storyboard
from ..creative import visual_prompts, scene_planner, director, visual_review
from ..production import voice_manager, caption_manager, music_manager, image_manager
from .. import composition
from ..delivery import validator, render_manager, exporter, metadata, storage

def _scene_plan(job):
    return director.run(job) if job.cfg.switch('scene_planner', 'rules') == 'ai' else scene_planner.plan(job)

ON = lambda job: True
STAGES = [
    # name            area                   function                   enabled when
    ('research',      'content intelligence', research.run,             lambda j: bool(j.cfg.switch('research', False))),
    ('script',        'content intelligence', script_writer.run,        ON),
    ('fact_check',    'content intelligence', fact_checker.run,         lambda j: j.cfg.switch('fact_check', 'off') != 'off'),
    ('visual_prompts','creative director',    visual_prompts.run,       ON),
    ('scene_draft',   'creative director',    scene_planner.plan,       ON),
    ('storyboard',    'content intelligence', storyboard.run,           ON),
    ('validate_draft','quality & delivery',   validator.run,            ON),
    ('voice',         'asset production',     voice_manager.run,        ON),
    ('captions',      'asset production',     caption_manager.run,      ON),
    ('music',         'asset production',     music_manager.run,        ON),
    ('images',        'asset production',     image_manager.fetch,      ON),
    ('image_review',  'creative director',    visual_review.run,        lambda j: j.cfg.switch('image_review', 'manual') != 'off'),
    ('scene_plan',    'creative director',    _scene_plan,              ON),
    ('validate',      'quality & delivery',   validator.run,            ON),
    ('plates',        'composition engine',   composition.run_plates,   ON),
    ('compose',       'composition engine',   composition.run_compose,  ON),
    ('mix',           'composition engine',   composition.run_mix,      ON),
    ('render',        'quality & delivery',   render_manager.run,       ON),
    ('export',        'quality & delivery',   exporter.run,             ON),
    ('metadata',      'quality & delivery',   metadata.run,             ON),
    ('storage',       'quality & delivery',   storage.run,              ON),
]
NAMES = [s[0] for s in STAGES]
SCRIPT_STAGES = NAMES[:NAMES.index('storyboard') + 1]       # what WRITE_SCRIPT runs
