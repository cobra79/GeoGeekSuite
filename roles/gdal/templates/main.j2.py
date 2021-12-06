import cobra_logging
import cobra_gdal
from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, Docker!'

@app.route('/load_shape', methods=['POST'])
def load_shape():
    data = request.json
    g = cobra_gdal.cobra_gdal()
    try:
        g.shape2pg(data.path)
    except:
        print('Did not work')
    finally:
        return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')