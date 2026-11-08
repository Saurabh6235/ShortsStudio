# A command-line AI assistant you are already signed in to - uses your subscription instead of an API key.
#   Gemini CLI (Google AI Pro / Gemini subscription):  "command": ["gemini", "-p", "{prompt}"]
#   Claude Code (Claude subscription):                 "command": ["claude", "-p", "{prompt}"]
# The full prompt (system + task) replaces {prompt}; with "stdin": true it is piped in instead (for very long prompts).
# Profile keys: command (list), [stdin, timeout, max_output_tokens, vision=false]
import shutil, subprocess
from ...core.registry import register
from ...core.exceptions import ProviderError, RetryableError
from . import LLMProvider

@register('llm', 'cli')
class CLI(LLMProvider):
    def _complete(self, system, user, image, max_tokens, json_mode):
        prompt = f'{system}\n\n{user}' + ('\n\nReply with JSON only - no explanation, no code fences.' if json_mode else '')
        cmd = list(self.p.get('command') or [])
        exe = shutil.which(cmd[0]) if cmd else None
        if not exe: raise ProviderError(f'LLM profile "{self.name}": command {cmd[:1]} not found - install it and sign in once')
        stdin = self.p.get('stdin', False)
        args = [exe] + [a.replace('{prompt}', '' if stdin else prompt) for a in cmd[1:]]
        try:
            r = subprocess.run(args, input=prompt if stdin else None, capture_output=True, text=True, encoding='utf-8', errors='replace',
                               timeout=self.p.get('timeout', 900))
        except subprocess.TimeoutExpired:
            raise RetryableError(f'{self.name}: timed out')
        if r.returncode: raise RetryableError(f'{self.name}: exit {r.returncode} {r.stderr[-300:]}')
        return r.stdout
