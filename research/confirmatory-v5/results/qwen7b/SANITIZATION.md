# Metadata sanitization

The `model` field in `run_meta.json` was changed from an absolute local cache
path to the public model identifier plus mirror description. No result,
prompt, seed, package version, dtype, hash, timestamp, or analysis field was
changed.
