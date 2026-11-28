"""Actual wheel/frozen-source/resource checks and synthetic private-worker run."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from verify_phase05_package import main as baseline_packages

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))


def normalized(code):
    return code.replace(co_filename='', co_consts=tuple(normalized(c) if hasattr(c, 'co_consts') else c for c in code.co_consts))


def main(output, frozen):
    result = baseline_packages(output, frozen)
    if frozen:
        from PyInstaller.archive.readers import CArchiveReader
        from clydex.core.processes import run_process
        from clydex.automation.tasks import CancellationToken
        archive = CArchiveReader(str(frozen)).open_embedded_archive('PYZ.pyz')
        modules = ('automation.workspace', 'automation.workflows.schema', 'automation.workflows.runtime',
                   'automation.scheduler', 'plugins.manager', 'plugins.sdk', 'integrations.mcp',
                   'integrations.services', 'tools.worker', 'tools.catalog', 'security.schema')
        for module in modules:
            code = archive.extract('clydex.' + module)
            source = ROOT / 'src/clydex' / (module.replace('.', '/') + '.py')
            assert normalized(code) == normalized(compile(source.read_text(encoding='utf-8'), '', 'exec')), module
        bundle = frozen.parent / '_internal'
        migration = Path('clydex/database/migrations/005_operating.sql')
        assert (bundle / migration).read_bytes() == (ROOT / 'src' / migration).read_bytes()
        assert (bundle / 'tzdata/zoneinfo/Asia/Colombo').is_file()
        assert list(bundle.glob('tzdata-*.dist-info/licenses/LICENSE'))
        assert list(bundle.glob('tzdata-*.dist-info/licenses/licenses/LICENSE_APACHE'))
        entry = ROOT / 'examples/plugins/synthetic_echo/echo.py'
        data = dict(kind='plugin', data=dict(entry=str(entry), sha256=hashlib.sha256(entry.read_bytes()).hexdigest(),
            request=dict(sdk_version=1, operation='tool', tool='echo.text', arguments={'text': 'Synthetic frozen SDK fixture'}, configuration={})))
        process = run_process([str(frozen), '--internal-worker'], input=json.dumps(data), timeout=20,
                              cancel=CancellationToken(), max_output_bytes=65536, memory_limit_bytes=536870912)
        assert process.returncode == 0, process.stderr
        assert json.loads(process.stdout)['result']['text'] == 'Synthetic frozen SDK fixture', process.stdout
        result.update(operating_modules_verified=list(modules), schema5=True, packaged_iana_timezone=True, timezone_license_notices=True,
                      actual_frozen_plugin_helper=True, helper_started_core=False,
                      optional_sql_camera_mqtt='Dependencies/accounts/hardware not activated or accepted')
    (output / 'package-results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--frozen', type=Path)
    args = parser.parse_args()
    print(json.dumps(main(args.output.resolve(), args.frozen.resolve() if args.frozen else None), indent=2))
