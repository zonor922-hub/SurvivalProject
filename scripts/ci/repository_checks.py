"""Static Git repository checks. Never execute project scripts or download LFS objects."""

import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


CHECKS = ('structure', 'python', 'json', 'lfs', 'ini', 'afs', 'evidence')
AFS_SECTION = '/Script/AndroidFileServerEditor.AndroidFileServerRuntimeSettings'
MANIFEST = 'scripts/ci/evidence_manifest.json'
REQUIRED = (
    'SurvivalProject.uproject', '.gitattributes', '.gitignore', 'AGENTS.md',
    'Config/DefaultEngine.ini', 'Config/DefaultGame.ini', 'Config/DefaultInput.ini',
    'Docs/ProjectStatus.md', 'Docs/Architecture/README.md',
    'Content/Survival/Inventory/BPC_Inventory.uasset',
    'Content/Survival/Interaction/BPC_Interaction.uasset',
    'Content/Survival/Interaction/BP_WorldPickup.uasset',
    'Content/Survival/UI/WBP_HUD.uasset',
    'Content/Survival/Maps/LV_SystemsTest.umap',
    '.github/workflows/repository-ci.yml', 'scripts/ci/repository_checks.py',
    'scripts/ci/test_repository_checks.py', MANIFEST,
)
LFS_EXTENSIONS = frozenset(
    '.uasset .umap .ubulk .uexp .uptnl .png .jpg .jpeg .tga .psd .exr .hdr '
    '.fbx .blend .wav .ogg .mp4 .r16 .r8'.split()
)
POINTER = re.compile(
    rb'version https://git-lfs.github.com/spec/v1\n'
    rb'oid sha256:[0-9a-f]{64}\nsize (?:0|[1-9][0-9]*)\n'
)
EVIDENCE = {
    'Docs/Architecture/evidence/a12_automatic_summary.json': 'a12',
    'Docs/Architecture/evidence/a12_negative_summary.json': 'a12',
    'Docs/Architecture/evidence/a14_pie.json': 'tests',
    'Docs/Architecture/evidence/a15_lifecycle_results.json': 'lifecycle',
}


