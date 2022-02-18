#TODO: Rename Gdal to shape2pgsql

import os
import cobra.helper.logging as logging
import os.path
import cobra.postgres.interface as pgi
import time
import subprocess

class Gdal:
    '''
    Little bit more than a wrapper for GDAL...
    The Gdal class impletments a process that is intended to run inside a container.
    Purpose is to pickup jobs (that require gdal) and execute them.
    '''
    def __init__(self, download_folder=None, host=None,user=None, schema=None, run_in_loop=False):
        
        self.l = logging.Logger(self)
        
        password = os.environ['PGPASSWORD']
        if host == None:
            host = os.environ['PGHOST']
        
        opsdatabase = os.environ['OPSDATABASE']
        self.gisdatabase = os.environ['PGDATABASE']

        if user == None:
            user = os.environ['PGUSER']
        self.gis_connection_string = f'host={host} dbname={self.gisdatabase} user={user} password={password}'
        if download_folder == None:
            self.download_folder = os.environ['DOWNLOAD_FOLDER']
        else:
            self.download_folder = download_folder
        self.pg = pgi.PgInterface(opsdatabase)
        self.busy = False
        if run_in_loop:
            self._mainloop_()

    def __repr__(self):
        return "GDAL"

    def __str__(self):
        return "A wrapper for GDAL"

    def get_gis_db_connection_string(self):

        password = os.environ['PGPASSWORD']

        if self.schema == None:
            return f'host={self.host} dbname={self.gisdatabase} user={self.user} password={password}'
        else:
            return f'host={self.host} dbname={self.gisdatabase} user={self.user} password={password} schemas={self.schema}'
        

    def _mainloop_(self):

        while True:
            self.pick_a_job_when_not_busy()
            time.sleep(10)


    def pick_a_job_when_not_busy(self):

        self.l.silly('pick_a_job_when_not_busy')
        if self.busy == False:
            self.pick_a_job()

    def pick_a_job(self):

        self.l.silly('pick_a_job')
       
        with self.pg.get_connection() as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT id, job_type FROM jobs.jobs WHERE (status = 'Waiting' AND job_type = 'shape2pg') OR (status = 'Waiting' AND job_type = 'pg2x')  ORDER BY priority, date_created LIMIT 1")
                result = curs.fetchone()
                if result != None:
                    job_id = result[0]
                    job_type = result[1]
                    self.l.debug(f'Found job {job_id} of type {job_type}')
                else:
                    self.l.silly('No Waining jobs in queue')
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
                elif job_type == 'pg2x':
                    self.l.debug(f'pg2x job (job: {job_id})')
                    curs.execute(f"SELECT sql, format, filename FROM jobs.pg2x WHERE id = '{job_id}'")
                    result = curs.fetchone()
                    self.l.debug(f'result: {result}')
                    if result != None:
                        self.l.silly(f'Found details {result}')
                        sql = result[0]
                        format = result[1]
                        filename = result[2]
                        self.update_job_status(job_id, 'Started')
                        self.execute_pg2x(sql, format, filename, job_id)
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

    def execute_pg2x(self, sql, format, filename, job_id):

        self.l.debug(f'execute_pg2sql sql:{sql}, format:{format}, filename:{filename}')
        self.busy = True

        try:
            connection_string = self.gis_connection_string
            args = ['ogr2ogr', '-f', format, f'/export/{filename}', f'PG: {connection_string}', '-sql', sql ]
            return_value = subprocess.run(args)

            if return_value.returncode == 0:
                self.l.info(f'Job {job_id} - export to {filename} finished successfully')
                self.update_job_status(job_id, 'Finished')
                self.update_time(job_id, 'date_finished')
            else: 
                self.l.error(f'Error in {job_id} - export {filename} failed')
                self.l.error(return_value.stderr)
                self.update_job_status(job_id, 'Failed')
        except Exception as e:
            self.update_job_status(job_id, 'Failed')
            self.l.error(e)
        finally:
            self.busy = False

             

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
            connection_string = self.gis_connection_string
            args =['ogr2ogr','-f','PostgreSQL',f'PG: {connection_string}', '-lco', f'SCHEMA={self.schema}', path_to_shape]
            if skip_failures:
                args.append('-skipfailures')
            return_value = subprocess.run(args)

            if return_value.returncode == 0:
                self.l.info(f'Job {job_id} - loading {path_to_shape} finished successfully')
                self.update_job_status(job_id, 'Finished')
                self.update_time(job_id, 'date_finished')
            else: 
                self.l.error(f'Error in {job_id} - loading {path_to_shape} failed')
                self.l.error(return_value.stderr)
                self.update_job_status(job_id, 'Failed')
        except Exception as e:
            self.update_job_status(job_id, 'Failed')
            self.l.error(e)
        finally:
            self.busy = False
            

