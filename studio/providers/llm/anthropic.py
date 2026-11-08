# Claude API: POST https://api.anthropic.com/v1/messages. Profile keys: model, key_env, max_output_tokens, vision, [base_url, timeout]
import base64
from pathlib import Path
import httpx
from ...core.registry import register
from ...core.exceptions import RetryableError
from . import LLMProvider, http_error

@register('llm', 'anthropic')
class Anthropic(LLMProvider):
    def _complete(self, system, user, image, max_tokens, json_mode):
        content = [{'type': 'text', 'text': user + ('\nReply with JSON only.' if json_mode else '')}]
        if image:
            content.insert(0, {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/jpeg',
                                                            'data': base64.b64encode(Path(image).read_bytes()).decode()}})
        try:
            r = httpx.post(self.p.get('base_url', 'https://api.anthropic.com/v1').rstrip('/') + '/messages', timeout=self.p.get('timeout', 600),
                           headers={'x-api-key': self.key(), 'anthropic-version': '2023-06-01', 'content-type': 'application/json'},
                           json={'model': self.model, 'max_tokens': max_tokens, 'system': system, 'messages': [{'role': 'user', 'content': content}]})
        except httpx.HTTPError as e:
            raise RetryableError(f'{self.name}: network error {e}')
        if r.status_code >= 400: http_error(self.name, r)
        return ''.join(b.get('text', '') for b in r.json().get('content', []))
