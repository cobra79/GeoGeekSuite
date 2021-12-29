import cobra.helper.logging as logging
import cobra.postgres.interface as pgi
import time
import subprocess
import os


class Osm2PgSql():

    '''
    wrapper for osm2pgsql
    '''

    def __init__(self, style="default.style", run_in_loop = False, schema=None):

        self.l = logging.Logger(self)
        self.l.debug("New osm2pgsql")
        self.style = style
        self.busy = False
        
        self.pg = pgi.PgInterface()

        if run_in_loop:
            self._mainloop_()

    def __repr__(self):

        return "osm2pgsql"

    def __str__(self):
        
        return "A wrapper for osm2pgsql"

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
                curs.execute("SELECT id, job_type FROM jobs.jobs WHERE status = 'Waiting' AND job_type = 'osm2pg' ORDER BY priority, date_created LIMIT 1")
                result = curs.fetchone()
                if result != None:
                    job_id = result[0]
                    job_type = result[1]
                    self.l.debug(f'Found job {job_id} of type {job_type}')

                    curs.execute(f"SELECT path_to_osm, target_schema FROM jobs.osm2pg WHERE id = '{job_id}'")
                    result = curs.fetchone()
                    path_to_osm = result[0]
                    schema = result[1]
                    
                    self.l.debug(f'Path for osm {path_to_osm}. Create in schema {schema}')
                    self.update_job_status(job_id, 'Started')

                    self.execute_osm2pgsql(path_to_osm, job_id, schema=schema)

                else:
                    self.l.debug('No Waining jobs in queue')
                    job_type = None

               
            
                
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
    
    
    def execute_osm2pgsql(self, path_to_pbf, job_id, schema='gis', cache=None):

        self.l.debug("execute_osm2pgsql")

        self.busy = True

        self.pg.create_schema(schema)


        if os.path.isfile(path_to_pbf) == False:
            self.l.error(f'File {path_to_pbf} does not exist')
            self.update_job_status(job_id, 'Failed')
            self.busy = False
            return 

        try:
            
            #args =['osm2pgsql','-c','-d', self.connection_string, '-S', f'{self.style}', path_to_pbf]
            args =['osm2pgsql','-c','-S', f'/styles/{self.style}', f'--output-pgsql-schema={schema}', path_to_pbf]
            
            if cache != None:
                args.append(f'--cache {str(cache)}')

            return_value = subprocess.run(args)

            if return_value.returncode == 0:
                self.l.info(f'Job {job_id} - loading {path_to_pbf} finished successfully')
                self.update_job_status(job_id, 'Finished')
                self.update_time(job_id, 'date_finished')
            else: 
                self.l.error(f'Error in {job_id} - loading {path_to_pbf} finished')
                self.l.error(return_value.stderr)
                self.update_job_status(job_id, 'Failed')
        
        except Exception as e:
            self.update_job_status(job_id, 'Failed')
            self.l.error(e)
        finally:
            self.busy = False

