#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import html
import re
from pathlib import Path


RELEASES_DIR = Path(__file__).resolve().parent
SIMPLE_DIR = RELEASES_DIR / 'simple'
PACKAGE_NAME = 'clickhouse-driver'
PACKAGE_DIR = SIMPLE_DIR / PACKAGE_NAME
VERSION = '0.2.10'
PLATFORM = 'linux_x86_64'
PYTHON_TAGS = ('cp312', 'cp313', 'cp314')
WHEEL_RE = re.compile(
    rf'^clickhouse_driver-{re.escape(VERSION)}-'
    rf'(?P<python_tag>cp31[234])-(?P<abi_tag>cp31[234])-'
    rf'{re.escape(PLATFORM)}\.whl$'
)


def sha256sum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def collect_wheels() -> tuple[list[tuple[str, Path, str]], list[str]]:
    wheels = []
    found_tags = set()

    for path in sorted(RELEASES_DIR.glob('clickhouse_driver-*.whl')):
        match = WHEEL_RE.match(path.name)
        if match is None:
            continue

        python_tag = match.group('python_tag')
        abi_tag = match.group('abi_tag')
        if python_tag != abi_tag:
            continue

        wheels.append((python_tag, path, sha256sum(path)))
        found_tags.add(python_tag)

    missing = [tag for tag in PYTHON_TAGS if tag not in found_tags]
    wheels.sort(key=lambda item: item[0])
    return wheels, missing


def build_root_index() -> str:
    return """<!DOCTYPE html>
<html>
  <body>
    <a href=\"clickhouse-driver/\">clickhouse-driver</a>
  </body>
</html>
"""


def build_package_index(wheels: list[tuple[str, Path, str]], missing: list[str]) -> str:
    lines = ['<!DOCTYPE html>', '<html>', '  <body>']

    if missing:
        missing_text = ', '.join(missing)
        lines.append(f'    <!-- Missing wheels: {missing_text} -->')

    if wheels:
        for _python_tag, path, digest in wheels:
            href = f'../../{html.escape(path.name)}#sha256={digest}'
            name = html.escape(path.name)
            lines.append(f'    <a href="{href}">{name}</a><br>')
    else:
        lines.append('    <!-- No matching wheels found. -->')

    lines.extend(['  </body>', '</html>', ''])
    return '\n'.join(lines)


def main() -> int:
    wheels, missing = collect_wheels()

    SIMPLE_DIR.mkdir(exist_ok=True)
    PACKAGE_DIR.mkdir(exist_ok=True)

    (SIMPLE_DIR / 'index.html').write_text(build_root_index(), encoding='utf-8')
    (PACKAGE_DIR / 'index.html').write_text(
        build_package_index(wheels, missing),
        encoding='utf-8'
    )

    print(f'Wrote {(SIMPLE_DIR / "index.html").relative_to(RELEASES_DIR)}')
    print(f'Wrote {(PACKAGE_DIR / "index.html").relative_to(RELEASES_DIR)}')

    if wheels:
        print('Included wheels:')
        for python_tag, path, _digest in wheels:
            print(f'  {python_tag}: {path.name}')
    else:
        print('Included wheels: none')

    if missing:
        print(f'Missing wheels: {", ".join(missing)}')
    else:
        print('Missing wheels: none')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
