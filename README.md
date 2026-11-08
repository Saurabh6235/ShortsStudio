# ShortsStudio

**Turn a text file of topics into finished faceless short videos**: YouTube Shorts and Instagram Reels in Hinglish, English or other Indian languages, each with a thumbnail and ready-to-paste upload text.

You write a topic and a hook. ShortsStudio then:
- researches the topic, writes the script and fact-checks it;
- voices it, finds pictures and designs the shots;
- animates captions, keywords and diagrams, mixes music and sound effects;
- renders a 4K vertical video.

Every outside service (the LLM, the voice, pictures, music, the render machine) is **chosen in a config file**, so you can switch from Sarvam to Gemini, or from your laptop to cloud rendering, without touching code.

```
topics.txt ─▶ research ─▶ script ─▶ fact check ─▶ voice ─▶ images ─▶ shot plan ─▶ animation + mix ─▶ 4K render ─▶ export/
```

| | |
|---|---|
| **Output** | 2160×3840 MP4 (−14 LUFS), thumbnail JPG, `_YouTube.txt` (title, description, hashtags), `_Instagram.txt` |
| **Languages** | Hinglish (Devanagari voice, romanized captions) and English out of the box; other Sarvam languages via config |
| **LLMs** | Sarvam, Gemini, OpenAI, Claude, OpenRouter, Ollama, your own OpenAI-compatible API, or a signed-in CLI (Gemini CLI / Claude Code). Each role can have a **fallback list**. |
| **Voice** | Sarvam Bulbul (natural, pay per use) or Kokoro (free, offline) |
| **Pictures** | Free stock search (HeyGen account), your own folder, or AI-generated (Gemini) |
| **Rendering** | HyperFrames (HTML + GSAP → video) in a local headless Chrome, or HeyGen cloud |
| **Cost** | About ₹3–5 per topic with the defaults (Sarvam voice + script); everything else is free |
| **Runs on** | Windows 10/11 (one-click installer). The Python code itself is cross-platform. |

---

