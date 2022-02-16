import unittest
from . import jobregistry
import cobra.postgres.interface as pgi

class TestJobregistry(unittest.TestCase):

    def test_class(self):

        test_db = 'test_ops'
        i = pgi.PgInterface()
        i.create_database(test_db)
        jr = jobregistry.Jobregistry(download_folder = './download', database=test_db)
        self.assertEqual(jr.download_folder, './download')
        i.drop_database(test_db)

    def test_init(self):

        test_db = 'test_ops'
        i = pgi.PgInterface()
        i.create_database(test_db)
        jr = jobregistry.Jobregistry(download_folder = './download', database=test_db)
        interface = pgi.PgInterface(database=test_db)
        conn = interface.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM information_schema.tables WHERE table_schema = 'jobs'")
        res = cur.fetchall()
        res = [x[2] for x in res]

        self.assertTrue('jobs' in res)
        self.assertTrue('shape2pg' in res)
        self.assertTrue('osm2pg' in res)
        self.assertTrue('pg2x' in res)

        cur.close()
        conn.close()
        i.drop_database(test_db)

    def test_shape2pg_job(self):

        test_db = 'testops'
        test_path = '/highway/to/test'
        test_name = 'Testjob'

        i = pgi.PgInterface()
        i.create_database(test_db)

        jr = jobregistry.Jobregistry(download_folder = './download', database=test_db)
         
        jr.create_shape2pg_job(test_path, job_name=test_name)

        i_test =  pgi.PgInterface(test_db)
        res = i_test.__execute_sql__(f"SELECT name FROM jobs.jobs WHERE name = '{test_name}'", fetch='one')
        res = res[0]

        self.assertTrue(res == test_name)

        id = i_test.__execute_sql__(f"SELECT id FROM jobs.jobs WHERE name = '{test_name}'", fetch='one')
        id = id[0]      

        res = i_test.__execute_sql__(f"SELECT * FROM jobs.shape2pg WHERE id = '{id}'", fetch='one')
        self.assertEqual(res[1], test_path)

        i.drop_database(test_db)
#
    def test_osm2pg_job(self):

        test_db = 'testops'
        osm_test_path = '/highway/to/osm'
        osm_test_name = 'OsmTestjob'
        style = 'test.style'

        i = pgi.PgInterface()
        i.create_database(test_db)

        jr = jobregistry.Jobregistry(download_folder = './download', database=test_db)
        i_test =  pgi.PgInterface(test_db)
        
        jr.create_osm2pg_job(osm_test_path, style, job_name=osm_test_name)

        res = i_test.__execute_sql__(f"SELECT name FROM jobs.jobs WHERE name = '{osm_test_name}'", fetch='one')
        res = res[0]

        self.assertTrue(res == osm_test_name)

        id = i_test.__execute_sql__(f"SELECT id FROM jobs.jobs WHERE name = '{osm_test_name}'", fetch='one')
        id = id[0]

        res = i_test.__execute_sql__(f"SELECT * FROM jobs.osm2pg WHERE id = '{id}'", fetch='one')

        self.assertEqual(res[1], osm_test_path)
        self.assertEqual(res[2], style)

        i.drop_database(test_db)

    def test_get_jobs(self):

        test_db = 'testops'

        i = pgi.PgInterface()
        i.create_database(test_db)

        jr = jobregistry.Jobregistry(download_folder = './download', database=test_db)
        jr.delete_all_jobs()

        jobs = jr.get_jobs()

        self.assertEqual(len(jobs), 0)

        osm_test_path = '/highway/to/osm'
        osm_test_name = 'OsmTestjob'
        style = 'test.style'
        jr.create_osm2pg_job(osm_test_path, style, job_name=osm_test_name)

        jobs = jr.get_jobs()
        
        self.assertEqual(len(jobs), 1)

        i.drop_database(test_db)
        