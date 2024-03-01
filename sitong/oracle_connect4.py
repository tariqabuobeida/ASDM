import cx_Oracle
from flask import Flask, jsonify
import json
from flask_cors import CORS


app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes and domains

def fetch_geojson():
    conn = cx_Oracle.connect(dsn="geoslearn", user="s2606314", password="fudge")
    c = conn.cursor()

    # Execute the query to fetch the location as GeoJSON and the DESCRIPTION field
    c.execute("""
        SELECT SDO_UTIL.TO_GEOJSON(LOCATION) AS geojson, DESCRIPTION
        FROM GEOMETRIES
    """)
    
    # Construct GeoJSON features including the DESCRIPTION
    geojson_features = []
    for geojson, description in c:
        # Parse the GeoJSON geometry and append the DESCRIPTION to its properties
        feature = {
            'type': 'Feature',
            'geometry': json.loads(geojson.read()),
            'properties': {
                'description': description  # Add other attributes here as needed
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
    return "Welcome! Please visit /geojson to see the GeoJSON or /map for the map."

if __name__ == '__main__':
    app.run(debug=True)