class Invalid(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Invalid(message)


def git(root, *args, data=None):
    result = subprocess.run(
        ['git', '-C', str(root), *args], input=data, capture_output=True, check=False,
    )
    # Do not print Git stderr or file content: it may contain sensitive values.
    require(result.returncode == 0, 'Git metadata command failed')
    return result.stdout


def load_json(raw):
    def pairs(entries):
        result = {}
        for key, value in entries:
            require(key not in result, 'duplicate JSON object key')
            result[key] = value
        return result

    def constant(_value):
        raise Invalid('nonstandard JSON number')

    try:
        return json.loads(raw.decode('utf-8-sig'), object_pairs_hook=pairs,
                          parse_constant=constant)
    except (UnicodeError, json.JSONDecodeError) as exc:
        line = getattr(exc, 'lineno', None)
        raise Invalid('invalid JSON encoding/syntax' + (f' at line {line}' if line else '')) from None


def parse_ini(raw):
    """UE permits repeated assignments and + - . ! array operators; no interpolation."""
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeError:
        raise Invalid('INI must be UTF-8') from None
    require('\x00' not in text, 'NUL in INI')
    sections = {}
    section = None
    for number, source in enumerate(text.splitlines(), 1):
        line = source.strip()
        if not line or line.startswith((';', '#')):
            continue
        if line.startswith('['):
            require(bool(re.fullmatch(r'\[[^\[\]\r\n]+\]', line)),
                    f'malformed INI section at line {number}')
            section = line[1:-1]
            sections.setdefault(section, [])
            continue
        require(section is not None and '=' in line,
                f'expected section or key=value at line {number}')
        key, value = line.split('=', 1)
        key = key.strip()
        require(bool(re.fullmatch(r'[+.!\-]?[^\s=\[\]]+', key)),
                f'invalid INI key at line {number}')
        sections[section].append((key, value.strip()))
    require(bool(sections), 'INI contains no sections')
    return sections


class Repository:
    def __init__(self, root):
        self.root = root.resolve()
        self.entries = {}
        for row in git(root, 'ls-files', '--stage', '-z').split(b'\0'):
            if not row:
                continue
            meta, path = row.split(b'\t', 1)
            mode, oid, stage = meta.decode().split()
            name = path.decode('utf-8')
            require(stage == '0', 'unmerged Git index entry')
            require(mode in ('100644', '100755'), f'{name}: unsupported symlink/submodule')
            self.entries[name] = oid

    def read(self, name):
        require(name in self.entries, f'{name}: required tracked file missing')
        path = self.root / name
        require(not path.is_symlink() and path.is_file(), f'{name}: regular file missing')
        return path.read_bytes()

    def structure(self):
        for name in REQUIRED:
            require(name in self.entries and (self.root / name).is_file(),
                    f'{name}: required tracked file missing')
        project = load_json(self.read('SurvivalProject.uproject'))
        require(isinstance(project, dict) and type(project.get('FileVersion')) is int,
                'uproject: expected object and integer FileVersion')
        require(project.get('EngineAssociation') == '5.8', 'uproject: expected UE 5.8 association')
        return f'{len(REQUIRED)} required files; UE 5.8 project descriptor'

    def python(self):
        names = [p for p in self.entries if p.endswith('.py')]
        for name in names:
            try:
                ast.parse(self.read(name).decode('utf-8-sig'), filename=name)
            except (SyntaxError, UnicodeError) as exc:
                raise Invalid(f'{name}: Python syntax/encoding error at line '
                              f'{getattr(exc, "lineno", "unknown")}') from None
        return f'{len(names)} Python files parsed; none executed'

    def json(self):
        names = [p for p in self.entries if Path(p).suffix.lower() in ('.json', '.uproject', '.uplugin')]
        for name in names:
            try:
                load_json(self.read(name))
            except Invalid as exc:
                raise Invalid(f'{name}: {exc}') from None
        return f'{len(names)} JSON/project descriptors parsed'

    def lfs(self):
        names = list(self.entries)
        raw = git(self.root, 'check-attr', '--cached', '-z', '--stdin',
                  'filter', 'diff', 'merge', 'text', data=b'\0'.join(p.encode() for p in names) + b'\0')
        fields = raw.split(b'\0')[:-1]
        attributes = {p: {} for p in names}
        for offset in range(0, len(fields), 3):
            name, attribute, value = fields[offset:offset + 3]
            attributes[name.decode()][attribute.decode()] = value.decode()
        # Query sizes before reading: a mistakenly committed giant asset must not be loaded.
        oids = list(dict.fromkeys(self.entries.values()))
        sizes = git(self.root, 'cat-file', '--batch-check=%(objectname) %(objecttype) %(objectsize)',
                    data=('\n'.join(oids) + '\n').encode()).decode().splitlines()
        sizes = {row.split()[0]: (row.split()[1], int(row.split()[2])) for row in sizes}
        small = [oid for oid in oids if sizes[oid][1] <= 1024]
        output = git(self.root, 'cat-file', '--batch', data=('\n'.join(small) + '\n').encode())
        blobs = {}
        cursor = 0
        for oid in small:
            end = output.index(b'\n', cursor)
            header = output[cursor:end].split()
            size = int(header[2])
            blobs[oid] = output[end + 1:end + 1 + size]
            cursor = end + 2 + size
        count = 0
        for name, oid in self.entries.items():
            attrs = attributes[name]
            is_lfs = attrs['filter'] == 'lfs'
            require(Path(name).suffix.lower() not in LFS_EXTENSIONS or is_lfs,
                    f'{name}: binary extension must use LFS attributes')
            blob = blobs.get(oid, b'')
            if is_lfs:
                require(all(attrs[k] == v for k, v in
                            [('diff', 'lfs'), ('merge', 'lfs'), ('text', 'unset')]),
                        f'{name}: expected diff=lfs merge=lfs -text')
                require(bool(POINTER.fullmatch(blob)), f'{name}: invalid canonical LFS pointer in Git index')
                count += 1
            else:
                require(not blob.startswith(b'version https://git-lfs.github.com/spec/'),
                        f'{name}: LFS pointer has no effective LFS attributes')
        return f'{count} Git-index pointers; no LFS objects downloaded or inspected'

    def ini(self):
        names = [p for p in self.entries if p.lower().endswith('.ini')]
        for name in names:
            try:
                parse_ini(self.read(name))
            except Invalid as exc:
                raise Invalid(f'{name}: {exc}') from None
        return f'{len(names)} INI files; UE repeated keys and array operators allowed'

    def afs(self):
        name = 'Config/DefaultEngine.ini'
        sections = parse_ini(self.read(name))
        entries = sections.get(AFS_SECTION, [])
        # Case-insensitive and operator-insensitive detection prevents alternate spellings.
        values = {}
        for key, value in entries:
            values.setdefault(key.lstrip('+-.!').lower(), []).append(value.lower())
        require('securitytoken' not in values, f'{name}: AFS SecurityToken must be absent (value omitted)')
        for key in ('benableplugin', 'ballownetworkconnection',
                    'bincludeinshipping', 'ballowexternalstartinshipping'):
            require(values.get(key) == ['false'], f'{name}: AFS {key} must occur once as False')
        # A token assigned in another section of the same config is also prohibited.
        require(not any(key.lstrip('+-.!').lower() == 'securitytoken'
                        for entries in sections.values() for key, _ in entries),
                f'{name}: SecurityToken key must be absent (value omitted)')
        return 'AFS plugin/network disabled; token absent; Shipping protections retained'

    def evidence(self):
        manifest = load_json(self.read(MANIFEST))
        require(isinstance(manifest, dict) and manifest.get('schema_version') == 1,
                'evidence manifest: unsupported schema')
        rows = manifest.get('files')
        require(isinstance(rows, list) and len(rows) == len(EVIDENCE), 'evidence manifest: wrong file count')
        require(all(isinstance(row, dict) for row in rows), 'evidence manifest: invalid entry')
        require(Counter(row.get('path') for row in rows) == Counter(EVIDENCE.keys()),
                'evidence manifest: unexpected or duplicate paths')
        for row in rows:
            name = row['path']
            require(bool(re.fullmatch(r'[0-9a-f]{64}', str(row.get('sha256', '')))),
                    f'{name}: invalid manifest SHA-256')
            raw = self.read(name)
            # Git-normalized LF avoids false mismatches on Windows text checkouts.
            require(hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest() == row['sha256'],
                    f'{name}: historical evidence digest mismatch; review before updating manifest')
            evidence = load_json(raw)
            require(isinstance(evidence, dict) and type(evidence.get('passed')) is bool,
                    f'{name}: expected historical boolean passed field')
            engine = evidence.get('engine_version', evidence.get('engine'))
            require(isinstance(engine, str) and engine.startswith('5.8.4-'), f'{name}: engine metadata missing')
            tests = evidence.get('tests')
            require(isinstance(tests, list) and bool(tests), f'{name}: historical tests missing')
            require(all(isinstance(t, dict) and type(t.get('passed')) is bool
                        and isinstance(t.get('name', t.get('test')), str) for t in tests),
                    f'{name}: invalid historical test record')
            if EVIDENCE[name] == 'a12':
                context = evidence.get('context', {})
                require(isinstance(context, dict) and bool(re.fullmatch(r'[0-9a-f]{40}', str(context.get('commit', '')))),
                        f'{name}: tested commit metadata missing')
                require(type(evidence.get('process_exit_code')) is int
                        and type(evidence.get('timed_out')) is bool, f'{name}: runner metadata missing')
                for key, count in [('pass_assertions', sum(t['passed'] for t in tests)),
                                   ('fail_assertions', sum(not t['passed'] for t in tests))]:
                    require(type(evidence.get(key)) is int and evidence[key] == count,
                            f'{name}: historical assertion count mismatch')
            if EVIDENCE[name] == 'lifecycle':
                hashes = evidence.get('unchanged_assets_sha256', {})
                require(isinstance(hashes, dict) and bool(hashes)
                        and all(re.fullmatch(r'[0-9a-f]{64}', str(v)) for v in hashes.values()),
                        f'{name}: historical asset digest metadata missing')
        return f'{len(rows)} historical documents: digest/schema only; historical false is allowed; NO runtime tests run'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--check', action='append', choices=CHECKS, help='Run only selected groups')
    args = parser.parse_args(argv)
    try:
        repo = Repository(args.root)
    except (Invalid, OSError, ValueError):
        print('FAIL repository: cannot read supported Git index', file=sys.stderr)
        return 1
    failed = False
    for check in args.check or CHECKS:
        try:
            print(f'PASS {check}: {getattr(repo, check)()}')
        except Invalid as exc:
            print(f'FAIL {check}: {exc}', file=sys.stderr)
            failed = True
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            print(f'FAIL {check}: missing or malformed input (content omitted)', file=sys.stderr)
            failed = True
    return int(failed)


if __name__ == '__main__':
    sys.exit(main())
