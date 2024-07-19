import cx_Oracle
import json
from flask import Flask, request, jsonify, render_template, Response
from flask_cors import CORS
app = Flask(__name__)
CORS(app)

#Reading the Credential
app.config.from_object('config')

## Sitong's


def fetch_geojson(query):
    conn = cx_Oracle.connect(dsn=app.config['DATABASE_DSN'],
                         user=app.config['DATABASE_USER'],
                         password=app.config['DATABASE_PASSWORD'])
    c = conn.cursor()

    # Execute the query 
    c.execute(query)
    
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

def fetch_CL(player_id):
    conn = cx_Oracle.connect(dsn=app.config['DATABASE_DSN'],
                         user=app.config['DATABASE_USER'],
                         password=app.config['DATABASE_PASSWORD'])
    c = conn.cursor()

    query = """
    SELECT SDO_UTIL.TO_GEOJSON(current_location) AS geojson
    FROM players
    WHERE player_id = :player_id
    """

    # Execute the query with player_id as a bind variable
    c.execute(query, player_id=player_id)

    # Construct GeoJSON features including the DESCRIPTION
    geojson_features = []
    for row in c:
        geojson_lob = row[0]
        geojson_str = geojson_lob.read()
        feature = {
            'type': 'Feature',
            'geometry': json.loads(geojson_str),
            'properties': {
                'description': 'you are here',
                #add a class to remind this marker could be updated
                'markerClass': 'updated-marker'
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

def update_current_location(player_id, geometry_id):
    try:
        #Query to obtain the SDO_GEOMETRY data of the specified geometry_id
        select_query = """
        SELECT LOCATION
        FROM GEOMETRIES
        WHERE GEOMETRY_ID = :geometry_id
        """

        # Connection Settings
        conn = cx_Oracle.connect(dsn=app.config['DATABASE_DSN'],
                            user=app.config['DATABASE_USER'],
                            password=app.config['DATABASE_PASSWORD'])
        c = conn.cursor()


        # Execute Query
        c.execute(select_query, geometry_id=geometry_id)
        result = c.fetchone()

        if result:
            # Get SDO Geometry
            location_data = result[0]

            # Update Player's Location
            update_query = """
            UPDATE players 
            SET current_location = :location_data
            WHERE player_id = :player_id
            """

            # Execute update query
            c.execute(update_query, location_data=location_data, player_id=player_id)
            conn.commit()

            # Return Sucess Messege or other data
            return None
        else:
            return jsonify({'error': 'The specified one cannot be found geometry_id'})

    except Exception as e:
        # # If an exception occurs, return an error message
        return jsonify({'error': str(e)})

    finally:
        # Close cursor and connection
        c.close()
        conn.close()
    
def get_path(line_id):
    conn = cx_Oracle.connect(dsn=app.config['DATABASE_DSN'],
                         user=app.config['DATABASE_USER'],
                         password=app.config['DATABASE_PASSWORD'])
    c = conn.cursor()

    try:
        # Get Geosjosn
        viquery = f"""
        SELECT SDO_UTIL.TO_GEOJSON(LOCATION) AS geojson, DESCRIPTION 
        FROM GEOMETRIES 
        WHERE geometry_id = {line_id}
        """
        pathdata = fetch_geojson(viquery)

        # Calculate disance
        # distancequery = f"""
        # SELECT SDO_GEOM.SDO_DISTANCE(p.current_location, g.location, 0.005)
        # FROM players p
        # JOIN geometries g ON g.geometry_id = {point_id}
        # WHERE p.player_id = {player_id}
        # """
        distancequery = f"""
        SELECT SDO_GEOM.SDO_LENGTH(g.location, m.diminfo)
        FROM GEOMETRIES g
        JOIN user_sdo_geom_metadata m 
        ON m.table_name = 'GEOMETRIES' AND m.column_name = 'LOCATION'
        WHERE g.geometry_id = {line_id}
        """
        c.execute(distancequery)
        distance_result = c.fetchone()[0]

        # Add the distance to the properties of the first feature in pathdata
        if pathdata['features']:
            pathdata['features'][0]['properties']['distance'] = distance_result

        return jsonify(pathdata)

    except Exception as e:
        return jsonify({'error': str(e)})#Calculate Distance

    finally:
        c.close()
        conn.close()

def update_interactions(player_id, geometry_id):
    try:
        # Query to obtain all element_ids related to the specified geometry_id
        element_ids_query = """
        SELECT ELEMENT_ID
        FROM GAME_ELEMENTS
        WHERE GEOMETRY_ID = :geometry_id
        """

        # Connection
        conn = cx_Oracle.connect(dsn=app.config['DATABASE_DSN'],
                            user=app.config['DATABASE_USER'],
                            password=app.config['DATABASE_PASSWORD'])
        c = conn.cursor()


        # Excute query to get element_ids
        c.execute(element_ids_query, geometry_id=geometry_id)
        element_ids = [row[0] for row in c.fetchall()]

        # Insert into INTERACTIONS table
        insert_query = """
        INSERT INTO INTERACTIONS (PLAYER_ID, ELEMENT_ID, INTERACTION_TIME)
        VALUES (:player_id, :element_id, CURRENT_TIMESTAMP)
        """

        for element_id in element_ids:
            c.execute(insert_query,player_id=player_id, element_id=element_id)

        conn.commit()

        # Returns a success message or other necessary data
        return None
        #return jsonify({'message': 'succeed!'})

    except Exception as e:
        # If an exception occurs, an error message is returned
        return jsonify({'error': str(e)})

    finally:
        # Close Connection
        c.close()
        conn.close()

def get_items(player_id):
    # Connect to DB
    conn = cx_Oracle.connect(dsn=app.config['DATABASE_DSN'],
                         user=app.config['DATABASE_USER'],
                         password=app.config['DATABASE_PASSWORD'])
    c = conn.cursor()

    try:
        # Use JOIN to connect two tables
        query = """
        SELECT ge.name, ge.details
        FROM game_elements ge
        JOIN interactions i ON ge.element_id = i.element_id
        WHERE i.player_id = :player_id
        AND ge.type = 'Item'
        """

        c.execute(query, player_id=player_id)
        result = c.fetchall()

        if not result:
            return jsonify({'message': "You haven't collected any item!"})

        c.close()
        # Return JSON data
        return jsonify({'game_elements': result})

    except Exception as e:
        return jsonify({'error': str(e)})

    finally:
        # close connection
        conn.close()

def initialise_puzzle_location(player_id,puzzle_id):
    #get the coordinate of left bottom
    if puzzle_id==1:
        geometry_id=19
    elif puzzle_id==2:
        geometry_id=20
    elif puzzle_id==3:
        geometry_id=22
    elif puzzle_id==4:
        geometry_id=24

    puzzlequery="""
    SELECT SDO_UTIL.TO_GEOJSON(LOCATION) AS geojson, DESCRIPTION 
    FROM GEOMETRIES WHERE GEOMETRY_ID= :geometry_id
    """
    conn = cx_Oracle.connect(dsn=app.config['DATABASE_DSN'],
                         user=app.config['DATABASE_USER'],
                         password=app.config['DATABASE_PASSWORD'])
    c = conn.cursor()

    c.execute(puzzlequery,{'geometry_id':geometry_id})
    result=c.fetchall()
    formatted_result = [{'geojson': json.loads(str(row[0])), 'description': row[1]} for row in result]
    second_coordinate = formatted_result[0]['geojson']['coordinates'][0][1]

    x=second_coordinate[0]
    y=second_coordinate[1]
    srid=8307

    #update current location to the left bottom point
    update_query = """
    UPDATE players 
    SET current_location = SDO_GEOMETRY('POINT (' || :x || ' ' || :y || ')', :srid)
    WHERE player_id = :player_id
    """
    try:
        # update
        c.execute(update_query, {'x': x, 'y': y, 'srid': srid, 'player_id': player_id})
        conn.commit()
        return None
    except Exception as e:
        return jsonify({'error': str(e)})
    
    finally:
        c.close()
        conn.close()

def clear_interactions():
    try:
        # Define the DELETE query
        delete_query = 'DELETE FROM interactions'

        conn = cx_Oracle.connect(dsn=app.config['DATABASE_DSN'],
                            user=app.config['DATABASE_USER'],
                            password=app.config['DATABASE_PASSWORD'])
        c = conn.cursor()


        # Execute the DELETE query
        c.execute(delete_query)#计算距离
        conn.commit()

        return jsonify({'message': 'succeed!'})

    except cx_Oracle.Error as error:
        print(f"Error: {error}")
    
    finally:
        # Close cursor and connection
        c.close()
        conn.close()

@app.route('/enterPuzzle/1/polygon',endpoint='#Calculate_distance_puzzle1p')
def Puzzle1polygon():
    puzzle1query="""
    SELECT SDO_UTIL.TO_GEOJSON(LOCATION) AS geojson, DESCRIPTION 
    FROM GEOMETRIES WHERE GEOMETRY_ID=19
    """
    puzzle1=fetch_geojson(puzzle1query)
    return jsonify(puzzle1)

@app.route('/enterPuzzle/1/marker',endpoint='puzzle1m')
def Puzzle1marker():
    clear_interactions()
    player_id=1
    puzzle_id=1
    initialise_puzzle_location(player_id,puzzle_id)
    CL=fetch_CL(player_id)
    return jsonify(CL)

@app.route('/enterPuzzle/1/clue',endpoint='puzzle1c')
def Puzzle1clue():
    cluequery="""
    SELECT SDO_UTIL.TO_GEOJSON(LOCATION) AS geojson, DESCRIPTION
    FROM GEOMETRIES
    WHERE GEOMETRY_ID in (1,2)
    """
    clue=fetch_geojson(cluequery)
    return jsonify(clue)

@app.route('/enterPuzzle/2/polygon',endpoint='puzzle2p')
def Puzzle2polygon():
    puzzle2query="""
    SELECT SDO_UTIL.TO_GEOJSON(LOCATION) AS geojson, DESCRIPTION 
    FROM GEOMETRIES WHERE GEOMETRY_ID=20
    """
    puzzle2=fetch_geojson(puzzle2query)
    return jsonify(puzzle2)

@app.route('/enterPuzzle/2/marker',endpoint='puzzle2m')
def Puzzle2marker():
    player_id=1
    puzzle_id=2
    initialise_puzzle_location(player_id,puzzle_id)
    CL=fetch_CL(player_id)
    return jsonify(CL)

@app.route('/enterPuzzle/2/clue',endpoint='puzzle2c')
def Puzzle2clue():
    cluequery="""
    SELECT SDO_UTIL.TO_GEOJSON(LOCATION) AS geojson, DESCRIPTION
    FROM GEOMETRIES
    WHERE GEOMETRY_ID in (4,5,6,56)
    """
    clue=fetch_geojson(cluequery)
    return jsonify(clue)

@app.route('/enterPuzzle/3/polygon',endpoint='puzzle3p')
def Puzzle3polygon():
    puzzle3query="""
    SELECT SDO_UTIL.TO_GEOJSON(LOCATION) AS geojson, DESCRIPTION 
    FROM GEOMETRIES WHERE GEOMETRY_ID=22
    """
    puzzle3=fetch_geojson(puzzle3query)
    return jsonify(puzzle3)

@app.route('/enterPuzzle/3/marker',endpoint='puzzle3m')
def Puzzle3marker():
    player_id=1
    puzzle_id=3
    initialise_puzzle_location(player_id,puzzle_id)
    CL=fetch_CL(player_id)
    return jsonify(CL)

@app.route('/enterPuzzle/3/clue',endpoint='puzzle3c')
def Puzzle3clue():
    cluequery="""
    SELECT SDO_UTIL.TO_GEOJSON(LOCATION) AS geojson, DESCRIPTION
    FROM GEOMETRIES
    WHERE GEOMETRY_ID in (8,9,10)
    """
    clue=fetch_geojson(cluequery)
    return jsonify(clue)

@app.route('/enterPuzzle/4/polygon',endpoint='puzzle4p')
def Puzzle4polygon():
    puzzle4query="""
    SELECT SDO_UTIL.TO_GEOJSON(LOCATION) AS geojson, DESCRIPTION 
    FROM GEOMETRIES WHERE GEOMETRY_ID=24
    """
    puzzle4=fetch_geojson(puzzle4query)
    return jsonify(puzzle4)

@app.route('/enterPuzzle/4/marker',endpoint='puzzle4m')
def Puzzle4marker():
    player_id=1
    puzzle_id=4
    initialise_puzzle_location(player_id,puzzle_id)
    CL=fetch_CL(player_id)
    return jsonify(CL)

@app.route('/enterPuzzle/4/clue',endpoint='puzzle4c')
def Puzzle4clue():
    cluequery="""
    SELECT SDO_UTIL.TO_GEOJSON(LOCATION) AS geojson, DESCRIPTION
    FROM GEOMETRIES
    WHERE GEOMETRY_ID=12
    """
    clue=fetch_geojson(cluequery)
    return jsonify(clue)



@app.route('/path/101',endpoint='path101')
def path101():
    return get_path(33)
        
@app.route('/path/102',endpoint='path102')
def path102():
    return get_path(35)

@app.route('/path/103',endpoint='path103')
def path103():
    return get_path(34)

@app.route('/path/112',endpoint='path112')
def path112():
    return get_path(37)

@app.route('/path/113',endpoint='path113')
def path113():
    return get_path(36)

@app.route('/path/123',endpoint='path123')
def path123():
    return get_path(38)

@app.route('/path/201',endpoint='path201')
def path201():
    return get_path(39)

@app.route('/path/212',endpoint='path212')
def path212():
    return get_path(41)

@app.route('/path/223',endpoint='path223')
def path223():
    return get_path(43)

@app.route('/path/234',endpoint='path234')
def path223():
    return get_path(59)

@app.route('/path/301',endpoint='path301')
def path301():
    return get_path(44)

@app.route('/path/302',endpoint='path302')
def path302():
    return get_path(45)

@app.route('/path/303',endpoint='path303')
def path303():
    return get_path(46)

@app.route('/path/321',endpoint='path321')
def path321():
    return get_path(47)

@app.route('/path/323',endpoint='path323')
def path323():
    return get_path(49)

@app.route('/path/313',endpoint='path313')
def path313():
    return get_path(48)

@app.route('/path/401',endpoint='path401')
def path401():
    return get_path(50)
        
@app.route('/path/402',endpoint='path402')
def path402():
    return get_path(51)

@app.route('/path/403',endpoint='path403')
def path403():
    return get_path(52)

@app.route('/path/412',endpoint='path412')
def path412():
    return get_path(53)

@app.route('/path/413',endpoint='path413')
def path413():
    return get_path(54)

@app.route('/path/432',endpoint='path432')
def path432():
    return get_path(55)




@app.route('/move/11',endpoint='move11')
def move11():
    player_id=1
    geometry_id=1
    update_current_location(player_id,geometry_id)
    update_interactions(player_id,geometry_id)
    CL=fetch_CL(player_id)
    return jsonify(CL)

@app.route('/move/12',endpoint='move12')
def move12():
    player_id=1
    geometry_id=2
    update_current_location(player_id,geometry_id)
    update_interactions(player_id,geometry_id)
    CL=fetch_CL(player_id)
    return jsonify(CL)

@app.route('/move/13',endpoint='move13')
def move13():
    player_id=1
    geometry_id=3
    update_current_location(player_id,geometry_id)
    update_interactions(player_id,geometry_id)
    CL=fetch_CL(player_id)
    return jsonify(CL)

@app.route('/move/21',endpoint='move21')
def move21():
    player_id=1
    geometry_id=4
    update_current_location(player_id,geometry_id)
    update_interactions(player_id,geometry_id)
    CL=fetch_CL(player_id)
    return jsonify(CL)

@app.route('/move/22',endpoint='move22')
def move22():
    player_id=1
    geometry_id=5
    update_current_location(player_id,geometry_id)
    update_interactions(player_id,geometry_id)
    CL=fetch_CL(player_id)
    return jsonify(CL)

@app.route('/move/23',endpoint='move23')
def move23():
    player_id=1
    geometry_id=6
    update_current_location(player_id,geometry_id)
    update_interactions(player_id,geometry_id)
    CL=fetch_CL(player_id)
    return jsonify(CL)

@app.route('/move/24',endpoint='move24')
def move24():
    player_id=1
    geometry_id=56
    update_current_location(player_id,geometry_id)
    update_interactions(player_id,geometry_id)
    CL=fetch_CL(player_id)
    return jsonify(CL)

@app.route('/move/32',endpoint='move32')
def move32():
    player_id=1
    geometry_id=9
    update_current_location(player_id,geometry_id)
    update_interactions(player_id,geometry_id)
    CL=fetch_CL(player_id)
    return jsonify(CL)

@app.route('/move/31',endpoint='move31')
def move31():
    player_id=1
    geometry_id=8
    update_current_location(player_id,geometry_id)
    update_interactions(player_id,geometry_id)
    CL=fetch_CL(player_id)
    return jsonify(CL)

@app.route('/move/33',endpoint='move33')
def move33():
    player_id=1
    geometry_id=10
    update_current_location(player_id,geometry_id)
    update_interactions(player_id,geometry_id)
    CL=fetch_CL(player_id)
    return jsonify(CL)

@app.route('/move/41',endpoint='move41')
def move41():
    player_id=1
    geometry_id=12
    update_current_location(player_id,geometry_id)
    update_interactions(player_id,geometry_id)
    CL=fetch_CL(player_id)
    return jsonify(CL)

@app.route('/move/43',endpoint='move43')
def move43():
    player_id=1
    geometry_id=14
    update_current_location(player_id,geometry_id)
    update_interactions(player_id,geometry_id)
    CL=fetch_CL(player_id)
    return jsonify(CL)

@app.route('/move/42',endpoint='move42')
def move42():
    player_id=1
    geometry_id=13
    update_current_location(player_id,geometry_id)
    update_interactions(player_id,geometry_id)
    CL=fetch_CL(player_id)
    return jsonify(CL)


@app.route('/collected_items')
def collectitems():
    return get_items(1)

## Sitong's


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