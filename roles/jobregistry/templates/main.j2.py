import cobra_logging
import cobra_gdal
from flask import Flask, request, jsonify
app = Flask(__name__)
l = cobra_logging.Logger('GDAL Flask')
l.debug('Start Cobra Logging')
@app.route('/')
def hello_world():
    l.debug('hello_world')
    return 'Hello, Docker!'

@app.route('/load_shape', methods=['POST'])
def load_shape():
    app.logger.info('load_shape')
    data = request.json
    g = cobra_gdal.cobra_gdal()
    try:
        app.logger.debug(data)
        #app.logger.info(f'{data['path']}')
        g.shape2pg(data.get('path'))
    except Exception as inst:
        app.logger.error(inst)
    finally:
        return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')