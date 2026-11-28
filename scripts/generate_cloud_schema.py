"""Generate canonical packaged SQL Server DDL; review its diff before migration."""
from pathlib import Path
from sqlalchemy.dialects import mssql
from sqlalchemy.schema import CreateTable, CreateIndex, DropTable
from clydex_cloud.repositories.schema import metadata


def main():
    target = Path(__file__).resolve().parents[1] / 'cloud/src/clydex_cloud/repositories/migrations'
    target.mkdir(parents=True, exist_ok=True)
    dialect = mssql.dialect()
    tables = list(metadata.sorted_tables)
    up = [str(CreateTable(t).compile(dialect=dialect)).strip() for t in tables]
    up += [str(CreateIndex(i).compile(dialect=dialect)).strip() for t in tables for i in sorted(t.indexes, key=lambda x: x.name)]
    down = [str(DropTable(t).compile(dialect=dialect)).strip() for t in reversed(tables)]
    for name, statements in (('001_core.sql', up), ('001_core.down.sql', down)):
        content = '-- Generated SQL Server 2025 schema. Apply using clydex_cloud CLI only.\n' + '\nGO\n'.join(statements)
        content = '\n'.join(line.rstrip() for line in content.splitlines()) + '\n'
        (target / name).write_text(content, encoding='utf-8', newline='\n')
    print(f'Generated {len(tables)} tables and {sum(len(t.indexes) for t in tables)} indexes; native execution not established.')


if __name__ == '__main__':
    main()
