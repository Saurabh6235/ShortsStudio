# Render providers: turn a HyperFrames project folder into <project>/renders/video.mp4.
# config/studio.json "use.render" names a profile in "providers.render".
#   local         headless Chrome on this laptop (free)
#   heygen_cloud  HeyGen's servers (billed per render by HeyGen) - for low-spec laptops
# More targets (AWS Lambda / Cloud Run via `hyperframes lambda|cloudrun`, your own render server) = one new file here.
import os, subprocess
HF = 'npx --yes hyperframes@0.9.5'

class RenderProvider:
    def __init__(self, profile, cfg): self.p, self.cfg, self.name = profile, cfg, profile['name']
    def render(self, project_dir): raise NotImplementedError
    def run(self, cmd, cwd):
        return subprocess.run(cmd, shell=True, cwd=cwd, env=dict(os.environ, CI='1', HEYGEN_NO_ANALYTICS='1'), stdin=subprocess.DEVNULL).returncode
