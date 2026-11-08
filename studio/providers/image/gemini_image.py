# AI-generated pictures with the Gemini API (generateContent with an image-output model, e.g. "gemini-2.5-flash-image").
# Profile keys: model, key_env (GEMINI_API_KEY), [style] - a style sentence added to every prompt.
# Uses your Gemini API key (Google AI Studio). Image output may be billed by Google beyond the free tier - check your quota.
import base64, os
import httpx
from ...core.registry import register
from ...core.exceptions import MissingKeyError, ProviderError, RetryableError
from . import ImageProvider

@register('image', 'gemini_image')
class GeminiImage(ImageProvider):
    def fetch(self, job, key, query):
        env = self.p.get('key_env', 'GEMINI_API_KEY'); api_key = os.environ.get(env, '')
        if not api_key: raise MissingKeyError(f'{env} is missing from .env (image profile "{self.name}")')
        prompt = f'{query}. ' + self.p.get('style', 'Photorealistic, cinematic lighting, vertical 9:16 composition, no text, no letters, no watermark.')
        url = f'https://generativelanguage.googleapis.com/v1beta/models/{self.p.get("model", "gemini-2.5-flash-image")}:generateContent'
        try:
            r = httpx.post(url, headers={'x-goog-api-key': api_key}, timeout=180,
                           json={'contents': [{'parts': [{'text': prompt}]}], 'generationConfig': {'responseModalities': ['IMAGE']}})
        except httpx.HTTPError as e:
            raise RetryableError(f'Gemini image: network error {e}')
        if r.status_code == 429 or r.status_code >= 500: raise RetryableError(f'Gemini image: HTTP {r.status_code}')
        if r.status_code >= 400: raise ProviderError(f'Gemini image: HTTP {r.status_code} {r.text[:300]}')
        for part in (r.json().get('candidates') or [{}])[0].get('content', {}).get('parts', []):
            data = part.get('inlineData') or part.get('inline_data')
            if data:
                dst = job.path('media', f'{key}.png'); dst.parent.mkdir(parents=True, exist_ok=True); dst.write_bytes(base64.b64decode(data['data']))
                return f'media/{key}.png'
        return None
