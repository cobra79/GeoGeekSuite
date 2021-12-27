import cobra.helper.logging as logging
import cobra.tools.gdal as gdal
from flask import Flask, request, jsonify
app = Flask(__name__)
l = logging.Logger('GDAL Flask')
l.debug('Start Cobra Logging')

#TODO: Schema handling
gdal.Gdal(schema='gis', run_in_loop=True)


@app.route('/')
def hello_world():
    l.debug('hello gdal')
    return 'Hello, GDAL!'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')