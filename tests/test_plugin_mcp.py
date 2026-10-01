"""Assert the Codex plugin JSON contract, not its TOML config spelling."""
import json
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
class PluginMcpTests(unittest.TestCase):
    def test_codex_plugin_declares_same_servers_as_claude(self):
        for root in (ROOT / 'plugins').iterdir():
            if not root.is_dir(): continue
            codex=json.loads((root / '.codex-plugin/plugin.json').read_text())
            claude=json.loads((root / '.claude-plugin/plugin.json').read_text())
            cx=json.loads((root / codex['mcpServers']).read_text())
            cc=json.loads((root / claude['mcpServers']).read_text())
            with self.subTest(plugin=root.name):
                self.assertIsInstance(cx.get('mcpServers'), dict)
                self.assertEqual(set(cx['mcpServers']), set(cc['mcpServers']))
                for name, server in cx['mcpServers'].items():
                    self.assertEqual(server['url'], cc['mcpServers'][name]['url'])
if __name__ == '__main__': unittest.main()
