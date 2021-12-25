import os
import cobra_logging
import os.path
import cobra_postgres
import time
import subprocess
class cobra_gdal:
    '''
    Wrapper for GDAL
    '''
    def __init__(self, download_folder='./downloads', host='postgres', database='postgres',user='postgres',password=None, schema=None, run_in_loop=False):
        
        self.l = cobra_logging.Logger(self)
        
        if password == None:
            password = os.environ['POSTGRES_PASSWORD']
        if schema == None:
            self.connection_string = f'host={host} dbname={database} user={user} password={password}'
        else:
            self.connection_string = f'host={host} dbname={database} user={user} password={password} schemas={schema}'
        
        self.l.debug(f'Connection {self.connection_string}')
        
        self.download_folder = download_folder
        
        self.pg = cobra_postgres.PgInterface()
        self.busy = False
        if run_in_loop:
            self._mainloop_()

    def __repr__(self):
        return "cobra_gdal"
    def __str__(self):
        return "A wrapper for GDAL"

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
                curs.execute("SELECT id, job_type FROM jobs.jobs WHERE status = 'Waiting' ORDER BY priority, date_created LIMIT 1")
                result = curs.fetchone()
                if result != None:
                    job_id = result[0]
                    job_type = result[1]
                else:
                    self.l.debug('No Waining jobs in queue')
                    job_type = None

                if job_type == 'shape2pg':
                    curs.execute(f"SELECT path_to_shape, skip_failures FROM jobs.shape2pg WHERE id = '{job_id}'")
                    result = curs.fetchone()
                    if result != None:
                        path_to_shape = result[0]
                        skip_failures = result[1] == 'True'

                        self.execute_shape2pg(path_to_shape, job_id, skip_failures)

    def update_job_status(self, job_id, new_status):
        self.l.debug(f'update_job_status of {job_id}: Set to {new_status}')
        sql = f"UPDATE jobs.jobs.jobs SET status='{new_status}' WHERE id = '{job_id}'"
        with self.pg.get_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql)
            
    def update_time(self, job_id, timefield):

        self.l.debug('Update Time')
        sql = f"UPDATE jobs.jobs SET {timefield}=now() WHERE id = '{job_id}'"
        with self.pg.get_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql)

    def execute_shape2pg(self, path_to_shape, job_id, skip_failures=True):

        self.l.debug('execute_shape2pg')     

        self.busy = True

        if os.path.isfile(path_to_shape) == False:
            self.l.error(f'File {path_to_shape} does not exist')
            self.update_job_status(job_id, 'Failed')
            self.busy = False
            return 

        try:
            
            args =['ogr2ogr','-f','PostgreSQL',f'PG: {self.connection_string}', path_to_shape]
            if skip_failures:
                args.append('-skipfailures')
            return_value = subprocess.run(args)
            self.update_time(job_id, 'date_started')

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
            

