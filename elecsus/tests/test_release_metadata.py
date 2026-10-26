"""[ES4] The version has to be the same in all three places that declare it.

`pyproject.toml`, `CITATION.cff` and `.zenodo.json` each carry a version string,
and they have drifted before: at the point this test was written they read
4.0.0, 4.0.0a2 and 4.0.0a1 respectively. Citation tooling reads the latter two
and installers read the first, so a mismatch means the DOI, the citation and the
installed package disagree about which release they are.

Bumping a version is therefore a three-file edit, and this test is what tells
you when you have only done two of them.

Skipped when the repository files are not present (e.g. running against an
installed wheel, which ships none of them).
"""
import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
PYPROJECT = REPO / 'pyproject.toml'
CITATION = REPO / 'CITATION.cff'
ZENODO = REPO / '.zenodo.json'

pytestmark = pytest.mark.skipif(
    not (PYPROJECT.exists() and CITATION.exists() and ZENODO.exists()),
    reason='release metadata files are not present outside the repository')


def _pyproject_version():
    for line in PYPROJECT.read_text().splitlines():
        match = re.match(r'\s*version\s*=\s*["\']([^"\']+)["\']', line)
        if match:
            return match.group(1)
    raise AssertionError('no version field in pyproject.toml')


def _citation_version():
    for line in CITATION.read_text().splitlines():
        match = re.match(r'\s*version:\s*(\S+)', line)
        if match:
            return match.group(1).strip('"\'')
    raise AssertionError('no version field in CITATION.cff')


def _zenodo_version():
    return json.loads(ZENODO.read_text())['version']


def test_all_three_declared_versions_agree():
    versions = {
        'pyproject.toml': _pyproject_version(),
        'CITATION.cff': _citation_version(),
        '.zenodo.json': _zenodo_version(),
    }
    assert len(set(versions.values())) == 1, (
        'version strings disagree: '
        + ', '.join(f'{name} = {value}' for name, value in sorted(versions.items()))
        + '. Bumping a release means editing all three.')


def test_zenodo_metadata_is_valid_json_with_the_fields_zenodo_needs():
    data = json.loads(ZENODO.read_text())
    for field in ('title', 'version', 'upload_type', 'license', 'creators'):
        assert field in data, f'.zenodo.json is missing {field!r}'
    assert data['creators'], '.zenodo.json lists no creators'
    for creator in data['creators']:
        assert 'name' in creator, f'creator entry without a name: {creator!r}'


def test_citation_cff_declares_the_fields_github_needs():
    text = CITATION.read_text()
    for field in ('cff-version:', 'title:', 'authors:', 'version:'):
        assert field in text, f'CITATION.cff is missing {field}'


def test_the_installed_version_is_exposed_as_dunder_version():
    """`elecsus.__version__` is the installed distribution's version (#112)."""
    from importlib.metadata import version
    import elecsus
    assert elecsus.__version__ == version('ElecSus')
    assert re.fullmatch(r'\d+(\.\d+)*(a|b|rc)?\d*', elecsus.__version__)


def test_no_tracked_file_holds_a_merge_conflict_marker():
    """elecsus/libs/NOTICE shipped '<<<<<<< HEAD' for years (#107)."""
    import shutil
    import subprocess
    if not (REPO / '.git').exists() or not shutil.which('git'):
        pytest.skip('needs a git checkout')
    # the pattern is built here so that this file does not match itself
    pattern = '^(' + '<' * 7 + '|' + '>' * 7 + ') '
    done = subprocess.run(['git', 'grep', '-nIE', pattern, '--', '.',
                           ':(exclude)*/reviews/*'],   # review reports quote one
                          cwd=REPO,
                          capture_output=True, text=True)
    assert done.returncode == 1, 'merge-conflict markers:\n' + done.stdout
