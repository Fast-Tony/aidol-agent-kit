import importlib.util
from pathlib import Path
import tempfile
import tomllib
import unittest

spec = importlib.util.spec_from_file_location('aidol_install', Path(__file__).parents[1] / 'install.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class InstallTests(unittest.TestCase):
    def test_both_servers_and_skills_and_preservation(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            (home / '.codex').mkdir()
            path = home / '.codex/config.toml'
            path.write_text('model="existing"\n[mcp_servers.other]\ncommand="other"\n', encoding='utf-8')
            for attempt in range(2):
                module.configure(home, Path(__file__).parents[1], Path('C:/Python/python.exe'))
            config = tomllib.loads(path.read_text(encoding='utf-8'))
            self.assertEqual(config['model'], 'existing')
            self.assertEqual(set(config['mcp_servers']), {'other','aidol_room','aidol_event_router'})
            self.assertTrue((home / '.claude/skills/aidol-room-live/SKILL.md').exists())
            self.assertTrue((home / '.codex/skills/aidol-event-router/SKILL.md').exists())


if __name__ == '__main__':
    unittest.main()
