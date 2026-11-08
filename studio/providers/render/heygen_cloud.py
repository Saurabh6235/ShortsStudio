# HyperFrames cloud render on HeyGen's servers. Billed per render by HeyGen (4k = 1.5x). Profile keys: quality, resolution.
# Set the environment variable STUDIO_CLOUD_DRY_RUN=1 to build and check the upload without sending it (no charge).
import os
from pathlib import Path
from ...core.registry import register
from ...core.exceptions import ProviderError
from . import RenderProvider, HF

@register('render', 'heygen_cloud')
class HeyGenCloud(RenderProvider):
    def render(self, project_dir):
        dry = ' --dry-run' if os.environ.get('STUDIO_CLOUD_DRY_RUN') else ''
        code = self.run(f'{HF} cloud render . --aspect-ratio 9:16 --quality {self.p.get("quality", "high")} '
                        f'--resolution {self.p.get("resolution", "1080p")} --wait -o renders/video.mp4{dry}', project_dir)
        if dry: raise ProviderError(f'cloud dry run finished with exit {code} (nothing uploaded) - unset STUDIO_CLOUD_DRY_RUN to render for real')
        out = Path(project_dir) / 'renders' / 'video.mp4'
        if code or not out.exists(): raise ProviderError(f'cloud render failed (exit {code})')
        return out
