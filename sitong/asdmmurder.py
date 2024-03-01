import cx_Oracle
from flask import Flask, jsonify, render_template  # Import render_template
import json
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes and domains

def fetch_geojson(query):
    conn = cx_Oracle.connect(dsn="geoslearn", user="s2606314", password="fudge")
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
    conn = cx_Oracle.connect(dsn="geoslearn", user="s2606314", password="fudge")
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
        # 查询获取指定 geometry_id 的 SDO_GEOMETRY 数据
        select_query = """
        SELECT LOCATION
        FROM GEOMETRIES
        WHERE GEOMETRY_ID = :geometry_id
        """

        # 连接设置
        conn = cx_Oracle.connect(dsn="geoslearn", user="s2606314", password="fudge")
        c = conn.cursor()

        # 执行查询
        c.execute(select_query, geometry_id=geometry_id)
        result = c.fetchone()

        if result:
            # 获取 SDO_GEOMETRY 数据
            location_data = result[0]

            # 更新查询
            update_query = """
            UPDATE players 
            SET current_location = :location_data
            WHERE player_id = :player_id
            """

            # 执行更新查询
            c.execute(update_query, location_data=location_data, player_id=player_id)
            conn.commit()

            # 返回成功消息或必要的其他数据
            return None
        else:
            return jsonify({'error': '找不到指定的 geometry_id'})

    except Exception as e:
        # 如果发生异常，则返回错误消息
        return jsonify({'error': str(e)})

    finally:
        # 关闭游标和连接
        c.close()
        conn.close()
    
def get_path(line_id):
    conn = cx_Oracle.connect(dsn="geoslearn", user="s2606314", password="fudge")
    c = conn.cursor()

    try:
        # 获取线的 GeoJSON 数据
        viquery = f"""
        SELECT SDO_UTIL.TO_GEOJSON(LOCATION) AS geojson, DESCRIPTION 
        FROM GEOMETRIES 
        WHERE geometry_id = {line_id}
        """
        pathdata = fetch_geojson(viquery)

        # #计算距离
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

        # 将距离添加到 pathdata 中的第一个 feature 的 properties 中
        if pathdata['features']:
            pathdata['features'][0]['properties']['distance'] = distance_result

        return jsonify(pathdata)

    except Exception as e:
        return jsonify({'error': str(e)})

    finally:
        c.close()
        conn.close()

def update_interactions(player_id, geometry_id):
    try:
        # 查询获取指定 geometry_id 相关的所有 element_ids
        element_ids_query = """
        SELECT ELEMENT_ID
        FROM GAME_ELEMENTS
        WHERE GEOMETRY_ID = :geometry_id
        """

        # 连接设置
        conn = cx_Oracle.connect(dsn="geoslearn", user="s2606314", password="fudge")
        c = conn.cursor()

        # 执行查询以获取 element_ids
        c.execute(element_ids_query, geometry_id=geometry_id)
        element_ids = [row[0] for row in c.fetchall()]

        # 插入到 INTERACTIONS 表中
        insert_query = """
        INSERT INTO INTERACTIONS (PLAYER_ID, ELEMENT_ID, INTERACTION_TIME)
        VALUES (:player_id, :element_id, CURRENT_TIMESTAMP)
        """

        for element_id in element_ids:
            c.execute(insert_query,player_id=player_id, element_id=element_id)

        conn.commit()

        # 返回成功消息或必要的其他数据
        return None
        #return jsonify({'message': 'succeed!'})

    except Exception as e:
        # 如果发生异常，则返回错误消息
        return jsonify({'error': str(e)})

    finally:
        # 关闭游标和连接
        c.close()
        conn.close()

def get_items(player_id):
    # 连接数据库
    conn = cx_Oracle.connect(dsn="geoslearn", user="s2606314", password="fudge")
    c = conn.cursor()

    try:
        # 使用 JOIN 连接两个表
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
        # 返回 JSON 数据
        return jsonify({'game_elements': result})

    except Exception as e:
        return jsonify({'error': str(e)})

    finally:
        # 关闭连接
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
    conn = cx_Oracle.connect(dsn="geoslearn", user="s2606314", password="fudge")
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

        conn = cx_Oracle.connect(dsn="geoslearn", user="s2606314", password="fudge")
        c = conn.cursor()

        # Execute the DELETE query
        c.execute(delete_query)
        conn.commit()

        return jsonify({'message': 'succeed!'})

    except cx_Oracle.Error as error:
        print(f"Error: {error}")
    
    finally:
        # Close cursor and connection
        c.close()
        conn.close()


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

@app.route('/shit')
def shit():
    player_id=1
    geometry_id=3
    shit=update_interactions(player_id,geometry_id)
    return shit


@app.route('/collected_items')
def collectitems():
    return get_items(1)

@app.route('/geojson')
def geojson():
    allquery="""
    SELECT SDO_UTIL.TO_GEOJSON(LOCATION) AS geojson, DESCRIPTION
    FROM GEOMETRIES
    """
    geojson_data = fetch_geojson(allquery)
    return jsonify(geojson_data)

@app.route('/')
def home():
    # Render the index.html file
    return render_template('index.html')

if __name__ == '__main__':
    app.run(port=50001,debug=True)
