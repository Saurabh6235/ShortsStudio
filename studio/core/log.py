# One logger for console + the job's log file (jobs/<job>/job.log).
import datetime, sys

class Log:
    def __init__(self, path=None):
        self.f = open(path, 'a', encoding='utf-8') if path else None
    def __call__(self, *a):
        msg = ' '.join(str(x) for x in a)
        try: print(msg, flush=True)
        except UnicodeEncodeError: print(msg.encode(sys.stdout.encoding or 'utf-8', 'replace').decode(sys.stdout.encoding or 'utf-8'), flush=True)
        if self.f: self.f.write(f'{datetime.datetime.now():%H:%M:%S} {msg}\n'); self.f.flush()
    def section(self, title): self(f'\n=== {title} ===')
