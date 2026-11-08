# Free stock images through `hyperframes media-use resolve --type image` (needs the free HeyGen sign-in).
import os, re, subprocess
from ...core.registry import register
from ...core.exceptions import RetryableError
from . import ImageProvider

@register('image', 'heygen_stock')
class HeyGenStock(ImageProvider):
    def fetch(self, job, key, query):
        r = subprocess.run(f'npx --yes hyperframes@0.9.5 media-use resolve --type image --intent "{query}" --project .', shell=True,
                           cwd=job.dir, capture_output=True, text=True, encoding='utf-8', errors='replace',
                           env=dict(os.environ, HEYGEN_NO_ANALYTICS='1'))
        m = re.search(r'resolved \S+ \S+ (\S+) \(', r.stdout)
        if m: return m.group(1).replace('\\', '/')
        out = (r.stdout + r.stderr).lower()
        if 'rate' in out or 'timeout' in out: raise RetryableError(f'stock search busy for "{query}"')
        return None
