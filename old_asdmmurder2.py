import cx_Oracle
import json
from flask import Flask, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def fetch_geojson():
    conn = cx_Oracle.connect(dsn="geoslearn", user="s2606314", password="fudge")
    c = conn.cursor()

    # Execute your query
    c.execute("""SELECT SDO_UTIL.TO_GEOJSON(LOCATION) AS geojson, DESCRIPTION
        FROM GEOMETRIES""")

    # Construct GeoJSON features including the DESCRIPTION
    geojson_features = []
    for geojson, description in c:
        feature = {
            'type': 'Feature',
            'geometry': json.loads(geojson.read()),
            'properties': {
                'description': description
            }
        }
        geojson_features.append(feature)
    
    geojson_collection = {
        'type': 'FeatureCollection',
        'features': geojson_features
    }

    c.close()
    conn.close()

    return geojson_collection

@app.route('/geojson')
def geojson():
    geojson_data = fetch_geojson()
    return jsonify(geojson_data)

@app.route('/')
def home():
    # Render the index.html file
    return render_template('index.html')


if __name__ == '__main__':
    app.run(host='www.geos.ed.ac.uk', port=55411, debug=True)
