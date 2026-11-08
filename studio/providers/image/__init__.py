# Image providers. config/studio.json "use.images" names a profile in "providers.image".
#   heygen_stock   free stock photo search (HyperFrames media-use, free HeyGen account)
#   local_folder   your own pictures: <folder>/<key>.jpg|png (falls back to another profile for missing keys)
#   gemini_image   AI-generated pictures with the Gemini API (needs GEMINI_API_KEY; billed by Google beyond the free tier)
class ImageProvider:
    def __init__(self, profile, cfg): self.p, self.cfg, self.name = profile, cfg, profile['name']
    def fetch(self, job, key, query):   # save the picture inside the job folder; return its path relative to the job (or None)
        raise NotImplementedError
