import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'plugins/gdelt-cloud'

class PublicReleaseTests(unittest.TestCase):
    def test_all_client_defaults_use_the_canonical_endpoint(self):
        for client in ('claude', 'codex', 'cursor'):
            cfg = json.loads((DATA / f'.mcp.{client}.json').read_text())
            self.assertEqual(cfg['mcpServers']['gdelt-cloud']['url'], 'https://mcp.gdeltcloud.com/mcp')
            self.assertEqual(cfg['mcpServers']['gdelt-cloud-docs']['url'], 'https://docs.gdeltcloud.com/mcp')

    def test_packaged_named_workflows_do_not_route_to_absent_wrappers(self):
        manifest = json.loads((DATA / 'workflows/manifest.json').read_text())
        self.assertEqual(manifest['tool_exposure'], 'named')
        old = re.compile(r'\b\w+_tool_(?:list|get|call|write)\b')
        offenders = [str(p.relative_to(ROOT)) for folder in ('skills', 'workflows')
                     for p in (DATA / folder).rglob('*.md') if old.search(p.read_text())]
        self.assertEqual(offenders, [])

class DiscoveryGuidanceTests(unittest.TestCase):
    def test_does_not_invent_schema_or_execution_discovery_tools(self):
        files = [ROOT / 'README.md', *(DATA / 'skills').rglob('*.md'), *(DATA / 'workflows').rglob('*.md')]
        unavailable = re.compile(r'\b(?:get_tool_schema|search_tools)\b')
        self.assertEqual([str(p.relative_to(ROOT)) for p in files if unavailable.search(p.read_text())], [])

if __name__ == '__main__': unittest.main()
