"""CLI integration tests in disposable Git repositories; never edit source evidence."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import repository_checks as checks


SCRIPT = Path(checks.__file__).resolve()
SOURCE_ROOT = SCRIPT.parents[2]
POINTER = ('version https://git-lfs.github.com/spec/v1\n'
           'oid sha256:' + 'a' * 64 + '\nsize 123\n')
SAFE_INI = (
    f'[{checks.AFS_SECTION}]\n'
    'bEnablePlugin=False\nbAllowNetworkConnection=False\n'
    'bIncludeInShipping=False\nbAllowExternalStartInShipping=False\n'
    '[UnrealArrays]\n+Entries=A\n+Entries=B\n-Entries=C\n'
    '.Entries=D\n!Entries=ClearArray\nValue=(X=1,Y=2)\n'
    'Repeated=one\nRepeated=two\n'
)


class RepositoryChecksTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='survival-sec02-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.git('init', '--quiet')
        self.git('config', 'core.autocrlf', 'false')
        # Hooks and LFS filters are unnecessary: fixtures stage pointer text directly.
        self.git('config', 'core.hooksPath', str(self.root / 'unused-hooks'))
        self.git('config', 'filter.lfs.clean', 'cat')
        self.git('config', 'filter.lfs.smudge', 'cat')
        self.git('config', 'filter.lfs.process', '')
        self.git('config', 'filter.lfs.required', 'false')
        for name in checks.REQUIRED:
            value = POINTER if Path(name).suffix in checks.LFS_EXTENSIONS else 'fixture\n'
            self.write(name, value)
        self.write('SurvivalProject.uproject', json.dumps({'FileVersion': 3, 'EngineAssociation': '5.8'}))
        self.write('.gitattributes', '*.uasset filter=lfs diff=lfs merge=lfs -text\n'
                   '*.umap filter=lfs diff=lfs merge=lfs -text\n')
        for name in ['Config/DefaultEngine.ini', 'Config/DefaultGame.ini', 'Config/DefaultInput.ini']:
            self.write(name, SAFE_INI)
        for name in ['scripts/ci/repository_checks.py', 'scripts/ci/test_repository_checks.py']:
            self.write(name, 'raise RuntimeError("must not execute tracked project files")\n')
        self.write('fixture.json', '{"valid": true}\n')
        # Copy historical text into a temporary fixture, never write to the originals.
        for name in checks.EVIDENCE:
            self.write(name, (SOURCE_ROOT / name).read_bytes())
        self.manifest()
        self.stage()

    def git(self, *args):
        result = subprocess.run(['git', '-C', str(self.root), *args], capture_output=True)
        self.assertEqual(result.returncode, 0, 'temporary fixture Git operation failed')
        return result.stdout

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value.encode() if isinstance(value, str) else value)

    def stage(self):
        names = [str(p.relative_to(self.root)) for p in self.root.rglob('*')
                 if p.is_file() and '.git' not in p.relative_to(self.root).parts]
        self.git('add', '--', *names)

    def manifest(self):
        rows = [{'path': name, 'sha256': hashlib.sha256(
            (self.root / name).read_bytes().replace(b'\r\n', b'\n')).hexdigest()}
                for name in checks.EVIDENCE]
        self.write(checks.MANIFEST, json.dumps({'schema_version': 1, 'files': rows}))

    def run_check(self, group=None, succeeds=True):
        command = [sys.executable, '-B', str(SCRIPT), '--root', str(self.root)]
        if group:
            command += ['--check', group]
        result = subprocess.run(command, capture_output=True, text=True,
                                env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
        self.assertEqual(result.returncode, 0 if succeeds else 1, result.stdout + result.stderr)
        if not succeeds:
            self.assertIn('FAIL ' + group + ':', result.stderr)
        return result

    def test_positive_all_groups_including_historical_negative_result(self):
        result = self.run_check()
        self.assertEqual(result.stdout.count('PASS '), len(checks.CHECKS))
        self.assertIn('NO runtime tests run', result.stdout)

    def test_invalid_json_rejected(self):
        for value in ['{"broken":', '{"duplicate":1,"duplicate":2}', '{"bad":NaN}']:
            with self.subTest(case=value):
                self.write('fixture.json', value)
                self.run_check('json', succeeds=False)

    def test_python_syntax_error_rejected(self):
        self.write('scripts/ci/test_repository_checks.py', 'def broken(:\n')
        self.run_check('python', succeeds=False)

    def test_tracked_python_is_parsed_without_execution(self):
        self.run_check('python')  # Fixture Python would raise if executed.

    def test_malformed_lfs_pointer_rejected(self):
        self.write('Content/Survival/UI/WBP_HUD.uasset', POINTER.replace('a' * 64, 'not-a-digest'))
        self.stage()
        self.run_check('lfs', succeeds=False)

    def test_raw_binary_in_index_rejected(self):
        self.write('Content/Survival/UI/WBP_HUD.uasset', b'\x00' * 2048)
        self.stage()
        self.run_check('lfs', succeeds=False)

    def test_lfs_extension_attribute_mismatch_rejected(self):
        self.write('.gitattributes', '*.umap filter=lfs diff=lfs merge=lfs -text\n')
        self.stage()
        self.run_check('lfs', succeeds=False)

    def test_pointer_without_attributes_rejected(self):
        self.write('orphan.txt', POINTER)
        self.stage()
        self.run_check('lfs', succeeds=False)

    def test_lfs_reads_index_instead_of_smudged_worktree(self):
        self.write('Content/Survival/UI/WBP_HUD.uasset', b'simulated smudged content')
        self.run_check('lfs')

    def test_unsafe_afs_rejected_without_leaking_value(self):
        cases = [
            SAFE_INI.replace('bEnablePlugin=False', 'bEnablePlugin=True'),
            SAFE_INI.replace('bAllowNetworkConnection=False', 'bAllowNetworkConnection=True'),
            SAFE_INI.replace('bIncludeInShipping=False', 'bIncludeInShipping=True'),
            SAFE_INI.replace('bEnablePlugin=False', 'bEnablePlugin=False\nbEnablePlugin=True'),
            SAFE_INI.replace('[UnrealArrays]', 'SecurityToken=TEST_ONLY_DO_NOT_LOG\n[UnrealArrays]'),
            SAFE_INI.replace('[UnrealArrays]', '+securitytoken=\n[UnrealArrays]'),
        ]
        for index, value in enumerate(cases):
            with self.subTest(case=index):
                self.write('Config/DefaultEngine.ini', value)
                result = self.run_check('afs', succeeds=False)
                self.assertNotIn('TEST_ONLY_DO_NOT_LOG', result.stdout + result.stderr)

    def test_malformed_ini_rejected(self):
        self.write('Config/DefaultInput.ini', '[Broken\nValue=1\n')
        self.run_check('ini', succeeds=False)

    def test_missing_required_file_rejected(self):
        self.git('rm', '--quiet', '--force', '--', 'SurvivalProject.uproject')
        self.run_check('structure', succeeds=False)

    def test_evidence_digest_mismatch_rejected(self):
        name = next(iter(checks.EVIDENCE))
        self.write(name, (self.root / name).read_bytes() + b'\n')
        self.run_check('evidence', succeeds=False)

    def test_evidence_schema_rejected_even_with_updated_digest(self):
        name = next(iter(checks.EVIDENCE))
        value = json.loads((self.root / name).read_bytes())
        value['passed'] = 'not a boolean'
        self.write(name, json.dumps(value))
        self.manifest()
        self.run_check('evidence', succeeds=False)


if __name__ == '__main__':
    unittest.main()
