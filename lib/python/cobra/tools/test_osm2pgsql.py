import unittest
from . import osm2pgsql

class TestOsm2PgSql(unittest.TestCase):

    def test_class_init(self):

        osm2pgsql_class = osm2pgsql.Osm2PgSql()
        self.assertEqual(osm2pgsql_class.busy, False)

