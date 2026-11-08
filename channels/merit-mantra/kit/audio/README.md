# Channel audio kit (not included in the repository)

Put these files in this folder. The `kit_library` music provider checks they exist before mixing:

| File | Role |
|---|---|
| `bgm_001.wav` | music bed: tension (hook) |
| `bgm_003.wav` | music bed: build (mechanism) |
| `bgm_002.wav` | music bed: uplift (payoff, ending) |
| `sfx_001.mp3` | whoosh (section dissolves) |
| `sfx_002.mp3` | pop (keyword overlays) |
| `sfx_003.mp3` | impact (thumbnail card) |
| `sfx_004.mp3` | boom (twist / payoff) |
| `sfx_005.mp3` | riser (into the payoff) |

The roles of the three music beds are set in `channel.json` under `"music"`.

**Where to get them:** any royalty-free source you are licensed to use, for example:
- the HyperFrames free catalog: `npx hyperframes media-use resolve --type bgm --intent "dark cinematic tension" --project .`, and `--type sfx` for the effects;
- freesound.org (check each sound's licence).

Note credits that a licence requires in `SFX_CREDITS.md`. The audio is not in the repository because stock licences often do not allow redistribution.
