# ShortsStudio: how to run (quick sheet)

Everything happens by **double-clicking a `.cmd` file** in the `ShortsStudio` folder. You can also type it in PowerShell from inside the folder, for example `.\MAKE_VIDEO.cmd`.

---

## A. First-time setup (once per laptop)

| Step | Do this | You should see |
|---|---|---|
| 1 | Copy the `ShortsStudio` folder to the laptop (any drive). | |
| 2 | Double-click **`INSTALL.cmd`** | Steps 1–8, each `[OK]`, then `All good.` |
| 3 | When it asks, sign in to **HeyGen** (free account, for stock pictures) in the browser that opens. | `[OK] signed in as ...` |
| 4 | When it asks, paste your **Sarvam API key** (from dashboard.sarvam.ai). | `[OK] key saved in .env` |
| 5 | *(Optional, recommended)* Open `.env` in Notepad and add a second line: `GEMINI_API_KEY=your-key` (free key from aistudio.google.com/apikey). | |
| 6 | Double-click **`CHECK_SETUP.cmd`** | Every role `OK`, then `All good.` |

If a step says `[MISSING]`, close the window, open a **new** one and run `INSTALL.cmd` again.

---

## B. Make videos (every time)

| Step | Do this |
|---|---|
| 1 | Open the `inbox` folder. Copy `TEMPLATE.txt`, rename the copy (e.g. `my-topics.txt`) and fill in `Topic:`, `Hook:`, `Hidden science:`, `Interesting fact:`. **More videos in one file:** put a line with `---` between topics. |
| 2 | Double-click **`MAKE_VIDEO.cmd`**. It uses the **newest** `.txt` in `inbox`. |
| 3 | Wait. Each topic takes about 10–15 minutes (two languages). The window shows each stage as it runs. |
| 4 | Open the `export` folder. There's one folder per video and language, each with the **.mp4**, **_thumbnail.jpg**, **_YouTube.txt** and **_Instagram.txt**. |

The finished topic file moves to `inbox\done`.

---

## C. Which file to run when

| I want to… | Run |
|---|---|
| Install / repair the tools | `INSTALL.cmd` |
| See if everything is set up (changes nothing) | `CHECK_SETUP.cmd` |
| Make videos from the newest topic file | `MAKE_VIDEO.cmd` |
| Make videos from **all** topic files in `inbox` | `MAKE_ALL.cmd` |
| Only write the script first, to read and edit it | `WRITE_SCRIPT.cmd`, then read `jobs\<job>\storyboard.md` (edit `jobs\<job>\script.json` if needed), then `BUILD_VIDEO.cmd <job>` |
| Finish or retry a video that stopped | `BUILD_VIDEO.cmd <job>` (job = the folder name in `jobs\`) |
| Redo a video from a certain step | `BUILD_VIDEO.cmd <job> --from voice` (or `images`, `scene_plan`, `render`…) |
| See all videos and how far each got | `JOBS.cmd` |

**Stopped with an error?** Read the last lines, fix what it says (usually a key in `.env` or a setting), then run `BUILD_VIDEO.cmd <job>`. Finished steps are skipped, and nothing is paid for twice. The full log is in `jobs\<job>\job.log`.

---

## D. Settings you will actually change (`config\studio.json`, in Notepad)

| Setting | Values |
|---|---|
| `"script_llm"` | `["gemini", "gemini_flash", "sarvam"]`: tried in order; the next takes over if one fails |
| `"voice"` | `"sarvam"` (natural) or `"kokoro"` (free, offline) |
| `"images"` | `"stock"` (free stock), `"my_images"` (your pictures in the `my_images` folder), `"gemini_ai"` (AI pictures) |
| `"render"` | `"local"` (this laptop) or `"cloud"` (HeyGen servers, billed per render) |
| `"research"` | `true` / `false` |
| `"fact_check"` | `"off"` / `"report"` / `"fix"` |
| `"scene_planner"` | `"rules"` / `"ai"` (AI-designed shots) |
| `"image_review"` | `"manual"` / `"ai"` / `"off"` |

After any change, run **`CHECK_SETUP.cmd`**. Keep the quotes and commas exactly as they are.

**Gemini note:**
- The free tier covers the Flash models: `gemini` = `gemini-3.5-flash` and `gemini_flash` = `gemini-3.5-flash-lite`.
- `gemini_pro` (`gemini-pro-latest`) needs billing turned on in Google AI Studio; without it you get `HTTP 429 quota`.
- Google sometimes answers `503 high demand`. The app waits, retries, then uses the next model in the list.

---

## E. Language and channel

- **Languages:** `channels\merit-mantra\channel.json` → `"languages"`. Remove the English entry for Hinglish-only videos, which halves the cost and time.
- **Another channel / niche:** copy `channels\merit-mantra` to a new folder, edit it, then set `"channel"` in `config\studio.json`.

More detail: **GUIDE.md** (everything) and **ARCHITECTURE.md** (how the code is organized).
