# QUALITY & DELIVERY / export: upload master per language - upscaled to the channel's upload size (default 2160x3840),
# H.264 CRF 16, AAC 320k with a -1.5 dB peak limiter (keeps true peak under -1 dBTP after AAC), plus the thumbnail (frame 0.2 s).
import subprocess
from . import storage

def run(job):
    S = job.read('spec.json'); fmt = job.cfg.channel.get('format', {}); w, h = fmt.get('upload_size', [2160, 3840]); dirs = []
    for lang in job.langs:
        out = job.path(f'build_{lang}'); d = storage.export_dir(job, S['name'], lang)
        stem = f"{job.cfg.channel.get('file_prefix', 'Video')}_{S['name']}_{job.cfg.lang(lang).get('label', lang)}"
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(out / 'renders' / 'video.mp4'), '-i', str(out / 'assets' / 'audio' / 'final_mix.wav'),
                        '-map', '0:v', '-map', '1:a', '-vf', f'scale={w}:{h}:flags=lanczos', '-c:v', 'libx264', '-preset', 'slow', '-crf', '16',
                        '-pix_fmt', 'yuv420p', '-af', 'alimiter=limit=0.79:level=false:attack=1:release=50', '-c:a', 'aac', '-b:a', '320k',
                        '-ar', '48000', '-movflags', '+faststart', '-shortest', str(d / f'{stem}.mp4')], check=True)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '0.2', '-i', str(out / 'renders' / 'video.mp4'), '-frames:v', '1', '-q:v', '2',
                        str(d / f'{stem}_thumbnail.jpg')], check=True)
        job.data.setdefault('stems', {})[lang] = (str(d), stem); dirs.append(str(d)); job.log(f'  {lang} -> {d}')
    job.write('exports.json', {'stems': job.data['stems'], 'dirs': dirs})     # persisted, so metadata/storage work after a resume
    return f'{len(dirs)} video(s) exported'
