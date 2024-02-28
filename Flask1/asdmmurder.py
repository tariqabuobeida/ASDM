import cx_Oracle
import json
from flask import Flask, request, jsonify, render_template, Response
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

#######

def all_geometries():
    conn = cx_Oracle.connect(dsn=app.config['DATABASE_DSN'],
                         user=app.config['DATABASE_USER'],
                         password=app.config['DATABASE_PASSWORD'])

    c = conn.cursor()

    # Execute your query
    c.execute("""SELECT SDO_UTIL.TO_GEOJSON(g.location) 
              AS geojson, g.geometry_type, g.description FROM GEOMETRIES G
""")



    # Construct GeoJSON features including the DESCRIPTION
    geojson_features = []
    for geojson,geometry_type,description in c:
        feature = {
            'type': 'Feature',
            'geometry': json.loads(geojson.read()),
            'properties': {
                'Type' : geometry_type,
                'Description': description
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
@app.route('/all_geometries')
def all_geojson():
    geojson_data = all_geometries()
    return Response(json.dumps(geojson_data), mimetype='application/json')

#######


def fetch_nearest_polygon():
    conn = cx_Oracle.connect(dsn=app.config['DATABASE_DSN'],
                             user=app.config['DATABASE_USER'],
                             password=app.config['DATABASE_PASSWORD'])
    cursor = conn.cursor()

    # Execute your query
    cursor.execute("""
    SELECT SDO_UTIL.TO_GEOJSON(g.location) AS geojson, sq.name, sq.type, sq.details, sq.distance_to_polygon
    FROM (
        SELECT e.geometry_id, e.name, e.type, e.details,
            MIN(SDO_GEOM.SDO_DISTANCE(g.location, p.current_location, 0.005)) AS distance_to_polygon
        FROM GAME_ELEMENTS e
        JOIN GEOMETRIES g ON e.geometry_id = g.geometry_id
        CROSS JOIN (SELECT current_location FROM PLAYERS WHERE player_id = 2) p
        WHERE e.type = 'Area'
        GROUP BY e.geometry_id, e.name, e.type, e.details
    ) sq
    JOIN GEOMETRIES g ON sq.geometry_id = g.geometry_id
    ORDER BY sq.distance_to_polygon ASC
    FETCH FIRST ROW ONLY
    """)

    # Construct GeoJSON features including the DESCRIPTION
    geojson_features = []
    for row in cursor:
        geojson, name, type, details, distance_to_polygon = row
        feature = {
            'type': 'Feature',
            'geometry': json.loads(geojson.read() if geojson else '{}'),
            'properties': {
                'Name': name,
                'Type': type,
                'Details': details,
                'DistanceToPolygon': distance_to_polygon
            }
        }
        geojson_features.append(feature)

    geojson_collection = {
        'type': 'FeatureCollection',
        'features': geojson_features
    }

    cursor.close()
    conn.close()

    return geojson_collection
@app.route('/nearest_polygon')
def nearest_polygon():
    geojson_data = fetch_nearest_polygon()
    return Response(json.dumps(geojson_data), mimetype='application/json')


### polygon Distance
def fetch_polygon_distance():
    conn = cx_Oracle.connect(dsn=app.config['DATABASE_DSN'],
                             user=app.config['DATABASE_USER'],
                             password=app.config['DATABASE_PASSWORD'])
    cursor = conn.cursor()

    # Execute your query
    cursor.execute("""
    SELECT SDO_UTIL.TO_GEOJSON(g.location) AS geojson, sq.name, sq.type, sq.details, sq.distance_to_polygon
    FROM (
        SELECT e.geometry_id, e.name, e.type, e.details,
            MIN(SDO_GEOM.SDO_DISTANCE(g.location, p.current_location, 0.005)) AS distance_to_polygon
        FROM GAME_ELEMENTS e
        JOIN GEOMETRIES g ON e.geometry_id = g.geometry_id
        CROSS JOIN (SELECT current_location FROM PLAYERS WHERE player_id = 2) p
        WHERE e.type = 'Area'
        GROUP BY e.geometry_id, e.name, e.type, e.details
    ) sq
    JOIN GEOMETRIES g ON sq.geometry_id = g.geometry_id
    ORDER BY sq.distance_to_polygon ASC
    """)

    # Construct GeoJSON features including the DESCRIPTION
    geojson_features = []
    for row in cursor:
        geojson, name, type, details, distance_to_polygon = row
        feature = {
            'type': 'Feature',
            'geometry': json.loads(geojson.read() if geojson else '{}'),
            'properties': {
                'Name': name,
                'Type': type,
                'Details': details,
                'DistanceToPolygon': distance_to_polygon
            }
        }
        geojson_features.append(feature)

    geojson_collection = {
        'type': 'FeatureCollection',
        'features': geojson_features
    }

    cursor.close()
    conn.close()

    return geojson_collection
@app.route('/polygon_distance')
def polygon_distance():
    geojson_data = fetch_polygon_distance()
    return Response(json.dumps(geojson_data), mimetype='application/json')


### polygon Distance

@app.route('/update-location', methods=['POST'])
def update_location():
    data = request.json
    player_id = data['player_id']
    lat = data['lat']
    lon = data['lon']
    print(lat, lon)

    conn = None
    cursor = None
    try:
        # Establish the database connection
        conn = cx_Oracle.connect(dsn=app.config['DATABASE_DSN'],
                                 user=app.config['DATABASE_USER'],
                                 password=app.config['DATABASE_PASSWORD'])
        # Create a new cursor
        cursor = conn.cursor()
        # Update the current_location of the player
        update_query = """
        UPDATE PLAYERS
        SET current_location = SDO_GEOMETRY(2001, 8307, SDO_POINT_TYPE(:lon, :lat, NULL), NULL, NULL)
        WHERE player_id = :player_id
        """
        cursor.execute(update_query, [lon, lat, player_id])
        conn.commit()
        return jsonify({"success": True, "message": "Location updated successfully"})
    except Exception as e:
        print("Error:", e)
        return jsonify({"success": False, "message": str(e)})
    finally:
        # Ensure the cursor and connection are properly closed
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/')
def home():
    # Render the index.html file
    return render_template('index.html')


if __name__ == '__main__':
    app.run(port=50003, debug=True)
# host='www.geos.ed.ac.uk'