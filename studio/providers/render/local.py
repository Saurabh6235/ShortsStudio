# Headless Chrome on this laptop via `hyperframes render` (free). Profile keys: [quality: draft|standard|delivery]
from pathlib import Path
from ...core.registry import register
from ...core.exceptions import ProviderError
from . import RenderProvider, HF

@register('render', 'local')
class Local(RenderProvider):
    def render(self, project_dir):
        code = self.run(f'{HF} render --quality {self.p.get("quality", "delivery")} -o renders/video.mp4', project_dir)
        out = Path(project_dir) / 'renders' / 'video.mp4'
        if code or not out.exists(): raise ProviderError(f'local render failed (exit {code})')
        return out
