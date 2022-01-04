import cobra.helper.logging as logging
import requests
import cobra.postgres.interface as pgi
import pandas as pd
import os

class Job():

    '''
    A job definition for a task that will be executed on a separate pod.
    '''
    
    def __init__(self):

        self.l = logging.Logger(self)
        self.l.debug("NEW Job")
        
        self.id : UUID = None
        self.name : String = None
        self.job_type : String = None
        self.date_created : Date = None
        self.date_stated : Date = None
        self.date_finished : Date = None
        self.priority : Integer = None
        self.status : String = None

    def __repr__(self):
        return f"Job ({self.name})"

    def __str__(self):
        return f"Job ({self.id})"
 
    
    def set_values_from_db(self, job_id, name, job_type, date_created, date_started, date_finished, priority, status):
        
        self.l.debug(f'set values from db ({job_id}, {name}, {job_type})')

        self.id : UUID = job_id
        self.name : String = name
        self.job_type : String = job_type
        self.date_created : Date = date_created
        self.date_stated : Date = date_started
        self.date_finished : Date = date_finished
        self.priority : Integer = priority
        self.status : String = status
        
        
    def values_as_list(self):
             
        return [self.id,
        self.name,
        self.job_type,
        self.date_created,
        self.date_stated,
        self.date_finished,
        self.priority,
        self.status]

class Jobmanager():

    '''
    Class to query and create jobs
    '''
    
    def __init__(self):
        
        self.l = logging.Logger(self)
        self.l.debug ('New Job_Manager')
        #TODO: Use job registry instead of direct DB access
        self.pg_interface = pgi.PgInterface()
        self.pg_interface.switch_schema('gdal')
    
    def get_jobs(self, df=False):

        self.l.debug(f'get_jobs')
        
        job_list = []
        results = requests.get('http://jobregistry:5000/jobs')

        for a_result in results.json():
            new_job = Job()
    
            new_job.set_values_from_db(a_result[0], a_result[1],a_result[2],a_result[3],a_result[4],a_result[5],a_result[6],a_result[7])
            job_list.append(new_job)
                
        if df == False:
        
            return job_list
        
        else:
            
            return pd.DataFrame([a_job.values_as_list() for a_job in job_list], columns = ['UUID','Name','Job Type','Date created','Date started','Date finished','Priority','Status'])
    
    def create_import_job_from_dataset(self, dataset, schema='gis'):

        self.l.debug('create_job_from_dataset')

        if dataset['Type'] == 'Shape':

            dataset_name = dataset['Dataset']
            data_file = dataset['File']
            path = dataset['Path']

            self.create_new_shape_to_pg(f'{path}/{data_file}', f'Load shape from {dataset_name}', schema=schema)

        elif dataset['Type'] == 'OSM PBF':

            dataset_name = dataset['Dataset']
            data_file = dataset['File']
            path = dataset['Path']

            self.create_new_osm_to_pg(f'{path}/{data_file}', f'Load OSM from {dataset_name}', schema=schema)
        
        else:

            self.l.error('Cannot load this dataset yet')



    def create_new_shape_to_pg(self, path, job_name = None, skip_failures = None, priority = None, schema='gis'):
        
        self.l.debug(f'create_new_shape_to_pg ({path})')

        # Check if file exists
        if os.path.isfile(path) == False:
            
            raise Exception(f'File {path} does not exist')
        
        body = {'path' : path,
            'schema' : schema }

        if job_name != None:
            body['job_name'] = job_name
        if skip_failures != None:
            body['skip_failures'] = skip_failures
        if priority != None:
            body['priority'] = priority
    
        r = requests.post('http://jobregistry:5000/shape_to_pg_job', json=body)
        
        if r.status_code != 200:
            raise Exception(f'job server has not accepted the job')

    def create_new_osm_to_pg(self, path_to_osm, job_name = None, priority = None, style='default.style', schema='gis'):

        self.l.debug(f'create_new_osm_to_pg ({path_to_osm})')

        # Check if file exists
        if os.path.isfile(path_to_osm) == False:
            
            raise Exception(f'File {path_to_osm} does not exist')

        # Check if style exists
        if os.path.isfile(os.path.join('/styles',style)) == False:
            
            raise Exception(f'File {path_to_osm} does not exist')

        body = {
            'path_to_osm' : path_to_osm,
            'style' : style,
            'schema' : schema
            }

        if job_name != None:
            body['job_name'] = job_name
        if priority != None:
            body['priority'] = priority

        r = requests.post('http://jobregistry:5000/osm_to_pg_job', json=body)
        
        if r.status_code != 200:
            raise Exception(f'job server has not accepted the job')