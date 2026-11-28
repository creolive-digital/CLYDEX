"""Inspect actual frozen resources and build wheels from an external source snapshot."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main(output, frozen):
    output.mkdir(parents=True, exist_ok=True)
    result = {}
    with tempfile.TemporaryDirectory(prefix='wheel-input-', dir=output) as folder:
        for label, source in (('desktop', ROOT), ('cloud', ROOT / 'cloud')):
            target = Path(folder) / label
            target.mkdir()
            shutil.copy2(source / 'pyproject.toml', target / 'pyproject.toml')
            shutil.copytree(source / 'src', target / 'src', ignore=shutil.ignore_patterns('__pycache__', '*.egg-info'))
            subprocess.run([sys.executable, '-m', 'pip', 'wheel', '--no-deps', '--no-build-isolation', str(target),
                            '--wheel-dir', str(output)], check=True, stdout=subprocess.DEVNULL)
    wheels = list(output.glob('*.whl'))
    for path in wheels:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            if path.name.startswith('clydex_cloud-'):
                assert 'clydex_cloud/repositories/migrations/001_core.sql' in names
                assert 'clydex_cloud/api/app.py' in names
            else:
                assert 'clydex/database/migrations/004_cloud.sql' in names
                assert 'clydex/cloud/workspace.py' in names
                assert 'clydex/desktop/hud_contract.json' in names
    result['wheels'] = [{'name': p.name, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in wheels]
    if frozen:
        from PyInstaller.archive.readers import CArchiveReader
        archive = CArchiveReader(str(frozen))
        pyz = archive.open_embedded_archive('PYZ.pyz')
        assert 'clydex.cloud.workspace' in pyz.toc
        assert 'clydex.synchronization.local' in pyz.toc
        assert 'clydex_cloud.api.app' not in pyz.toc
        code = pyz.extract('clydex.cloud.workspace')
        def normalized_code(value):
            return value.replace(co_filename='', co_consts=tuple(
                normalized_code(x) if hasattr(x, 'co_consts') else x for x in value.co_consts))
        source_code = compile((ROOT / 'src/clydex/cloud/workspace.py').read_text(encoding='utf-8'), '', 'exec')
        assert normalized_code(code) == normalized_code(source_code), 'Frozen cloud client differs from reviewed source.'
        def constants(value):
            for item in value.co_consts:
                if hasattr(item, 'co_consts'):
                    yield from constants(item)
                else:
                    yield item
        assert 'sync.theme' in set(x for x in constants(code) if isinstance(x, str))
        bundle = frozen.parent / '_internal'
        migration = bundle / 'clydex/database/migrations/004_cloud.sql'
        assert migration.read_bytes() == (ROOT / 'src/clydex/database/migrations/004_cloud.sql').read_bytes()
        assert json.loads((bundle / 'clydex/desktop/hud_contract.json').read_text()) == json.loads((ROOT / 'src/clydex/desktop/hud_contract.json').read_text())
        expected = ROOT / 'deployment/windows/artifacts/frontend'
        assets = list(expected.rglob('*'))
        for path in assets:
            if path.is_file():
                assert (bundle / 'frontend/hud' / path.relative_to(expected)).read_bytes() == path.read_bytes()
        result.update(frozen_resources=True, embedded_cloud_client=True, cloud_server_excluded=True,
                      frontend_files_verified=sum(p.is_file() for p in assets), legacy_fallback=(bundle/'frontend/legacy/index.html').is_file())
    (output / 'package-results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--frozen', type=Path)
    args = parser.parse_args()
    print(json.dumps(main(args.output.resolve(), args.frozen), indent=2))