## Contents
1. [Quick start (Windows, one click)](#1-quick-start-windows-one-click)
2. [Manual setup, step by step](#2-manual-setup-step-by-step-windows-macos-linux)
3. [Make videos with the launchers](#3-make-videos-with-the-launchers)
4. [Make videos from the command line](#4-make-videos-from-the-command-line)
5. [Configuration in 2 minutes](#5-configuration-in-2-minutes)
6. [Which file does what](#6-which-file-does-what)
7. [Troubleshooting](#7-troubleshooting)
8. [More documentation](#8-more-documentation)

---

## 1. Quick start (Windows, one click)

You need **Windows 10/11** with **winget** (built into Windows 11; on Windows 10 install "App Installer" from the Microsoft Store), an internet connection and about 3 GB of disk space.

1. **Get the code**: either
   ```bash
   git clone https://github.com/Saurabh6235/ShortsStudio.git
   ```
   or download the ZIP from GitHub and unzip it.
2. **Double-click `INSTALL.cmd`.** It installs whatever is missing:
   - Python 3.12, Node.js and FFmpeg (through winget);
   - the Python packages;
   - the HyperFrames 0.9.5 renderer and its headless Chrome.

   Then it:
   - opens a browser so you can **sign in to a free HeyGen account** (used only for free stock pictures);
   - asks for your **Sarvam API key** (get one at https://dashboard.sarvam.ai; new accounts get free credit) and saves it in `.env`.
3. **Add the music kit.** The stock music and SFX are not in the repo; see [`channels/merit-mantra/kit/audio/README.md`](channels/merit-mantra/kit/audio/README.md) for the 8 files to drop in.
4. *(Optional, recommended)* Add a free **Gemini API key** (https://aistudio.google.com/apikey) as a new line in `.env`:
   ```
   GEMINI_API_KEY=your-key
   ```
5. **Double-click `CHECK_SETUP.cmd`.** Every line should show `[OK]`, ending with `All good.`
6. **Make your first video**: see [section 3](#3-make-videos-with-the-launchers).

> If a step shows `[MISSING]`, close the window, open a **new** one and run `INSTALL.cmd` again. Freshly installed tools only appear in new windows.

---

## 2. Manual setup, step by step (Windows, macOS, Linux)

Use this if you prefer to install things yourself or are not on Windows. Commands are shown for Windows. On macOS/Linux, use `python3.12` instead of `py -3.12`, and copy `.env` with `cp`.

| # | Step | Command / action |
|---|---|---|
| 1 | Install **Python 3.12**, **Node.js** (LTS or newer) and **FFmpeg** | Windows: `winget install -e --id Python.Python.3.12`, `winget install -e --id OpenJS.NodeJS.LTS`, `winget install -e --id Gyan.FFmpeg` (open a new terminal afterwards); macOS: `brew install python@3.12 node ffmpeg` |
| 2 | Clone the repo | `git clone https://github.com/Saurabh6235/ShortsStudio.git` then `cd ShortsStudio` |
| 3 | Python packages | `py -3.12 -m pip install -r setup/requirements.txt` |
| 4 | Renderer (pinned HyperFrames 0.9.5) | `npm install` |
| 5 | Render browser (headless Chrome) | `npx --yes hyperframes@0.9.5 browser ensure` |
| 6 | Free HeyGen sign-in (stock pictures) | `npx --yes hyperframes@0.9.5 auth login` |
| 7 | API keys | Copy `config/.env.example` to `.env` (in the project root) and fill in `SARVAM_API_KEY=` (plus `GEMINI_API_KEY=` if you have one) |
| 8 | Music kit | Put the 8 audio files in `channels/merit-mantra/kit/audio/` ([list](channels/merit-mantra/kit/audio/README.md)) |
| 9 | Check | `py -3.12 -m studio check`. It should end with `All good.` |

Verify the tools at any time:
```bash
py -3.12 --version
```
```bash
node --version
```
```bash
ffmpeg -version
```
```bash
npx --yes hyperframes@0.9.5 --version
```

---

## 3. Make videos with the launchers

**Step 1. Write your topic.** Copy `inbox/TEMPLATE.txt` to a new file in `inbox/` (for example `my-topics.txt`):

```
Topic: Why Does Ice Float on Water?
Hook: "Pathar paani mein doob jaata hai, lekin barf ka itna bada tukda kaise tair jaata hai?"
Hidden science: density, hydrogen bonds, open hexagonal ice crystal, water densest at 4 °C.
Interesting fact: Lakes freeze from the top, so fish survive winter underneath.
---
Topic: Why Do We See Lightning Before Thunder?
Hook: "Bijli pehle dikhti hai, aur garaj baad mein sunai deti hai - aisa kyun?"
```

Only `Topic:` is required. **Several videos from one file:** put a line with `---` between topics.

**Step 2. Double-click a launcher.**

| Launcher | What it does |
|---|---|
| `INSTALL.cmd` | One-time setup / repair (section 1) |
| `CHECK_SETUP.cmd` | Checks tools, sign-in, keys and which provider each role uses. Changes nothing. |
| **`MAKE_VIDEO.cmd`** | Newest `.txt` in `inbox/`: every topic in it becomes a finished video |
| `MAKE_ALL.cmd` | Every `.txt` in `inbox/`, one after another |
| `WRITE_SCRIPT.cmd` | Only the scripts + storyboards, so you can read/edit them before spending on voice and rendering |
| `BUILD_VIDEO.cmd <job>` | Run, finish or retry one video (job = folder name in `jobs/`). Add `--from <stage>` to redo from a stage. |
| `JOBS.cmd` | Every job and how far it got |

**Step 3. Collect the results** in `export/<date>_<Name>_<Language>/`. A topic takes about 10–15 minutes for two languages on a normal laptop. The topic file then moves to `inbox/done/`.

**Recommended flow for best quality:**
1. `WRITE_SCRIPT.cmd`.
2. Read `jobs/<job>/storyboard.md`; edit `jobs/<job>/script.json` if you want.
3. `BUILD_VIDEO.cmd <job>`. Your edits are detected: the shot plan is redone, and only changed lines are re-voiced.

---

## 4. Make videos from the command line

Everything the launchers do is available as `py -3.12 -m studio <command>`, run from the project folder. On macOS/Linux use `python3.12 -m studio`.

```bash
cd ShortsStudio
```

| Command | What it does |
|---|---|
| `py -3.12 -m studio check` | Shows the channel, languages, which provider each role uses, and missing keys |
| `py -3.12 -m studio make` | Newest topic file in `inbox/` → finished videos |
| `py -3.12 -m studio make inbox/my-topics.txt` | A specific topic file |
| `py -3.12 -m studio make --all` | Every topic file in `inbox/` |
| `py -3.12 -m studio write` | Scripts + storyboards only (stops before voice) |
| `py -3.12 -m studio build <job>` | Run or resume one job |
| `py -3.12 -m studio build <job> --from images` | Redo a job from a stage (later stages re-run too) |
| `py -3.12 -m studio build <job> --only render` | Run a single stage |
| `py -3.12 -m studio status <job>` | Each stage: done / skipped / failed, with notes |
| `py -3.12 -m studio list` | All jobs and their progress |
| `py -3.12 -m studio stages` | The pipeline stages in order, with their area |
| `py -3.12 -m studio providers` | Provider types you can name in the config |

**Options:**
- `--channel <name>` uses another channel profile from `channels/`.
- `--unattended` never waits for Enter (for scheduled or overnight runs).

On Windows, set these once per terminal for clean output:
```powershell
$env:PYTHONIOENCODING = "utf-8"; $env:CI = "1"
```

**Step-by-step example:**
```bash
py -3.12 -m studio check
```
```bash
py -3.12 -m studio write inbox/my-topics.txt
```
```bash
py -3.12 -m studio status why-does-ice-float-on-water
```
```bash
py -3.12 -m studio build why-does-ice-float-on-water
```

The pipeline stages, in order:

| Area | Stages |
|---|---|
| Content intelligence | `research` → `script` → `fact_check` → `storyboard` |
| Creative director | `visual_prompts` → `scene_draft` → `image_review` → `scene_plan` |
| Asset production | `voice` → `captions` → `music` → `images` |
| Composition engine | `plates` → `compose` → `mix` |
| Quality & delivery | `validate_draft`, `validate` → `render` → `export` → `metadata` → `storage` |

(Exact run order: research, script, fact_check, visual_prompts, scene_draft, storyboard, validate_draft, voice, captions, music, images, image_review, scene_plan, validate, plates, compose, mix, render, export, metadata, storage.)

**A job never repeats work:**
- finished stages are skipped;
- voice lines are cached by their text;
- pictures are cached by key.

If a run stops, fix the reason and run `build <job>` again.

---

## 5. Configuration in 2 minutes

All settings live in **`config/studio.json`**. Keys go in **`.env`**.

```jsonc
"use": {                                   // which provider plays each ROLE
  "script_llm":     ["gemini", "gemini_flash", "sarvam"],   // a list = fallback order
  "research_llm":   ["gemini_flash", "sarvam"],
  "fact_check_llm": ["gemini", "gemini_flash", "sarvam"],
  "director_llm":   ["gemini", "gemini_flash"],             // needs a big-output model
  "review_llm":     ["gemini_flash", "gemini"],             // needs a vision model
  "voice":  "sarvam",     // or "kokoro" (free, offline)
  "images": "stock",      // or "my_images" (your folder) or "gemini_ai" (AI pictures)
  "music":  "kit",
  "render": "local"       // or "cloud" (HeyGen servers, billed per render)
},
"pipeline": {                              // switch optional stages on/off
  "research": true,
  "script": "llm",            // or "manual" (you write script.json)
  "fact_check": "fix",        // "off" | "report" | "fix"
  "scene_planner": "ai",      // "rules" (free) | "ai" (AI-designed shots)
  "image_review": "ai"        // "manual" | "ai" | "off"
},
"providers": { "llm": {...}, "tts": {...}, "image": {...}, "music": {...}, "render": {...} }   // the connections
```

- **Add any LLM:** most providers speak the OpenAI-compatible API. Copy the `my_api` profile and set `base_url`, `model` and `key_env`.
- **Change the channel:** edit `channels/merit-mantra/channel.json` (languages, voices, CTA, music roles) and `prompts/script_brief.txt` (writing style). For another brand or niche, copy that folder and set `"channel"`.
- **After every change,** run `CHECK_SETUP.cmd` or `py -3.12 -m studio check`.

The full reference is in [GUIDE.md](GUIDE.md).

---

## 6. Which file does what

### Files you run or edit

| File | Purpose |
|---|---|
| `INSTALL.cmd` → `setup/install.ps1` | One-click installer and checker (`-CheckOnly` = `CHECK_SETUP.cmd`) |
| `MAKE_VIDEO.cmd`, `MAKE_ALL.cmd`, `WRITE_SCRIPT.cmd`, `BUILD_VIDEO.cmd`, `JOBS.cmd` | Launchers for `py -3.12 -m studio ...` |
| `config/studio.json` | **Roles → providers, pipeline switches, provider profiles, retry, export folder** |
| `config/.env.example` | Template for `.env` (your API keys; `.env` is git-ignored) |
| `channels/<name>/channel.json` | Channel profile: languages, voices, CTA ending, music roles, video format |
| `channels/<name>/prompts/script_brief.txt` | The writing style every script follows |
| `channels/<name>/kit/` | `brand/` (end card, logo) and `audio/` (music + SFX, add your own) |
| `inbox/TEMPLATE.txt` | Topic file format |
| `setup/requirements.txt`, `package.json` | Python packages; pinned HyperFrames renderer |

### The app (`studio/`)

| Path | Area | What it does |
|---|---|---|
| `__main__.py` | — | Command line (`make`, `write`, `build`, `status`, `list`, `check`, `providers`, `stages`) |
| `core/config.py` | core | Loads `studio.json`, the channel profile and `.env` |
| `core/models.py` | core | The `Job` object and the files each job folder holds |
| `core/registry.py` | core | Provider plug-in registry (`@register('kind', 'type')`) |
| `core/services.py` | core | Stages call services **by role**; handles fallback lists and retries |
| `core/exceptions.py` | core | Typed errors (retryable, config, provider, validation, user action) |
| `core/doctor.py`, `core/log.py` | core | `studio check`; console + `job.log` logging |
| `providers/llm/` | providers | `openai_compatible.py` (Sarvam, Gemini, OpenAI, OpenRouter, Ollama, own API), `anthropic.py`, `cli.py` |
| `providers/tts/` | providers | `sarvam.py`, `kokoro.py` |
| `providers/image/` | providers | `heygen_stock.py`, `local_folder.py`, `gemini_image.py` |
| `providers/music/`, `providers/render/` | providers | `kit_library.py`; `local.py`, `heygen_cloud.py` |
| `intelligence/` | content intelligence | `research.py`, `script_writer.py`, `fact_checker.py`, `storyboard.py` |
| `creative/` | creative director | `visual_prompts.py`, `scene_planner.py` (rules), `director.py` (AI), `visual_review.py` |
| `production/` | asset production | `voice_manager.py`, `caption_manager.py` (timing), `image_manager.py`, `music_manager.py`, `asset_manager.py` |
| `composition/` | composition engine | `plates.py` (backgrounds/cut-outs), `hyperframes.py` (layout + animation), `animations.py` (diagram library), `mixer.py` (FFmpeg mix) |
| `delivery/` | quality & delivery | `validator.py`, `render_manager.py`, `exporter.py` (4K + thumbnail), `metadata.py` (upload text), `storage.py` |
| `workflow/` | workflow | `pipeline.py` (stage list), `orchestrator.py` (run/skip/resume), `state.py`, `retry.py`, `jobs.py` (multi-topic batches) |

### Created while you work (git-ignored)

| Path | Contents |
|---|---|
| `.env` | Your API keys |
| `jobs/<slug>/` | One folder per topic: `input.txt`, `research.json`, `script.json`, `fact_check.json`, `storyboard.md`, `spec.json`, `audio/`, `media/`, `build_<lang>/`, `state.json`, `job.log` |
| `export/` | Finished videos, thumbnails, upload text |
| `my_images/` | Your own pictures for the `my_images` image provider |

---

## 7. Troubleshooting

| Message | Fix |
|---|---|
| `XYZ_API_KEY is missing` | Add the key to `.env` (template: `config/.env.example`) |
| `profile "x" is not defined` | A name in `"use"` must match a name under `"providers"` exactly |
| `studio.json is not valid JSON (line N…)` | A missing comma or quote near that line |
| `HTTP 401` / `403` / `404` / `429` | Wrong key / no access / wrong `base_url` or model name / quota (Gemini Pro needs billing; the Flash models work on the free tier) |
| `HTTP 503 high demand` | Temporary: retried automatically, then the next model in the list is used |
| `channel kit … is missing: bgm_001.wav …` | Add the music/SFX files ([list](channels/merit-mantra/kit/audio/README.md)) |
| `ACTION NEEDED: …` | The pipeline paused on purpose (manual script or review); do what it says, then build again |
| A picture is wrong | Change its phrase in `jobs/<job>/script.json` → `images`, delete its line in `media/assets.json`, then run `build <job> --from images` |
| Anything else | See `jobs/<job>/job.log`, fix the cause, then run `build <job>` again (finished stages are skipped) |

---

## 8. More documentation

- **[HOW_TO_RUN.md](HOW_TO_RUN.md):** a one-page run sheet.
- **[GUIDE.md](GUIDE.md):** every setting, switching providers, using Gemini (API key or Gemini CLI), channel profiles, costs.
- **[ARCHITECTURE.md](ARCHITECTURE.md):** how the code is organized, and how to add a provider, a stage or a channel.
- **[docs/COMPOSITION_SPEC.md](docs/COMPOSITION_SPEC.md):** the shot-plan format (for hand-tuning and the AI director).

---

**Credits and licences.** The rendering uses [HyperFrames](https://hyperframes.heygen.com) (HTML + GSAP → video), FFmpeg, Sarvam AI (voice) and optional LLM providers. The stock music and SFX are not included; use audio you are licensed to use, and keep its credits in `channels/<name>/kit/audio/SFX_CREDITS.md`. The Merit Mantra end card and logo in `channels/merit-mantra/kit/brand/` belong to the Merit Mantra channel. Replace them with your own brand when you create a new channel.
