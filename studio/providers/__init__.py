# Outside services, each behind a small interface (see the base class in each sub-package's __init__.py):
#   llm/     chat models          LLMProvider.chat(system, user, image=None, json_mode=True)
#   tts/     voices               TTSProvider.speak(text, out_wav, voice_cfg)
#   image/   pictures             ImageProvider.fetch(job, key, query) -> file path relative to the job
#   music/   music + SFX library  MusicProvider.prepare(job) -> folder with the house tracks
#   render/  frame rendering      RenderProvider.render(project_dir) -> project_dir/renders/video.mp4
# A new provider = one file with a class decorated @register('<kind>', '<type>'); then name it in config/studio.json.
