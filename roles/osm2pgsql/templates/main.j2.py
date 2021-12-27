import cobra.helper.logging as logging
import cobra.tools.osm2pgsql as osm

from flask import Flask, request, jsonify
app = Flask(__name__)
l = logging.Logger('Osm2pgsql Flask')
l.debug('Start Cobra Logging')

#TODO: Schema handling
osm.Osm2PgSql(run_in_loop = True)

@app.route('/')
def hello_world():
    l.debug('hello osm')
    return 'Hello, osm!'


#@app.route('/load_shape', methods=['POST'])
#def load_shape():
#    app.logger.info('load_shape')
#    data = request.json
#    g = cobra_gdal.cobra_gdal()
#    try:
#        app.logger.debug(data)
#        #app.logger.info(f'{data['path']}')
#        g.shape2pg(data.get('path'))
#    except Exception as inst:
#        app.logger.error(inst)
#    finally:
#        return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')