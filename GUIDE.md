# ShortsStudio: guide

Turn a text file of topics into finished **faceless short videos**: YouTube Shorts and Instagram Reels, in Hinglish, English or other languages. Each video comes with a thumbnail and ready-to-paste upload text.
- **Modular:** every service (LLM, voice, images, music, render machine) is chosen in one config file.
- **Not tied to one channel:** the channel is a swappable profile.
- **Runs on any Windows laptop**, with an optional cloud render for weak machines.

How it is built and how to extend it: **ARCHITECTURE.md**.

---

## 1. Install (one time)

1. Copy the `ShortsStudio` folder anywhere on the laptop.
2. Double-click **`INSTALL.cmd`**. It installs Python 3.12, Node.js, FFmpeg, the Python packages, the pinned HyperFrames 0.9.5 renderer and its browser. Then it signs you in to a **free** HeyGen account (used for stock images) and asks for your **Sarvam** API key. It finishes with the configuration check.
3. **`CHECK_SETUP.cmd`** at any time shows what is installed and which provider each role uses. It changes nothing.

`.env` holds your keys. Template: `config\.env.example`. Never share `.env`.

---

## 2. Make videos

1. Copy `inbox\TEMPLATE.txt` to a new `.txt` in `inbox` and fill it in. **Several videos from one file:** put a line with `---` between topics.
   ```
   Topic: Why Does Ice Float on Water?
   Hook: "Pathar paani mein doob jaata hai, lekin barf ka itna bada tukda kaise tair jaata hai?"
   Hidden science: density, hydrogen bonds, open hexagonal ice crystal, water densest at 4 °C.
   Interesting fact: Lakes freeze from the top, so fish survive winter underneath.
   ---
   Topic: Why Do We See Lightning Before Thunder?
   Hook: "Bijli pehle dikhti hai, aur garaj baad mein sunai deti hai - aisa kyun?"
   ```
2. Pick a launcher:

