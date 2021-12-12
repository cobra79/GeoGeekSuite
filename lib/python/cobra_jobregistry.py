import os
import cobra_logging
import os.path
import cobra_postgres
import cobra_datamodelfabric
import uuid

class cobra_jobregistry:
    '''
    Jobregistry
    '''
    def __init__(self, download_folder='./downloads', host='postgres', database='postgres',user='postgres',password=None):
        if password == None:
            password = os.environ['POSTGRES_PASSWORD']
        self.connection_string = f'host={host} dbname={database} user={user} password={password}'
        self.download_folder = download_folder
        self.l = cobra_logging.Logger(self)
        self.pg = cobra_postgres.PgInterface()
        self.init_database_structure()

    def __repr__(self):
        return "cobra_jobregistry"
    def __str__(self):
        return "Registry for Jobs"

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