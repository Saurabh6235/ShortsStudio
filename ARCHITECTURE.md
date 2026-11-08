# ShortsStudio: architecture

A modular factory for faceless short videos (YouTube Shorts / Instagram Reels) in several languages. **Code** says *how* each step works. **Configuration** says *which* service does it. **Channel profiles** say *what* the content looks and sounds like. Changing an LLM, a voice, the image source or the render machine never needs a code change.

```
                 topic .txt (one or many topics, separated by ---)
                                    |
   workflow/jobs.py  ->  one job folder per topic: jobs/<slug>/
                                    |
   workflow/orchestrator.py runs workflow/pipeline.py STAGES in order, records state.json, retries, resumes
                                    |
 +-------------------+--------------------+-------------------+---------------------+---------------------+
 | CONTENT           | CREATIVE           | ASSET             | COMPOSITION         | QUALITY &           |
 | INTELLIGENCE      | DIRECTOR           | PRODUCTION        | ENGINE              | DELIVERY            |
 | intelligence/     | creative/          | production/       | composition/        | delivery/           |
 |  research         |  visual_prompts    |  voice_manager    |  plates             |  validator          |
 |  script_writer    |  scene_planner     |  caption_manager  |  hyperframes        |  render_manager     |
 |  fact_checker     |  director (AI)     |  image_manager    |  animations         |  exporter           |
 |  storyboard       |  visual_review     |  music_manager    |  mixer (FFmpeg)     |  metadata, storage  |
 +---------+---------+---------+----------+---------+---------+----------+----------+----------+----------+
           |                   |                    |                    |                     |
           +------------ core/services.py: ask(job, role, ...) / provider(job, kind, role) -----+
                                    |
                 core/registry.py  ->  providers/<kind>/<type>.py  (chosen in config/studio.json)
                 llm: openai_compatible | anthropic | cli      tts: sarvam | kokoro
                 image: heygen_stock | local_folder | gemini_image     music: kit_library     render: local | heygen_cloud
```

## Folders

| Folder | Responsibility |
|---|---|
| `studio/core/` | `config.py` (loads `config/studio.json`, the channel profile and `.env`), `models.py` (the Job object and the files a job contains), `exceptions.py` (every deliberate error), `registry.py` (provider plug-ins), `services.py` (stages reach providers *by role*), `log.py`, `doctor.py` (`studio check`) |
| `studio/providers/` | Outside services behind small interfaces. The base class is in each sub-package's `__init__.py`; each concrete provider is one file. |
| `studio/intelligence/` | **Content intelligence**: research → script → fact check → storyboard |
| `studio/creative/` | **Creative director**: visual prompts → scene plan (rules, or the AI director) → visual review of pictures |
| `studio/production/` | **Asset production**: voice, caption timing, images, music; `asset_manager` keeps the registry of fetched files |
| `studio/composition/` | **Composition engine**: graded plates, HyperFrames layout + GSAP animation, diagram library, FFmpeg mix |
| `studio/delivery/` | **Quality & delivery**: validation, rendering, 4K export, upload text, storage/copy |
| `studio/workflow/` | `pipeline.py` (ordered stages), `orchestrator.py` (run/skip/resume), `state.py` (per-job progress), `retry.py` (temporary failures), `jobs.py` (batches) |
| `config/` | `studio.json` (roles → providers, pipeline switches, retry, export), `.env.example` |
| `channels/<name>/` | Channel profile: `channel.json` (languages, voices, CTA, music roles, format), `prompts/` (writing style), `kit/` (music, SFX, end card, logo) |
| `jobs/<slug>/` | One folder per video topic, holding every intermediate file (see `core/models.py`), so any stage can be re-run |
| `export/` | Finished videos, thumbnails and upload text |

## The three extension points

**1. A new provider** (another LLM API, voice, image source, render farm). Add one file, for example `studio/providers/tts/elevenlabs.py`:

```python
from ...core.registry import register
from . import TTSProvider

@register('tts', 'elevenlabs')
class ElevenLabs(TTSProvider):
    def speak(self, text, out_wav, voice_cfg):
        ...  # call the API, write out_wav
        return voice_cfg['voice_id']
```

Then add a profile, `"providers": {"tts": {"eleven": {"type": "elevenlabs", "key_env": "ELEVEN_KEY"}}}`, and select it with `"use": {"voice": "eleven"}`. Its per-language voice settings go in the channel's `"voices": {"elevenlabs": {...}}`.

LLMs rarely need code: most providers are `openai_compatible`, so a new one is just a profile with `base_url`, `model` and `key_env`.

**2. A new stage** (for example thumbnail A/B variants, a chart generator, an auto-uploader):
- Write `run(job)` in the right area folder, returning a one-line note.
- Add one line to `STAGES` in `studio/workflow/pipeline.py`, with an `enabled` condition (usually a switch in `"pipeline"`).

The orchestrator handles state, logging, retries, skipping and resuming.

**3. A new channel** (another niche, brand or language set):
- Copy `channels/merit-mantra` to `channels/<new>`.
- Edit `channel.json`, `prompts/script_brief.txt` and `kit/`.
- Run it with `--channel <new>`, or set `"channel"` in `config/studio.json`.

For languages: Hindi uses Devanagari for the voice with romanized captions, and English uses Latin script. Other Sarvam languages (`ta-IN`, `bn-IN`, `mr-IN`...) use `"voice_text": "native"`.

## Rules the code follows

- **Stages talk through files in the job folder**, never through memory, so a stopped job resumes exactly where it stopped (`state.json`).
- **Stages ask for services by role** (`ask(job, 'script', ...)`, `provider(job, 'tts', 'voice')`), never by provider name.
- **Errors are typed** (`core/exceptions.py`):
  - `RetryableError` is retried with growing pauses.
  - `ConfigError` / `MissingKeyError` / `ProviderError` stop with a plain message.
  - `UserActionNeeded` pauses on purpose.
- **Nothing is paid for twice:** voice lines are cached by text and voice, and images by key. Hand edits to `script.json` re-plan automatically, and only changed lines are re-voiced.
- **AI output is always validated** (`delivery/validator.py`). The AI director falls back to the rules plan, so a bad answer never breaks a video.
