"""Install both Aidol MCP servers and skills for the current user's agents."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import tomllib


def write_with_backup(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        shutil.copy2(path, path.with_name(path.name + '.aidol-backup-' + str(time.time_ns())))
    temporary = path.with_name(path.name + '.aidol-next')
    temporary.write_text(text, encoding='utf-8')
    os.replace(temporary, path)


def configure(home, root, python):
    home, root = Path(home), Path(root).resolve()
    codex = home / '.codex/config.toml'
    claude = home / '.claude.json'
    text = codex.read_text(encoding='utf-8-sig') if codex.exists() else ''
    parsed = tomllib.loads(text)
    payload = json.loads(claude.read_text(encoding='utf-8-sig')) if claude.exists() else {}
    if not isinstance(payload, dict) or not isinstance(payload.get('mcpServers', {}), dict):
        raise ValueError('Invalid Claude config; no agent configuration changed')
    entries = {'aidol_room': root / 'room/server.py', 'aidol_event_router': root / 'router/server.py'}
    for name, server in entries.items():
        entry = {'command': str(python), 'args': [str(server)]}
        section = '\n[mcp_servers.' + name + ']\ncommand = ' + json.dumps(str(python)) + '\nargs = ' + json.dumps([str(server)]) + '\nstartup_timeout_sec = 60\n'
        if name in parsed.get('mcp_servers', {}):
            pattern = r'(?ms)^\[mcp_servers\.' + name + r'\][^\n]*\n.*?(?=^\[|\Z)'
            text, count = re.subn(pattern, lambda match: section.lstrip('\n') + '\n', text)
            if count != 1:
                raise ValueError('Cannot safely replace existing Codex entry: ' + name)
        else:
            text += '\n' + section
        payload.setdefault('mcpServers', {})[name.replace('_', '-')] = {'type': 'stdio', **entry}
    tomllib.loads(text)
    for agent in ('.codex', '.claude'):
        for name in ('aidol-room-live', 'aidol-event-router'):
            source = root / 'skills' / name
            if not (source / 'SKILL.md').is_file():
                raise ValueError('Missing skill: ' + name)
            destination = home / agent / 'skills' / name
            if destination.exists():
                shutil.copytree(destination, home / agent / 'aidol-backups' / (name + '-' + str(time.time_ns())))
            shutil.copytree(source, destination, dirs_exist_ok=True)
    write_with_backup(codex, text)
    write_with_backup(claude, json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    return {'servers': list(entries), 'skills': ['aidol-room-live', 'aidol-event-router']}


def main():
    parser = argparse.ArgumentParser(description='Install Aidol Room + Event Router MCP and skills')
    parser.add_argument('--home', type=Path, default=Path.home(), help='Agent configuration home, defaults to current user')
    parser.add_argument('--skip-deps', action='store_true', help='For isolated tests with dependencies already available')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    if args.skip_deps:
        python = Path(sys.executable)
    else:
        import venv
        environment = root / '.venv'
        venv.EnvBuilder(with_pip=True).create(environment)
        python = environment / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
        subprocess.run([str(python), '-m', 'pip', 'install', '-r', str(root / 'requirements.txt')], check=True)
    print(json.dumps(configure(args.home, root, python), ensure_ascii=False))
    print('Installed. Restart Codex/Claude Code. Router needs the compatible Windows app; Room opens its own visible Chrome window.')


if __name__ == '__main__':
    main()
