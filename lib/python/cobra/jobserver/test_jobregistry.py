import unittest
from . import jobregistry
import cobra.postgres.interface as pgi

class TestJobregistry(unittest.TestCase):

    def test_class(self):

        jr = jobregistry.Jobregistry()
        self.assertEqual(jr.download_folder, './downloads')

    def test_init(self):

        jr = jobregistry.Jobregistry()
        interface = pgi.PgInterface()
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

    def test_shape2pg_job(self):

        jr = jobregistry.Jobregistry()
        interface = pgi.PgInterface()
        test_path = '/highway/to/test'
        test_name = 'Testjob'

        #jr.create_shape2pg_job(path_to_shape, job_name=None, skip_failures=True, priority=42, schema='gis')
        jr.create_shape2pg_job(test_path, job_name=test_name)

        conn = interface.get_connection()
        cur = conn.cursor()
        cur.execute(f"SELECT name FROM jobs.jobs WHERE name = '{test_name}'")
        res = cur.fetchone()[0]

        self.assertTrue(res == test_name)

        cur.execute(f"SELECT id FROM jobs.jobs WHERE name = '{test_name}'")
        id = cur.fetchone()[0]

        cur.execute(f"SELECT * FROM jobs.shape2pg WHERE id = '{id}'")
        res = cur.fetchone()

        self.assertEqual(res[1], test_path)

        jr.delete_all_jobs()

        cur.close()
        conn.close()

    def test_osm2pg_job(self):

        jr = jobregistry.Jobregistry()
        interface = pgi.PgInterface()
        osm_test_path = '/highway/to/osm'
        osm_test_name = 'OsmTestjob'
        style = 'test.style'

        #jr.create_shape2pg_job(path_to_shape, job_name=None, skip_failures=True, priority=42, schema='gis')
        jr.create_osm2pg_job(osm_test_path, style, job_name=osm_test_name)

        conn = interface.get_connection()
        cur = conn.cursor()
        cur.execute(f"SELECT name FROM jobs.jobs WHERE name = '{osm_test_name}'")
        res = cur.fetchone()[0]

        self.assertTrue(res == osm_test_name)

        cur.execute(f"SELECT id FROM jobs.jobs WHERE name = '{osm_test_name}'")
        id = cur.fetchone()[0]

        cur.execute(f"SELECT * FROM jobs.osm2pg WHERE id = '{id}'")
        res = cur.fetchone()

        self.assertEqual(res[1], osm_test_path)
        self.assertEqual(res[2], style)

        jr.delete_all_jobs()

        cur.close()
        conn.close()

    def test_get_jobs(self):

        jr = jobregistry.Jobregistry()
        jr.delete_all_jobs()

        jobs = jr.get_jobs()

        self.assertEqual(len(jobs), 0)

        osm_test_path = '/highway/to/osm'
        osm_test_name = 'OsmTestjob'
        style = 'test.style'
        jr.create_osm2pg_job(osm_test_path, style, job_name=osm_test_name)

        jobs = jr.get_jobs()
        
        self.assertEqual(len(jobs), 1)

        jr.delete_all_jobs()
        