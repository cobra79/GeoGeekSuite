import cobra_logging
import requests
import cobra_postgres
import pandas as pd
import os

class Job():

    '''
    A job definition for a task that will be executed on a separate pod.
    '''
    
    def __init__(self):

        self.l = cobra_logging.Logger(self)
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

class Job_Manager():

    '''
    Class to query and create jobs
    '''
    
    def __init__(self):
        
        self.l = cobra_logging.Logger(self)
        self.l.debug ('New Job_Manager')
        self.pg_interface = cobra_postgres.PgInterface()
        self.pg_interface.switch_schema('gdal')
    
    def get_jobs(self, df=False):

        self.l.debug(f'get_fobs')
        
        job_list = []
        with self.pg_interface.get_connection() as conn:
            
            with conn.cursor() as curs:
                
                curs.execute('SELECT * FROM gdal.gdal_jobs')
                results = curs.fetchall()
                for a_result in results:
                    new_job = Job()
                    new_job.set_values_from_db(a_result[0], a_result[1],a_result[2],a_result[3],a_result[4],a_result[5],a_result[6],a_result[7])
                    job_list.append(new_job)
                
        if df == False:
        
            return job_list
        
        else:
            
            return pd.DataFrame([a_job.values_as_list() for a_job in job_list], columns = ['UUID','Name','Job Type','Date created','Date started','Date finished','Priority','Status'])
    
    def create_new_shape_to_pg(self, path, job_name = None, skip_failures = None, priority = None):
        
        self.l.debug(f'create_new_shape_to_pg ({path})')

        # Check if file exists
        if os.path.isfile(path) == False:
            
            raise Exception(f'File {path} does not exist')
        
        body = {'path' : path}
        if job_name != None:
            body['job_name'] = job_name
        if skip_failures != None:
            body['skip_failures'] = skip_failures
        if priority != None:
            body['priority'] = priority
    
        r = requests.post('http://jobregistry:5000/job', json=body)
        
        if r.status_code != 200:
            raise Exception(f'job server has not accepted the job')
