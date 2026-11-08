"""ShortsStudio - modular faceless short-video factory (YouTube Shorts / Instagram Reels).

Layers (each folder has one responsibility; see ARCHITECTURE.md):
  core/          config, data models, exceptions, provider registry, logging
  providers/     outside services behind small interfaces: llm, tts, image, music, render
  intelligence/  CONTENT INTELLIGENCE  research, script writing, fact checking, storyboard
  creative/      CREATIVE DIRECTOR     visual prompts, scene planning (rules or AI), visual review
  production/    ASSET PRODUCTION      voice, captions/timing, images, music
  composition/   COMPOSITION ENGINE    plates, HyperFrames layout + animation, audio mix (FFmpeg)
  delivery/      QUALITY & DELIVERY    validation, rendering, export, metadata, storage
  workflow/      pipeline stages, job state, retries, job manager (batches), orchestrator
"""
__version__ = '2.0.0'
