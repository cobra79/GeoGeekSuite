import os
import cobra_logging
import os.path
import cobra_postgres
import cobra_datamodelfabric
import uuid
class cobra_gdal:
    '''
    Wrapper for GDAL
    '''
    def __init__(self, download_folder='./downloads', host='postgres', database='postgres',user='postgres',password=None):
        if password == None:
            password = os.environ['POSTGRES_PASSWORD']
        self.connection_string = f'host={host} dbname={database} user={user} password={password}'
        self.download_folder = download_folder
        self.l = cobra_logging.Logger(self)
        self.pg = cobra_postgres.PgInterface()
        self.busy = False

    def __repr__(self):
        return "cobra_gdal"
    def __str__(self):
        return "A wrapper for GDAL"

    def init_database_structure(self):

        self.l.debug('init_database_structure')
        
        self.pg.create_schema('gdal', True)
        gdal_dm_dict = {
            'name': 'gdal',
            'tables':[
                {
                    'tablename':'gdal_jobs',
                    'fields':[
                        {'name':'id','type':'UUID PRIMARY KEY'},
                        {'name':'name', 'type':'VARCHAR (64) NOT NULL'},
                        {'name':'job_type', 'type':'VARCHAR (32) NOT NULL'},
                        {'name': 'date_created', 'type':'TIMESTAMP DEFAULT now()'},
                        {'name': 'priority', 'type':'INTEGER'},
                        {'name':'status', 'type':'VARCHAR (32)'}
                    ]
                },
                {
                    'tablename':'shape2pg',
                    'fields':[
                        {'name':'id','type':'UUID PRIMARY KEY'},
                        {'name':'path_to_shape', 'type':'VARCHAR (255) NOT NULL'},
                        {'name':'skip_failures', 'type':'BOOLEAN'}
                    ]
                }
            ]
        }
        
        dmf = cobra_datamodelfabric.DataModelFabric()
        gdal_dm = dmf.create_from_dict(gdal_dm_dict)
        dm_man = cobra_postgres.DataModelManager()
        dm_man.add_datamodel(gdal_dm)
        dm_man.apply_datamodel('gdal')

    def pick_a_job_when_not_busy(self):

        self.l.debug('pick_a_job_when_not_busy')
        if self.busy == False:
            self.pick_a_job()

    def pick_a_job(self):

        self.l.debug('pick_a_job')

        with self.pg.get_connection() as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT id, job_type FROM gdal.gdal_jobs WHERE status = 'Waiting' ORDER BY priority, date_created LIMIT 1")
                result = curs.fetchone()
                if result != None:
                    job_id = result[0]
                    job_type = result[1]

                if job_type == 'shape2pg':
                    curs.execute(f"SELECT path_to_shape, skip_failures FROM gdal.shape2pg WHERE id = '{job_id}'")
                    result = curs.fetchone()
                    if result != None:
                        path_to_shape = result[0]
                        skip_failures = result[1] == 'True'

                        self.execute_shape2pg(path_to_shape, job_id, skip_failures)

    def create_shape2pg_job(self, path_to_shape, job_name=None, skip_failures=True, priority=42):
    
        self.l.debug('create_shape2pg_job')

        job_id = str(uuid.uuid4())
        if job_name == None:
            job_name = 'Load Shape'

        #Update GDAL Jobs
        keys = ['id','name','job_type','status','priority']
        values = [[job_id, job_name,'shape2pg','Waiting', str(priority)]]
        self.pg.insert_into_table('gdal','gdal_jobs',keys, values)

        #Update shape2pg table
        keys = ['id','path_to_shape','skip_failures']
        values = [[job_id, path_to_shape, str(skip_failures)]]
        self.pg.insert_into_table('gdal','shape2pg',keys, values)  

    def update_job_status(self, job_id, new_status):
        self.l.debug(f'update_job_status of {job_id}: Set to {new_status}')
        sql = f"UPDATE gdal.gdal_jobs SET status='{new_status}' WHERE id = '{job_id}'"
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

        command = f'ogr2ogr -f "PostgreSQL" PG:"{self.connection_string}" "{path_to_shape}"'
        self.l.debug(command)
        if skip_failures:
            command = f'{command} -skip-failures'
        self.l.debug(f'ogr2ogr -f "PostgreSQL" PG:"..." "{path_to_shape}"')
        try:
            os_return_value = os.system(command)
            self.l.debug(f'ogr2ogr returned {os_return_value}')
            self.update_job_status(job_id, 'Finished')
        except Exception as e:
            self.update_job_status(job_id, 'Failed')
            self.l.error(e)
        finally:
            self.busy = False
            

