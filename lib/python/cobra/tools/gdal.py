import os
import cobra.helper.logging as logging
import os.path
import cobra.postgres.interface as pgi
import time
import subprocess
class Gdal:
    '''
    Wrapper for GDAL
    '''
    def __init__(self, download_folder='./downloads', host='postgres', database='postgres',user='postgres', schema=None, run_in_loop=False):
        
        self.l = logging.Logger(self)
        
        self.host = host
        self.database = database
        self.user = user
        self.schema = schema
            
        self.download_folder = download_folder
        
        self.pg = pgi.PgInterface()
        self.busy = False
        if run_in_loop:
            self._mainloop_()

    def __repr__(self):
        return "GDAL"

    def __str__(self):
        return "A wrapper for GDAL"

    def get_connection_string(self):

        password = os.environ['POSTGRES_PASSWORD']

        if self.schema == None:
            return f'host={self.host} dbname={self.database} user={self.user} password={password}'
        else:
            return f'host={self.host} dbname={self.database} user={self.user} password={password} schemas={self.schema}'
        

    def _mainloop_(self):

        while True:
            self.pick_a_job_when_not_busy()
            time.sleep(10)


    def pick_a_job_when_not_busy(self):

        self.l.debug('pick_a_job_when_not_busy')
        if self.busy == False:
            self.pick_a_job()

    def pick_a_job(self):

        self.l.debug('pick_a_job')
       
        with self.pg.get_connection() as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT id, job_type FROM jobs.jobs WHERE status = 'Waiting' AND job_type = 'shape2pg' ORDER BY priority, date_created LIMIT 1")
                result = curs.fetchone()
                if result != None:
                    job_id = result[0]
                    job_type = result[1]
                    self.l.debug(f'Found job {job_id} of type {job_type}')
                else:
                    self.l.debug('No Waining jobs in queue')
                    job_type = None

                if job_type == 'shape2pg':
                    self.l.debug(f'get shape job details')
                    #TODO: Check skip failures
                    curs.execute(f"SELECT path_to_shape, skip_failures, target_schema FROM jobs.shape2pg WHERE id = '{job_id}'")
                    result = curs.fetchone()
                    if result != None:
                        path_to_shape = result[0]
                        skip_failures = result[1] == 'True'
                        target_schema = result[2]
                        self.l.debug(f'Execute shape loading for {path_to_shape} to {target_schema}')
                        self.update_job_status(job_id, 'Started')
                        self.execute_shape2pg(path_to_shape, job_id, schema=target_schema, skip_failures=True)
                    else:
                        self.l.error(f'No details on Job')
                        self.update_job_status(job_id, 'Failed - no details')

    def update_job_status(self, job_id, new_status):
        self.l.debug(f'update_job_status of {job_id}: Set to {new_status}')
        sql = f"UPDATE jobs.jobs SET status='{new_status}' WHERE id = '{job_id}'"
        with self.pg.get_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql)
            
    def update_time(self, job_id, timefield):

        self.l.debug('Update Time')
        sql = f"UPDATE jobs.jobs SET {timefield}=now() WHERE id = '{job_id}'"
        with self.pg.get_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql)

    def execute_shape2pg(self, path_to_shape, job_id, skip_failures=True, schema=None):

        self.l.debug(f'execute_shape2pg path:{path_to_shape} id:{job_id} schema:{schema}')     

        if schema != None:

            self.schema = schema

        self.pg.create_schema(self.schema)

        self.busy = True

        if os.path.isfile(path_to_shape) == False:
            self.l.error(f'File {path_to_shape} does not exist')
            self.update_job_status(job_id, 'Failed')
            self.busy = False
            return 

        try:
            connection_string = self.get_connection_string()
            self.l.debug(f'connect string {connection_string}')
            self.l.debug(f'SCHEMA={self.schema}')
            args =['ogr2ogr','-f','PostgreSQL',f'PG: {connection_string}', '-lco', f'SCHEMA={self.schema}', path_to_shape]
            if skip_failures:
                args.append('-skipfailures')
            return_value = subprocess.run(args)

            if return_value.returncode == 0:
                self.l.info(f'Job {job_id} - loading {path_to_shape} finished successfully')
                self.update_job_status(job_id, 'Finished')
                self.update_time(job_id, 'date_finished')
            else: 
                self.l.error(f'Error in {job_id} - loading {path_to_shape} finished')
                self.l.error(return_value.stderr)
                self.update_job_status(job_id, 'Failed')
        except Exception as e:
            self.update_job_status(job_id, 'Failed')
            self.l.error(e)
        finally:
            self.busy = False
            
