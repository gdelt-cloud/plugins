"""Exercise the documented manual install, including thin skill dependencies."""
import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ManualInstallTests(unittest.TestCase):
    def test_documented_install_keeps_shared_workflows_reachable(self):
        readme = (ROOT / 'README.md').read_text()
        section = readme.split('### By hand, without the plugin system', 1)[1]
        commands = section.split('```bash', 1)[1].split('# 2. key', 1)[0]
        commands = '\n'.join(line for line in commands.splitlines()
                             if line.strip() and not line.startswith(('#', 'git clone')))
        commands = commands.replace('/tmp/gdelt-cloud-plugins', str(ROOT))
        with tempfile.TemporaryDirectory() as temp:
            subprocess.run(['bash', '-eu', '-c', commands], cwd=temp, check=True)
            installed = (Path(temp) / '.claude').resolve()
            for skill in (installed / 'skills').glob('*/SKILL.md'):
                text = skill.read_text()
                for relative in re.findall(r'\]\((\.\./\.\./workflows/[^)]+)\)', text):
                    dependency = (skill.parent / relative).resolve()
                    self.assertTrue(dependency.is_relative_to(installed), relative)
                    self.assertTrue(dependency.is_file(), f'{skill.parent.name}: {relative}')
                    self.assertEqual(dependency.read_bytes(),
                                     (ROOT / 'plugins/gdelt-cloud' / relative[6:]).read_bytes())
            self.assertEqual(len(list((installed / 'workflows').glob('*/SKILL.md'))), 5)

    def test_readme_names_packaged_release(self):
        version = json.loads((ROOT / 'plugins/gdelt-cloud/workflows/manifest.json').read_text())['version']
        readme = (ROOT / 'README.md').read_text()
        advertised = re.search(r'canonical workflow bundle\s+`([^`]+)`', readme).group(1)
        self.assertEqual(advertised, version)

if __name__ == '__main__':
    unittest.main()
