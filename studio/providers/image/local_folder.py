# Your own pictures: put <key>.jpg / .png in the folder named by "folder" (relative to the app root, or absolute).
# Keys without a picture are fetched with the "fallback" image profile (e.g. "stock"), if set.
import shutil
from pathlib import Path
from ...core.registry import register, get
from . import ImageProvider

@register('image', 'local_folder')
class LocalFolder(ImageProvider):
    def fetch(self, job, key, query):
        folder = Path(self.p.get('folder', 'my_images'))
        folder = folder if folder.is_absolute() else self.cfg.root / folder
        for ext in ('.png', '.jpg', '.jpeg', '.webp'):
            src = folder / f'{key}{ext}'
            if src.exists():
                dst = job.path('media', f'{key}{ext}'); dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy(src, dst)
                return f'media/{key}{ext}'
        fb = self.p.get('fallback')
        return get('image', fb, self.cfg).fetch(job, key, query) if fb else None
