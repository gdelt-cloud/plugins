"""Standalone verification of the exported canonical workflow release."""
from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parents[1]/'plugins/gdelt-cloud/workflows'
m=json.loads((root/'manifest.json').read_text())
assert len(m['files']) == 5
assert {str(p.relative_to(root)) for p in root.glob('*/SKILL.md')} == set(m['files'])
for name,digest in m['files'].items():
    assert 'sha256:'+hashlib.sha256((root/name).read_bytes()).hexdigest() == digest, name
print('Canonical workflow bundle verified:',m['version'])