| Launcher | What it does |
|---|---|
| **`MAKE_VIDEO.cmd`** | Newest `.txt` in `inbox`: every topic in it becomes a finished video |
| **`MAKE_ALL.cmd`** | Every `.txt` in `inbox`, one after another |
| **`WRITE_SCRIPT.cmd`** | Only the scripts and storyboards, to read and edit before paying for voice and rendering |
| **`BUILD_VIDEO.cmd <job>`** | Run or resume one job (the folder name in `jobs\`). Add `--from <stage>` to redo from a stage. |
| **`JOBS.cmd`** | Every job and how far it got |

3. Results go to `export\<date>_<Name>_<Language>\`:
   - The 4K video (2160×3840, −14 LUFS).
   - `_thumbnail.jpg`.
   - `_YouTube.txt`: title, description, hashtags.
   - `_Instagram.txt`: the caption.

**Recommended flow for quality:**
1. `WRITE_SCRIPT.cmd`.
2. Read `jobs\<job>\storyboard.md`; edit `jobs\<job>\script.json` if needed.
3. `BUILD_VIDEO.cmd <job>`. Your edits are detected: the plan is redone, and only changed lines are re-voiced.

**If something fails:** fix what the message says, then run `BUILD_VIDEO.cmd <job>` again. Finished stages are skipped. Details are in `jobs\<job>\job.log`, and `py -3.12 -m studio status <job>` shows each stage.

---

## 3. What runs where (and the cost)

| Area | Stage | Default provider | Cost |
|---|---|---|---|
| Content intelligence | research *(off)* | `gemini` | free tier / pay per use |
| | script | `sarvam` chat | about ₹0.5–1 per script |
| | fact check *(off)* | `gemini` | free tier / pay per use |
| | storyboard | built in | free |
| Creative director | visual prompts, scene plan (rules) | built in | free |
| | AI director *(off)*, AI image review *(off)* | `gemini` | free tier / pay per use |
| Asset production | voice | `sarvam` (Bulbul) | about ₹1–2 per language |
| | images | `stock` (free HeyGen search) | free |
| | music + SFX | `kit` (channel kit) | free |
| Composition engine | plates, layout, animation, mix | built in (HyperFrames, FFmpeg) | free |
| Quality & delivery | validate, export, metadata, storage | built in | free |
| | render | `local` (this laptop) | free; `cloud` is billed by HeyGen |

The default setup costs about **₹3–5 per topic** (two languages).

---

## 4. Configuration: everything is in `config\studio.json`

```
"use":      which provider plays each ROLE      ->  script_llm, research_llm, fact_check_llm, director_llm, review_llm,
                                                     voice, images, music, render
"pipeline": switch optional stages on/off       ->  research, script (llm|manual), fact_check (off|report|fix),
                                                     scene_planner (rules|ai), image_review (manual|ai|off)
"providers": the connections you can choose from, by kind: llm, tts, image, music, render
"retry":    attempts and pause for temporary failures
"export":   output folder, and an optional second folder to copy into (e.g. a Google Drive synced folder)
```

**Every switch is a one-word change.** Edit in Notepad, keep the quotes and commas, then run `CHECK_SETUP.cmd` to verify.

| I want to… | Change |
|---|---|
| Write scripts with Gemini | `"script_llm": "gemini"` (plus `GEMINI_API_KEY` in `.env`) |
| Use a cheaper/faster Gemini | `"script_llm": "gemini_flash"` |
| Research before writing | `"research": true` |
| Fact-check and auto-fix the script | `"fact_check": "fix"` (`"report"` only lists the problems) |
| AI-designed shots (Claude-style videos) | `"scene_planner": "ai"` with `"director_llm": "gemini"` |
| Let AI reject bad pictures | `"image_review": "ai"` with `"review_llm": "gemini"` |
| Free offline voice | `"voice": "kokoro"` |
| Use my own pictures | `"images": "my_images"`, then put `<key>.jpg` in the `my_images` folder. Missing ones fall back to stock. |
| AI-generated pictures | `"images": "gemini_ai"` (Gemini API key; image output may be billed) |
| Render in the cloud (weak laptop) | `"render": "cloud"` (billed per render by HeyGen) |
| Write scripts myself (free) | `"script": "manual"`, then create `jobs\<job>\script.json` from `examples\radar-rain.script.json` |
| Another channel / niche | `"channel": "<folder in channels>"` (section 6) |

### Several LLMs for one role (fallback lists)

Any `*_llm` role can name **one** profile or a **list**, tried in order:

```
"script_llm":     ["gemini", "sarvam"],          Gemini writes; if it fails (no key, limit reached, error) Sarvam writes instead
"research_llm":   ["gemini_flash", "sarvam"],
"fact_check_llm": ["gemini", "sarvam"],
"director_llm":   ["gemini", "gemini_flash"],    only models with max_output_tokens >= 12000 are used; otherwise the rules plan
"review_llm":     ["gemini_flash", "gemini"],    only models with "vision": true are used; otherwise no AI review
```

- **Retries first:** each model is retried on temporary errors before the next one takes over.
- **One model per stage:** once a model answers, it does the rest of that stage. A script is never half Gemini, half Sarvam: if the first model fails partway, the script stage starts again with the next model.
- **Check the list:** `CHECK_SETUP.cmd` shows every entry with OK or the reason it is skipped (for example "missing GEMINI_API_KEY").
- **Graceful when no entry works:** the director and the image review never stop a video. The director keeps the rules plan; the review is skipped.

### Your own API / any other LLM

Most providers and self-hosted servers speak the OpenAI-compatible API. Fill in `my_api` (or copy it under a new name):

```
"my_api": {"type": "openai_compatible", "base_url": "https://my-server.example.com/v1", "model": "my-model",
           "key_env": "MY_LLM_KEY", "max_output_tokens": 8000, "vision": false}
```

Then use `"script_llm": "my_api"` (or any other role).
- `max_output_tokens` ≥ 12000 enables one-pass script writing and the AI director.
- Optional extras: `"temperature"`, `"timeout"`, `"json_mode": false` (for servers without JSON mode), `"headers"`.

Claude uses `"type": "anthropic"`. A local model: install Ollama, `ollama pull qwen2.5:7b`, then use `"ollama"`.

---

## 5. Using your Gemini subscription

Your **Gemini Pro subscription** (Gemini app / Google AI Pro) is a consumer plan and isn't an API key. Two ways to use Gemini here:

**A) Gemini API key (recommended).**
1. Go to https://aistudio.google.com/apikey and create a key. There's a **free tier** with rate limits, enough for a few videos a day; beyond that, enable billing in Google AI Studio.
2. Add `GEMINI_API_KEY=your-key` to `.env`.
3. Point the roles you want at it:
   ```
   "use": {"script_llm": "gemini", "research_llm": "gemini", "fact_check_llm": "gemini", "director_llm": "gemini", "review_llm": "gemini", ...}
   "pipeline": {"research": true, "script": "llm", "fact_check": "fix", "scene_planner": "ai", "image_review": "ai"}
   ```
   This is the strongest setup: research, a better script, fact-checking, AI-designed shots and AI picture review. **Sarvam stays the voice**, because it's best for Hindi.

**B) Gemini CLI with your subscription login (no API key).**
1. Install it: `npm install -g @google/gemini-cli`.
2. Run `gemini` once and sign in with your Google account.
3. Use `"script_llm": "gemini_cli"` (or any LLM role except image review: the CLI connector can't send images).

It uses your subscription's quota through Google's own command-line tool. It's slower than the API, and limits depend on your plan.

> **Which Gemini models work on the free tier** (checked 2026-11-08 with your key):
> - `gemini` = `gemini-3.5-flash` and `gemini_flash` = `gemini-3.5-flash-lite` work, including image understanding.
> - `gemini_pro` = `gemini-pro-latest` returns `HTTP 429 quota` until billing is turned on in Google AI Studio.
> - `gemini-2.5-pro` / `gemini-2.5-flash` are closed to new users (`HTTP 404`).
>
> Google retires model names over time. If you see `HTTP 404 ... model`, put a current name from Google AI Studio into the profile's `"model"`. The `*-latest` names (`gemini-pro-latest`, `gemini-flash-latest`) always point at the newest model.
> `HTTP 503 high demand` is temporary: the app waits, retries, then moves to the next model in the role's list.

---

## 6. Channel profiles (any niche, any brand)

`channels\<name>\` holds everything that makes a channel *that* channel:
- `channel.json`: display name, hashtag, file prefix, **languages**, **voices** per provider and language, the **CTA** ending, music roles, video format.
- `prompts\script_brief.txt`: the writing style (tone, structure, audience, rules). This matters most for script quality.
- `kit\`: `audio\` (3 music beds, 5 SFX) and `brand\` (end card video, logo seal).

**New channel:**
1. Copy `channels\merit-mantra` to `channels\my-channel`.
2. Edit the three items above.
3. Set `"channel": "my-channel"` in `config\studio.json`, or run `py -3.12 -m studio make --channel my-channel`.

**Languages:** each entry is `{"code", "label", "voice_text", "captions"}`.
- Hinglish: `"voice_text": "devanagari"`, `"captions": "roman"`.
- English: `"latin"`.
- Other Indian languages that Sarvam speaks (Tamil `ta-IN`, Bengali `bn-IN`, Marathi `mr-IN`…): `"voice_text": "native"`, plus a voice in `"voices"`.

One language only means half the cost and half the render time.

---

## 7. Folder map

```
ShortsStudio\
  INSTALL.cmd  CHECK_SETUP.cmd  MAKE_VIDEO.cmd  MAKE_ALL.cmd  WRITE_SCRIPT.cmd  BUILD_VIDEO.cmd  JOBS.cmd
  GUIDE.md (this)  ARCHITECTURE.md (how it is built / extended)  .env (your keys)
  config\studio.json         roles -> providers, pipeline switches, retry, export
  channels\<name>\           channel profile: channel.json, prompts\, kit\
  inbox\                     topic .txt files (TEMPLATE.txt); done\ = finished
  jobs\<slug>\               one folder per topic: input.txt, research.json, script.json, fact_check.json, storyboard.md,
                             spec.json, audio\, media\, build_<lang>\, state.json, job.log
  export\                    finished videos + thumbnails + upload text
  my_images\                 your own pictures for the "my_images" image provider
  studio\                    the app (core, providers, intelligence, creative, production, composition, delivery, workflow)
  docs\COMPOSITION_SPEC.md   spec format the scene planners write (for hand-tuning and the AI director)
  examples\                  a hand-written script.json and a full spec.json
  setup\                     install.ps1, requirements.txt
```

---

## 8. Command line (optional)

```
py -3.12 -m studio make [file.txt] [--all] [--channel X] [--unattended]
py -3.12 -m studio write [file.txt]
py -3.12 -m studio build <job> [--from STAGE] [--only STAGE]
py -3.12 -m studio status <job>     |  list  |  check  |  providers  |  stages
```

Stages, in order: research, script, fact_check, visual_prompts, scene_draft, storyboard, validate_draft, voice, captions, music, images, image_review, scene_plan, validate, plates, compose, mix, render, export, metadata, storage.

---

## 9. Troubleshooting

| Message | Fix |
|---|---|
| `XYZ_API_KEY is missing` | Add the key line to `.env` (template: `config\.env.example`). |
| `profile "x" is not defined` | The name in `"use"` must match a name under `"providers"` exactly. |
| `studio.json is not valid JSON (line N…)` | A missing comma or quote near that line. |
| `HTTP 401` / `403` / `404` | Wrong key / no access or credits / wrong `base_url` or model name. |
| `empty reply … raise max_output_tokens` | The model "thinks" too long. Pick a non-reasoning model (Sarvam: use `sarvam-105b-conversations`, not `sarvam-105b`). |
| Rate limit / `429` | Retried automatically. If it keeps failing, wait and run `BUILD_VIDEO.cmd <job>` again. |
| `ACTION NEEDED: …` | The pipeline paused on purpose (manual script or review). Do what it says, then build again. |
| `AI director … kept the rules plan` | The model's plan was invalid three times, or its output limit is too small. The video is still made. |
| A picture is wrong | Change its phrase in `script.json` → `images`, delete its line in `media\assets.json`, then build again. Or turn on `"image_review": "ai"`. |

Every run is safe to repeat: finished stages are skipped, voices and images are reused.
