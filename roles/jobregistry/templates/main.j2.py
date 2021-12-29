import cobra.helper.logging as logging
import cobra.jobserver.jobregistry as jobs
from flask import Flask, request, jsonify

app = Flask(__name__)
l = logging.Logger('jobregistry Flask')

reg = jobs.Jobregistry()

@app.route('/')
def hello_world():
    l.debug('hello_world')
    return 'Hello, Docker!'

def data_or_default(key, dict, default_val):
  
    if key in dict.keys():
      return dict[key]
    else:
      return default_val

@app.route('/shape_to_pg_job', methods=['POST'])
def shape_to_pg_job():
    l.info('POST shape_to_pg_job')
    data = request.json
    
    try:
        l.debug(data)

        path = data['path']
        job_name = data_or_default('job_name',data,None)
        skip_failures = bool(data_or_default('skip_failures',data,True))
        priority = int(data_or_default('priority',data,42))
        schema = data_or_default('schema',data, 'gis')
        
        #TODO: Check/fix skip_failures
        reg.create_shape2pg_job(path, job_name=job_name, priority=priority, skip_failures=skip_failures, schema=schema)
        l.info('jobcreated')
    except Exception as inst:
        l.error("job failed", inst)
        app.logger.error(inst)
    finally:
        return jsonify(data)

@app.route('/osm_to_pg_job', methods=['POST'])
def osm_to_pg_job():
    l.info('POST osm_to_pg_job')
    data = request.json
    
    try:
        l.debug(data)

        path_to_osm = data['path_to_osm']
        style = data_or_default('style',data, "default.style")
        job_name = data_or_default('job_name',data,None)
        priority = int(data_or_default('priority',data,42))
        schema = data_or_default('schema',data, 'gis')
        
        #TODO: Check/fix skip_failures
        reg.create_osm2pg_job(path_to_osm, job_name=job_name, priority=priority, style=style, schema=schema)
        l.info('jobcreated')
    except Exception as inst:
        l.error("job failed", inst)
        app.logger.error(inst)
    finally:
        return jsonify(data)

@app.route('/jobs', methods=['GET'])
def get_jobs():
    l.info('GET jobs')
    data = request.json
    result_list = []

    try:
        l.debug(data)
        if data != None:
            job_type = data_or_default('job_type', data, None)
            status = data_or_default('status', data, None)
            result_list = reg.get_jobs(status=status, job_type=job_type)
        else:
            result_list = reg.get_jobs()
    
    except Exception as inst:
        l.error('Could not query jobs', inst)
    
    finally:
        return jsonify(result_list)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')