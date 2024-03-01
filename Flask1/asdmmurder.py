import cx_Oracle
import json
from flask import Flask, request, jsonify, render_template, Response
from flask_cors import CORS
app = Flask(__name__)
CORS(app)

#Reading the Credential
app.config.from_object('config')

## Entre New Area
def fetch_enter_new_area():
    conn = cx_Oracle.connect(dsn=app.config['DATABASE_DSN'],
                         user=app.config['DATABASE_USER'],
                         password=app.config['DATABASE_PASSWORD'])

    c = conn.cursor()

    # Execute your query
    c.execute("""
    SELECT 
        SDO_UTIL.TO_GEOJSON(g.location) AS geojson, 
        e.name, 
        e.type, 
        e.details
    FROM 
        GAME_ELEMENTS e
    JOIN 
        GEOMETRIES g ON e.geometry_id = g.geometry_id
    WHERE 
        e.geometry_id IN (
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
    AND e.type IN ('Clue', 'Suspect') 
    AND g.geometry_id NOT IN (13, 14, 12)

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

        # print(feature)
        geojson_features.append(feature)
    
    geojson_collection = {
        'type': 'FeatureCollection',
        'features': geojson_features
    }

    c.close()
    conn.close()

    return geojson_collection
@app.route('/enter_new_area')
def enter_new_area():
    geojson_data = fetch_enter_new_area()
    return Response(json.dumps(geojson_data), mimetype='application/json')
## Enter New Area


## All geometries
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

        # print(feature)
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
## All geometries

## Nearest polygon
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
## Nearest polygon

### Polygon Distance
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
### Polygon Distance

## Polygon area
def fetch_polygon_area():
    conn = cx_Oracle.connect(dsn=app.config['DATABASE_DSN'],
                             user=app.config['DATABASE_USER'],
                             password=app.config['DATABASE_PASSWORD'])
    cursor = conn.cursor()

    # Execute your query
    cursor.execute(""" 
                   SELECT SDO_UTIL.TO_GEOJSON(g.location), e.element_id, e.name, 
                    ROUND(SDO_GEOM.SDO_AREA(g.location, 0.005), 2) AS area
                    FROM GAME_ELEMENTS e
                    JOIN Geometries g ON e.geometry_id = g.geometry_id
                    WHERE e.type = 'Area'
    """)

    # Construct GeoJSON features including the DESCRIPTION
    geojson_features = []
    for row in cursor:
        geojson, element_id, name, area = row
        feature = {
            'type': 'Feature',
            'geometry': json.loads(geojson.read() if geojson else '{}'),
            'properties': {
                'Element ID': element_id,
                'Name': name,
                'Area': area
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
@app.route('/polygon_area')
def polygon_area():
    geojson_data = fetch_polygon_area()
    return Response(json.dumps(geojson_data), mimetype='application/json')
## Polygon area

## Game Elements within 200m
def fetch_200m_search():
    conn = cx_Oracle.connect(dsn=app.config['DATABASE_DSN'],
                             user=app.config['DATABASE_USER'],
                             password=app.config['DATABASE_PASSWORD'])
    cursor = conn.cursor()

    # Execute your query
    cursor.execute(""" 
        SELECT SDO_UTIL.TO_GEOJSON(g.location) AS geojson, e.element_id, e.name, e.type, e.details
            FROM GAME_ELEMENTS e
            JOIN GEOMETRIES g ON e.geometry_id = g.geometry_id
            WHERE SDO_WITHIN_DISTANCE(
            g.location, 
            (SELECT current_location FROM PLAYERS WHERE player_id = 2), 
            'distance=200 unit=METER') = 'TRUE'
    """)

    # Construct GeoJSON features including the DESCRIPTION
    geojson_features = []
    for row in cursor:
        geojson, element_id, name, type, details = row
        feature = {
            'type': 'Feature',
            'geometry': json.loads(geojson.read() if geojson else '{}'),
            'properties': {
                'Element ID': element_id,
                'Name': name,
                'Type': type,
                'Details': details
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
@app.route('/200m_search')
def search_200m():
    geojson_data = fetch_200m_search()
    return Response(json.dumps(geojson_data), mimetype='application/json')
## Game Elements Within 200m 

## Buffer Suspect 400m
def fetch_400m_susbuf():
    conn = cx_Oracle.connect(dsn=app.config['DATABASE_DSN'],
                             user=app.config['DATABASE_USER'],
                             password=app.config['DATABASE_PASSWORD'])
    cursor = conn.cursor()

    # Execute your query
    cursor.execute(""" 
        SELECT SDO_UTIL.TO_GEOJSON(SDO_GEOM.SDO_BUFFER(g.location, 400, 0.005)) AS geojson, e.name, e.type
                FROM GAME_ELEMENTS e
                JOIN GEOMETRIES g ON e.geometry_id = g.geometry_id
               WHERE e.type = 'Suspect'
    """)

    # Construct GeoJSON features including the DESCRIPTION
    geojson_features = []
    for row in cursor:
        geojson, name, type = row
        feature = {
            'type': 'Feature',
            'geometry': json.loads(geojson.read() if geojson else '{}'),
            'properties': {
                'Name': name,
                'Type': type,
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
@app.route('/400m_susbuf')
def susbuf_200m():
    geojson_data = fetch_400m_susbuf()
    return Response(json.dumps(geojson_data), mimetype='application/json')
# Buffer Suspect 400m


## Buffer Suspect 40m
def fetch_40m_susbuf():
    conn = cx_Oracle.connect(dsn=app.config['DATABASE_DSN'],
                             user=app.config['DATABASE_USER'],
                             password=app.config['DATABASE_PASSWORD'])
    cursor = conn.cursor()

    # Execute your query
    cursor.execute(""" 
        SELECT SDO_UTIL.TO_GEOJSON(SDO_GEOM.SDO_BUFFER(g.location, 40, 0.005)) AS buffered_geojson, e.name, e.type
        FROM GAME_ELEMENTS e
        JOIN GEOMETRIES g ON e.geometry_id = g.geometry_id
        WHERE e.type = 'Suspect'
        AND SDO_WITHIN_DISTANCE(g.location, 
            (SELECT p.current_location 
            FROM PLAYERS p
            WHERE p.player_id = 2), 'distance = 100') = 'TRUE'
        AND EXISTS (
        SELECT 1
        FROM GAME_ELEMENTS area
        JOIN GEOMETRIES area_g ON area.geometry_id = area_g.geometry_id
        WHERE area.type IN ('Area', 'Solution Area')
        AND SDO_CONTAINS(area_g.location, 
            (SELECT p.current_location
                FROM PLAYERS p
                WHERE p.player_id = 2)) = 'TRUE'
        AND SDO_CONTAINS(area_g.location, g.location) = 'TRUE'
    )
    """)

    # Construct GeoJSON features including the DESCRIPTION
    geojson_features = []
    for row in cursor:
        buffered_geojson, name, type = row
        feature = {
            'type': 'Feature',
            'geometry': json.loads(buffered_geojson.read() if buffered_geojson else '{}'),
            'properties': {
                'Name': name,
                'Type': type,
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
@app.route('/40m_susbuf')
def susbuf_40m():
    geojson_data = fetch_40m_susbuf()
    return Response(json.dumps(geojson_data), mimetype='application/json')
# Buffer Suspect 40m

## Nearest Point
def fetch_nearest_point():
    conn = cx_Oracle.connect(dsn=app.config['DATABASE_DSN'],
                             user=app.config['DATABASE_USER'],
                             password=app.config['DATABASE_PASSWORD'])
    cursor = conn.cursor()

    # Execute your query
    cursor.execute(""" 
    SELECT  SDO_UTIL.TO_GEOJSON(g.location) AS geojson, e.name, e.type, e.details, 
                   ROUND(SDO_GEOM.SDO_DISTANCE(g.location, p.current_location, 0.005), 2) AS distance 
                   FROM  GAME_ELEMENTS e JOIN  GEOMETRIES g ON e.geometry_id = g.geometry_id JOIN  PLAYERS p ON p.player_id = 2 
                   WHERE  e.type IN ('Clue', 'Suspect', 'Item') ORDER BY  distance ASC FETCH FIRST 1 ROW ONLY
    """)

    # Construct GeoJSON features including the DESCRIPTION
    geojson_features = []
    for row in cursor:
        geojson, name, type, details, distance = row
        feature = {
            'type': 'Feature',
            'geometry': json.loads(geojson.read() if geojson else '{}'),
            'properties': {
                'Name': name,
                'Type': type,
                'Details': details,
                'Distance': distance
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
@app.route('/nearest_point')
def nearest_point():
    geojson_data = fetch_nearest_point()
    return Response(json.dumps(geojson_data), mimetype='application/json')
# Nearest Point



## Puzzle 2 solution 
def fetch_puzzle2_solution():
    conn = cx_Oracle.connect(dsn=app.config['DATABASE_DSN'],
                             user=app.config['DATABASE_USER'],
                             password=app.config['DATABASE_PASSWORD'])
    cursor = conn.cursor()

    # Execute your query
    cursor.execute(""" 
SELECT 
        SDO_UTIL.TO_GEOJSON(g.location) AS geojson,
        e.name, 
        e.type, 
        e.details
        
        FROM 
            GAME_ELEMENTS e
        JOIN 
            GEOMETRIES g ON e.geometry_id = g.geometry_id
        WHERE 
        e.element_id = 7
    """)

    # Construct GeoJSON features including the DESCRIPTION
    geojson_features = []
    for row in cursor:
        geojson, name, type, details= row
        feature = {
            'type': 'Feature',
            'geometry': json.loads(geojson.read() if geojson else '{}'),
            'properties': {
                'Name': name,
                'Type': type,
                'Details': details
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
@app.route('/puzzle2_solution')
def puzle2_solution():
    geojson_data = fetch_puzzle2_solution()
    return Response(json.dumps(geojson_data), mimetype='application/json')
#  Puzzle 2 Solution

## Puzzle 3 solution 
def fetch_puzzle3_solution():
    conn = cx_Oracle.connect(dsn=app.config['DATABASE_DSN'],
                             user=app.config['DATABASE_USER'],
                             password=app.config['DATABASE_PASSWORD'])
    cursor = conn.cursor()

    # Execute your query
    cursor.execute(""" 
SELECT 
        SDO_UTIL.TO_GEOJSON(g.location) AS geojson,
        e.name, 
        e.type, 
        e.details
        
        FROM 
            GAME_ELEMENTS e
        JOIN 
            GEOMETRIES g ON e.geometry_id = g.geometry_id
        WHERE 
        e.element_id = 12
    """)

    # Construct GeoJSON features including the DESCRIPTION
    geojson_features = []
    for row in cursor:
        geojson, name, type, details= row
        feature = {
            'type': 'Feature',
            'geometry': json.loads(geojson.read() if geojson else '{}'),
            'properties': {
                'Name': name,
                'Type': type,
                'Details': details
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
@app.route('/puzzle3_solution')
def puzle3_solution():
    geojson_data = fetch_puzzle3_solution()
    return Response(json.dumps(geojson_data), mimetype='application/json')
#  Puzzle 3 Solution

## Enter Polygon 4
def fetch_enter_polygon4():
    conn = cx_Oracle.connect(dsn=app.config['DATABASE_DSN'],
                             user=app.config['DATABASE_USER'],
                             password=app.config['DATABASE_PASSWORD'])
    cursor = conn.cursor()

    # Execute your query
    cursor.execute(""" 
SELECT 
    SDO_UTIL.TO_GEOJSON(g.location) AS geojson, 
    e.name, 
    e.type, 
    e.details
FROM 
    GAME_ELEMENTS e
JOIN 
    GEOMETRIES g ON e.geometry_id = g.geometry_id
WHERE 
    g.geometry_id = 24 AND e.type = 'Area'
UNION ALL
SELECT 
    SDO_UTIL.TO_GEOJSON(g.location) AS geojson, 
    e.name, 
    e.type, 
    e.details
FROM 
    GAME_ELEMENTS e
JOIN 
    GEOMETRIES g ON e.geometry_id = g.geometry_id
JOIN 
    PLAYERS p ON p.player_id = 2
WHERE 
    SDO_CONTAINS(
        (SELECT location FROM GEOMETRIES WHERE geometry_id = 24), 
        g.location
    ) = 'TRUE'
    AND e.type IN ('Clue', 'Suspect', 'Item')
    AND EXISTS (
        SELECT 1 
        FROM PLAYERS p
        WHERE p.player_id = 2
        AND SDO_CONTAINS(
            (SELECT location FROM GEOMETRIES WHERE geometry_id = 19), 
            p.current_location
        ) = 'TRUE'
        AND SDO_WITHIN_DISTANCE(
            p.current_location, 
            (SELECT location FROM GEOMETRIES WHERE geometry_id = 24), 
            'distance=300 unit=METER'
        ) = 'TRUE')

    """)

    # Construct GeoJSON features including the DESCRIPTION
    geojson_features = []
    for row in cursor:
        geojson, name, type, details= row
        feature = {
            'type': 'Feature',
            'geometry': json.loads(geojson.read() if geojson else '{}'),
            'properties': {
                'Name': name,
                'Type': type,
                'Details': details
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
@app.route('/enter_polygon4')
def enter_polygon4():
    geojson_data = fetch_enter_polygon4()
    return Response(json.dumps(geojson_data), mimetype='application/json')
#  Enter Polygon 4


## Find Item 100m
def fetch_find_item100m():
    conn = cx_Oracle.connect(dsn=app.config['DATABASE_DSN'],
                             user=app.config['DATABASE_USER'],
                             password=app.config['DATABASE_PASSWORD'])
    cursor = conn.cursor()

    # Execute your query
    cursor.execute(""" 
    SELECT 
        SDO_UTIL.TO_GEOJSON(g.location) AS geojson,           
        e.element_id AS item_id, 
        e.name AS item_name, 
        e.type AS item_type, 
        e.details AS item_details
    FROM 
        GAME_ELEMENTS e
    JOIN 
        GEOMETRIES g ON e.geometry_id = g.geometry_id,
        (SELECT current_location FROM PLAYERS WHERE player_id = 2) p
    WHERE 
        e.type = 'Item'
        AND SDO_WITHIN_DISTANCE(g.location, p.current_location, 'distance=100 unit=METER') = 'TRUE'
        AND EXISTS (
            SELECT 1
            FROM GAME_ELEMENTS e2
            JOIN GEOMETRIES g2 ON e2.geometry_id = g2.geometry_id
            WHERE (e2.type = 'Area' OR e2.type = 'Solution Area')
            AND SDO_CONTAINS(g2.location, g.location) = 'TRUE'
            AND SDO_CONTAINS(g2.location, p.current_location) = 'TRUE'
    )

    """)

    # Construct GeoJSON features including the DESCRIPTION
    geojson_features = []
    for row in cursor:
        geojson, item_id, name, type, item_details= row
        feature = {
            'type': 'Feature',
            'geometry': json.loads(geojson.read() if geojson else '{}'),
            'properties': {
                'Item ID': item_id,
                'Name': name,
                'Type': type,
                'Details': item_details
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
@app.route('/find_item100m')
def find_item100m():
    geojson_data = fetch_find_item100m()
    return Response(json.dumps(geojson_data), mimetype='application/json')
#  Find Item 100m



## Find the culprit
def fetch_the_culprit():
    conn = cx_Oracle.connect(dsn=app.config['DATABASE_DSN'],
                             user=app.config['DATABASE_USER'],
                             password=app.config['DATABASE_PASSWORD'])
    cursor = conn.cursor()

    # Execute your query
    cursor.execute(""" 
        SELECT 
        SDO_UTIL.TO_GEOJSON(SDO_GEOM.SDO_BUFFER(g.location, 1000, 0.005)) AS buffered_geojson,
        e.element_id, 
        e.type
        
    FROM 
        GAME_ELEMENTS e
    JOIN 
        GEOMETRIES g ON e.geometry_id = g.geometry_id
    WHERE 
        e.type = 'Item'
        AND NOT EXISTS (
            SELECT 1
            FROM GAME_ELEMENTS polygons
            JOIN GEOMETRIES polyGeom ON polygons.geometry_id = polyGeom.geometry_id
            WHERE polygons.type IN ('Area', 'Solution Area')
            AND SDO_CONTAINS(polyGeom.location, g.location) = 'TRUE'
        )

    """)

    # Construct GeoJSON features including the DESCRIPTION
    geojson_features = []
    for row in cursor:
        buffered_geojson, element_id, type = row
        feature = {
            'type': 'Feature',
            'geometry': json.loads(buffered_geojson.read() if buffered_geojson else '{}'),
            'properties': {
                'Item ID': element_id,
                'Type': type,
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
@app.route('/find_culprit')
def find_culprit():
    geojson_data = fetch_the_culprit()
    return Response(json.dumps(geojson_data), mimetype='application/json')
#  Find the culprit




## Update location
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
## Update location
            
## Render html
@app.route('/')
def home():
    # Render the index.html file
    return render_template('index.html')
## Render html

if __name__ == '__main__':
    app.run(port=50003, debug=True)
# host='www.geos.ed.ac.uk/dev/asdmmurder' for web hosting