# LLM providers. A profile in config/studio.json "providers.llm" picks the type:
#   openai_compatible  Sarvam, Gemini (API key), OpenAI, OpenRouter, Groq, DeepSeek, Ollama, vLLM, LM Studio, your own server
#   anthropic          Claude API
#   cli                a command-line assistant you are signed in to (Gemini CLI with your Google subscription, Claude Code...)
import json, os, re
from ...core.exceptions import MissingKeyError, ProviderError, RetryableError

class LLMProvider:
    def __init__(self, profile, cfg):
        self.p, self.cfg, self.name = profile, cfg, profile['name']
        self.model = profile.get('model', '')
        self.max_output = int(profile.get('max_output_tokens', 4096))
        self.vision = bool(profile.get('vision', False))

    def key(self):
        env = self.p.get('key_env') or ''
        if not env: return ''
        k = os.environ.get(env, '')
        if not k: raise MissingKeyError(f'{env} is missing: add the line {env}=<your key> to .env (LLM profile "{self.name}")')
        return k

    @property
    def big(self): return self.max_output >= 12000          # can write a whole script / shot plan in one reply

    def _complete(self, system, user, image, max_tokens, json_mode):   # implemented by each provider -> str
        raise NotImplementedError

    def chat(self, system, user, image=None, json_mode=True, max_tokens=None):
        """One request. Returns parsed JSON (json_mode) or text. Raises RetryableError / ProviderError."""
        if image and not self.vision: raise ProviderError(f'LLM profile "{self.name}" has "vision": false - it cannot look at images')
        txt = self._complete(system, user, image, min(max_tokens or self.max_output, self.max_output), json_mode)
        if not (txt or '').strip(): raise RetryableError(f'{self.name}: empty reply - raise max_output_tokens or use a non-reasoning model')
        if not json_mode: return txt
        t = re.sub(r'^```(?:json)?\s*|\s*```$', '', txt.strip())
        try: return json.loads(t[t.find('{'):t.rfind('}') + 1])
        except ValueError: raise RetryableError(f'{self.name}: reply was not valid JSON')

def http_error(name, r):
    """Map an HTTP failure to the right exception: 429/5xx are temporary, everything else needs a config fix."""
    msg = f'{name}: HTTP {r.status_code} {r.text[:300]}'
    if r.status_code == 429 or r.status_code >= 500: raise RetryableError(msg)
    hint = {401: ' (wrong API key?)', 403: ' (no access / credits?)', 402: ' (credits exhausted)', 404: ' (wrong base_url or model name?)'}.get(r.status_code, '')
    raise ProviderError(msg + hint)
