# Any provider that speaks the OpenAI chat API: POST <base_url>/chat/completions.
# Profile keys: base_url, model, key_env, max_output_tokens, vision, [temperature, timeout, json_mode, headers]
import base64
from pathlib import Path
import httpx
from ...core.registry import register
from ...core.exceptions import RetryableError
from . import LLMProvider, http_error

@register('llm', 'openai_compatible')
class OpenAICompatible(LLMProvider):
    def _complete(self, system, user, image, max_tokens, json_mode):
        content = user if not image else [
            {'type': 'text', 'text': user},
            {'type': 'image_url', 'image_url': {'url': 'data:image/jpeg;base64,' + base64.b64encode(Path(image).read_bytes()).decode()}}]
        body = {'model': self.model, 'max_tokens': max_tokens, 'temperature': self.p.get('temperature', 0.5),
                'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': content}]}
        if json_mode and self.p.get('json_mode', True): body['response_format'] = {'type': 'json_object'}
        headers = {'Content-Type': 'application/json', **self.p.get('headers', {})}
        if self.key(): headers['Authorization'] = f'Bearer {self.key()}'
        url = self.p['base_url'].rstrip('/') + '/chat/completions'
        try:
            r = httpx.post(url, json=body, headers=headers, timeout=self.p.get('timeout', 600))
            if r.status_code == 400 and 'response_format' in r.text and 'response_format' in body:   # no JSON mode on this server
                body.pop('response_format'); r = httpx.post(url, json=body, headers=headers, timeout=self.p.get('timeout', 600))
        except httpx.HTTPError as e:
            raise RetryableError(f'{self.name}: network error {e}')
        if r.status_code >= 400: http_error(self.name, r)
        return r.json()['choices'][0]['message'].get('content') or ''
