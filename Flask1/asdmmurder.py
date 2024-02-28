import cx_Oracle
import json
from flask import Flask, jsonify, render_template, Response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

#Reading the Credential
app.config.from_object('config')

def fetch_geojson():
    conn = cx_Oracle.connect(dsn=app.config['DATABASE_DSN'],
                         user=app.config['DATABASE_USER'],
                         password=app.config['DATABASE_PASSWORD'])

    c = conn.cursor()

    # Execute your query
    c.execute("""SELECT SDO_UTIL.TO_GEOJSON(g.location) AS geojson, e.name, e.type, e.Details
FROM GAME_ELEMENTS e
JOIN GEOMETRIES g ON e.geometry_id = g.geometry_id
WHERE e.geometry_id IN (
      SELECT e.geometry_id
      FROM GAME_ELEMENTS e
      JOIN GEOMETRIES g ON e.geometry_id = g.geometry_id
      WHERE SDO_CONTAINS(
            (SELECT location FROM GEOMETRIES WHERE geometry_id = (
                 SELECT g.geometry_id
                 FROM GAME_ELEMENTS e
                 JOIN GEOMETRIES g ON e.geometry_id = g.geometry_id
                 WHERE e.type = 'Area'
                 AND SDO_CONTAINS(g.location, (SELECT current_location FROM PLAYERS WHERE player_id = 2)) = 'TRUE'
            )),
            g.location) = 'TRUE'
      UNION
      SELECT g.geometry_id
      FROM GAME_ELEMENTS e
      JOIN GEOMETRIES g ON e.geometry_id = g.geometry_id
      WHERE e.type = 'Area'
      AND SDO_CONTAINS(g.location, (SELECT current_location FROM PLAYERS WHERE player_id = 2)) = 'TRUE'
)
""")



    # Construct GeoJSON features including the DESCRIPTION
    geojson_features = []
    for geojson,name,type,Details in c:
        feature = {
            'type': 'Feature',
            'geometry': json.loads(geojson.read()),
            'properties': {
                'Name' : name,
                'Type' : type,
                'Details': Details
            }
        }

        print(feature)
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
    return Response(json.dumps(geojson_data), mimetype='application/json')

@app.route('/')
def home():
    # Render the index.html file
    return render_template('index.html')


if __name__ == '__main__':
    app.run(port=50002, debug=True)
# host='www.geos.ed.ac.uk'