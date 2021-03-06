import cobra.helper.logging as logging
import cobra.postgres.interface as pgi
import time
import subprocess
import os


class Osm2PgSql():

    '''
    Little bit more than a wrapper for GDAL...
    The Osm2PgSql class impletments a process that is intended to run inside a container.
    Purpose is to pickup jobs that use osm2pgsql to load OSM data.
    '''

    def __init__(self, run_in_loop = False, schema=None):

        '''
        Constructor
        Within a container the class schould normally run a loop.
        schema in the deprecated as it will be part of a job.
        '''
        #TODO: remove schema

        self.l = logging.Logger(self)
        self.l.debug("New osm2pgsql")
        self.busy = False
        
        opsdatabase = os.environ['OPSDATABASE']
        gisdatabase = os.environ['PGDATABASE']

        self.pg_ops = pgi.PgInterface(opsdatabase)
        self.pg_gis = pgi.PgInterface(gisdatabase)

        if run_in_loop:
            self._mainloop_()

    def __repr__(self):

        return "osm2pgsql"

    def __str__(self):
        
        return "Process that takes jobs and excecutes them with osm2pgsql"

    def _mainloop_(self):

        '''
        Infinite loop that checks in a devined interval for new jobs.
        '''

        while True:

            self.pick_a_job_when_not_busy()
            #TODO: Make sleeptime configurable
            time.sleep(10)

    def pick_a_job_when_not_busy(self):

        '''
        Check if busy, if not try a job - if available
        '''

        self.l.silly('pick_a_job_when_not_busy')
        if self.busy == False:
            self.pick_a_job()


    def pick_a_job(self):

        '''
        Pick a job - if available
        '''

        self.l.silly('pick_a_job')

        with self.pg_ops.get_connection() as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT id, job_type FROM jobs.jobs WHERE status = 'Waiting' AND job_type = 'osm2pg' ORDER BY priority, date_created LIMIT 1")
                result = curs.fetchone()
                if result != None:
                    job_id = result[0]
                    job_type = result[1]
                    self.l.debug(f'Found job {job_id} of type {job_type}')

                    curs.execute(f"SELECT path_to_osm, target_schema, style FROM jobs.osm2pg WHERE id = '{job_id}'")
                    result = curs.fetchone()
                    path_to_osm = result[0]
                    schema = result[1]
                    style = result[2]
                    
                    self.l.debug(f'Path for osm {path_to_osm}. Create in schema {schema}, style: {style}')
                    self.update_job_status(job_id, 'Started')

                    self.execute_osm2pgsql(path_to_osm, job_id, schema=schema, style=style)

                else:
                    self.l.silly('No Waining jobs in queue')
                    job_type = None

               
            
                
    def update_job_status(self, job_id, new_status):

        self.l.debug(f'update_job_status of {job_id}: Set to {new_status}')
        sql = f"UPDATE jobs.jobs SET status='{new_status}' WHERE id = '{job_id}'"
        with self.pg_ops.get_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql)
            
    def update_time(self, job_id, timefield):

        self.l.debug('Update Time')
        sql = f"UPDATE jobs.jobs SET {timefield}=now() WHERE id = '{job_id}'"
        with self.pg_ops.get_connection() as conn:
            with conn.cursor() as curs:
                curs.execute(sql)
    
    
    def execute_osm2pgsql(self, path_to_pbf, job_id, style, schema='gis', cache=None):

        self.l.debug("execute_osm2pgsql")

        self.busy = True

        self.pg_gis.create_schema(schema)

        
        if os.path.isfile(path_to_pbf) == False:
            self.l.error(f'File {path_to_pbf} does not exist')
            self.update_job_status(job_id, 'Failed')
            self.busy = False
            return 

        #if os.path.isfile(f'/styles/style') == False:
        #    self.l.error(f'Style /styles/{style} does not exist')
        #    self.update_job_status(job_id, 'Failed')
        #    self.busy = False
        #    return 

        try:
            
            #args =['osm2pgsql','-c','-d', self.connection_string, '-S', f'{self.style}', path_to_pbf]
            self.l.info(f'run osm2pgsql, styple:{style}, schema:{schema}, path_to_pbf:{path_to_pbf}')
            args =['osm2pgsql','-c','-S', f'/styles/{style}', f'--output-pgsql-schema={schema}', '--slim', path_to_pbf]
            
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
            self.l.error(f'Faild to execute osm2pgsql', e)
        finally:
            self.busy = False

