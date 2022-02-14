import unittest
import cobra.postgres.interface as pgi
from cobra.postgres.interface import TableDefinition
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

test_db_name = 'testdb'

class TestPgi(unittest.TestCase):

    def test_class_init(self):

        i = pgi.PgInterface()
        self.assertEqual(i.database, 'postgres')
       

    def test_new_db(self):

        i = pgi.PgInterface()
        conn = i. get_connection()
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute(f"CREATE DATABASE {test_db_name}")
        cur.execute(f"SELECT datname FROM pg_catalog.pg_database WHERE datname='{test_db_name}'")
        result = cur.fetchone()[0]
        self.assertEqual(result, test_db_name)
        i = pgi.PgInterface(database=test_db_name)
        td = TableDefinition('my_test_table')
        i.create_table(td)
        #TODO: Check if table exists
        cur.execute(f"DROP DATABASE {test_db_name}")
        cur.execute(f"SELECT datname FROM pg_catalog.pg_database WHERE datname='{test_db_name}'")
        result = cur.fetchone()
        self.assertEqual(result, None)
        
       