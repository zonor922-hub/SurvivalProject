"""Run beside SHA256_MANIFEST.json and the SurvivalProject backup directory."""
from pathlib import Path
import hashlib,json,sys
base=Path(__file__).resolve().parent
root=(base/'SurvivalProject').resolve()
manifest=json.loads((base/'SHA256_MANIFEST.json').read_text(encoding='utf-8'))
errors=[]
for item in manifest['files']:
    path=(root/item['path']).resolve()
    try:path.relative_to(root)
    except ValueError:raise SystemExit('Invalid path in manifest')
    if not path.is_file():errors.append(item['path']);continue
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(8*1024*1024),b''):h.update(block)
    if h.hexdigest()!=item['sha256']:errors.append(item['path'])
print('Files checked:',len(manifest['files']))
print('Hash mismatches / missing:',len(errors))
for error in errors:print(error)
sys.exit(1 if errors else 0)
