"""Opt-in native SQL qualification; never use an existing production database.

The owner must separately authorize and supply an EMPTY disposable SQL Server
2025 database named clx_phase05_*. This suite never provisions a server/database.
"""
import os
from pathlib import Path
import unittest
from sqlalchemy import inspect, text
from sqlalchemy.engine import make_url
from clydex_cloud.repositories.database import Database
from clydex_cloud.repositories.migrate import migrate, rollback_empty


@unittest.skipUnless(os.environ.get('CLYDEX_ALLOW_ISOLATED_SQL_TESTS') == 'true', 'No owner-authorized isolated SQL Server test environment supplied')
class NativeSqlTests(unittest.TestCase):
    def test_transactional_migration_constraints_and_ga_exact_vector_distance(self):
        path = Path(os.environ['CLYDEX_TEST_SQL_URL_FILE'])
        if not path.is_absolute() or path.is_symlink():
            self.fail('A protected absolute disposable-test DSN file is required.')
        url = path.read_text().strip()
        parsed = make_url(url)
        self.assertTrue(parsed.database.startswith('clx_phase05_'))
        database = Database(url)
        try:
            with database.engine.connect() as c:
                self.assertEqual(inspect(c).get_table_names(), [], 'Native test database must be empty.')
            self.assertTrue(migrate(database))
            try:
                self.assertTrue(database.ready())
                self.assertFalse(migrate(database))
                with database.transaction() as c:
                    self.assertEqual(c.execute(text("SELECT VECTOR_DISTANCE('cosine', CAST('[1,0]' AS VECTOR(2)), CAST('[1,0]' AS VECTOR(2)))")).scalar(), 0)
                with self.assertRaisesRegex(RuntimeError, 'synthetic rollback'):
                    with database.transaction() as c:
                        c.execute(text("INSERT INTO clx_invitation_uses(digest,used_at) VALUES(:digest,:epoch)"), {'digest':'a'*64,'epoch':1})
                        raise RuntimeError('synthetic rollback')
                with database.transaction() as c:
                    self.assertEqual(c.execute(text('SELECT COUNT(*) FROM clx_invitation_uses')).scalar(), 0)
                # Constraints/indexes are installed by the actual native DDL.
                with database.engine.connect() as c:
                    self.assertTrue(inspect(c).get_foreign_keys('clx_document_versions'))
                    self.assertTrue(inspect(c).get_indexes('clx_documents'))
            finally:
                rollback_empty(database)
        finally:
            database.close()
