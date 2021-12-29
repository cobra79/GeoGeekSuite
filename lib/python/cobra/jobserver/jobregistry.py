import os
import cobra.helper.logging as logging
import os.path
import cobra.postgres.interface as pgi
import cobra.postgres.datamodelfabric as fabric
import uuid

class Jobregistry:
    '''
    Jobregistry
    '''
    def __init__(self, download_folder='./downloads', host='postgres', database='postgres',user='postgres',password=None):
        if password == None:
            password = os.environ['POSTGRES_PASSWORD']
        self.connection_string = f'host={host} dbname={database} user={user} password={password}'
        self.download_folder = download_folder
        self.l = logging.Logger(self)
        self.pg = pgi.PgInterface()
        self.init_database_structure()

    def __repr__(self):
        return "Jobregistry"
    def __str__(self):
        return "Registry for Jobs"

    def init_database_structure(self):

        self.l.debug('init_database_structure')
        
        self.pg.create_schema('jobs', True)
        job_dm_dict = {
            'name': 'jobs',
            'tables':[
                {
                    'tablename':'jobs',
                    'fields':[
                        {'name':'id','type':'UUID PRIMARY KEY'},
                        {'name':'name', 'type':'VARCHAR (64) NOT NULL'},
                        {'name':'job_type', 'type':'VARCHAR (32) NOT NULL'},
                        {'name': 'date_created', 'type':'TIMESTAMP DEFAULT now()'},
                        {'name': 'date_started', 'type':'TIMESTAMP'},
                        {'name': 'date_finished', 'type':'TIMESTAMP'},
                        {'name': 'priority', 'type':'INTEGER'},
                        {'name':'status', 'type':'VARCHAR (32)'}
                    ]
                },
                {
                    'tablename':'shape2pg',
                    'fields':[
                        {'name':'id','type':'UUID PRIMARY KEY'},
                        {'name':'path_to_shape', 'type':'VARCHAR (255) NOT NULL'},
                        {'name':'skip_failures', 'type':'BOOLEAN'},
                        {'name':'target_schema', 'type':'VARCHAR (128)'}

                    ]
                },
                {
                    'tablename':'osm2pg',
                    'fields':[
                        {'name':'id','type':'UUID PRIMARY KEY'},
                        {'name':'path_to_osm', 'type':'VARCHAR (255) NOT NULL'},
                        {'name':'style', 'type':'VARCHAR (32)'},
                        {'name':'target_schema', 'type':'VARCHAR (128)'}
                    ]
                }
            ]
        }
        
        dmf = fabric.DataModelFabric()
        job_dm = dmf.create_from_dict(job_dm_dict)
        dm_man = pgi.DataModelManager()
        dm_man.add_datamodel(job_dm)
        dm_man.apply_datamodel('jobs')

    def create_shape2pg_job(self, path_to_shape, job_name=None, skip_failures=True, priority=42, schema='gis'):
    
        self.l.debug('create_shape2pg_job')

        job_id = str(uuid.uuid4())
        if job_name == None:
            job_name = 'Load Shape'

        #Update Jobs
        keys = ['id','name','job_type','status','priority']
        values = [[job_id, job_name,'shape2pg','Waiting', str(priority)]]
        self.pg.insert_into_table('jobs','jobs',keys, values)

        #Update shape2pg table
        keys = ['id','path_to_shape','skip_failures','target_schema']
        values = [[job_id, path_to_shape, str(skip_failures), schema]]
        self.pg.insert_into_table('jobs','shape2pg',keys, values)  

    def create_osm2pg_job(self, path_to_osm, style, job_name=None, priority=42, schema='gis'):

        self.l.debug('create_osm2pg_job')

        job_id = str(uuid.uuid4())
        if job_name == None:
            job_name = 'Load OSM'

        #Update Jobs
        keys = ['id','name','job_type','status','priority']
        values = [[job_id, job_name,'osm2pg','Waiting', str(priority)]]
        self.pg.insert_into_table('jobs','jobs',keys, values)

        #Update shape2pg table
        keys = ['id','path_to_osm','style','target_schema']
        values = [[job_id, path_to_osm, style, schema]]
        self.pg.insert_into_table('jobs','osm2pg',keys, values)

    def get_jobs(self, job_type=None, status=None):

        self.l.debug(f'get_jobs (job_type:{str(job_type)}, status:{str(status)}')

        job_list = []

        sql = 'SELECT * FROM jobs.jobs'

        if job_type != None and status == None:

            sql = f"{sql} WHERE job_type='{job_type}'"

        if job_type == None and status != None:

            sql = f"{sql} WHERE status='{status}'"

        if job_type != None and status != None:

            sql = f"{sql} WHERE job_type='{job_type}' AND status='{status}'"

        with self.pg.get_connection() as conn:
            
            with conn.cursor() as curs:
                
                curs.execute(sql)
                results = curs.fetchall()
                for a_result in results:
                    
                    job_list.append(a_result)

        self.l.debug(f'Returning {len(job_list)} jobs')

        return job_list

    def delete_all_jobs(self):

        sql_statements = ['DELETE FROM jobs.jobs','DELETE FROM jobs.shape2pg','DELETE FROM jobs.osm2pg']

        with self.pg.get_connection() as conn:
            
            with conn.cursor() as curs:
                
                for sql in sql_statements:
                    curs.execute(sql)
                    conn.commit()