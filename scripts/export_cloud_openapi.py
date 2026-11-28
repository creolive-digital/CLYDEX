"""Export actual route/model contracts locally; no service/database/network startup."""
import argparse
import json
from pathlib import Path
import tempfile
from unittest.mock import Mock
from clydex_cloud.api.app import create_app
from clydex_cloud.core.config import Settings


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as folder:
        settings = Settings(Path(folder) / 'data', Path(folder) / 'keys', environment='test', require_tls=False)
        application = create_app(settings, runtime=Mock())
        document = application.openapi()
    args.output.write_text(json.dumps(document, indent=2) + '\n', encoding='utf-8')
    print(f'Exported {len(document["paths"])} paths from actual FastAPI routes; no network/database connection.')
