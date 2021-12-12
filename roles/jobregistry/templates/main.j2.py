import cobra_logging
import cobra_jobregistry
from flask import Flask, request, jsonify

app = Flask(__name__)
l = cobra_logging.Logger('jobregistry Flask')

reg = cobra_jobregistry.cobra_jobregistry()

@app.route('/')
def hello_world():
    l.debug('hello_world')
    return 'Hello, Docker!'

def data_or_default(key, dict, default_val):
  
    if key in dict.keys():
      return dict[key]
    else:
      return default_val

@app.route('/job', methods=['POST'])
def job():
    l.info('POST job')
    data = request.json
    
    try:
        l.debug(data)

        path = data['path']
        job_name = data_or_default('job_name',data,None)
        skip_failures = bool(data_or_default('skip_failures',data,True))
        priority = int(data_or_default('priority',data,42))
        
        #TODO: Check/fix skip_failures
        reg.create_shape2pg_job(path, job_name=job_name, priority=priority, skip_failures=skip_failures)
        l.info('jobcreated')
    except Exception as inst:
        l.error("job failed", inst)
        app.logger.error(inst)
    finally:
        return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')