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
            c.execute(insert_query, player_id=player_id, element_id=element_id)

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

def enterpuzzle(puzzle_id,player_id):
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

    return jsonify(x)


    coordinates = puzzlejson_data['features'][0]['geometry']['coordinates'][0]
    second_point = coordinates[1]
    x, y = second_point
    srid = 8307

    #update current location to the left bottom point
    update_query = """
    UPDATE players 
    SET current_location = SDO_GEOMETRY('POINT (' || :x || ' ' || :y || ')', :srid)
    WHERE player_id = :player_id
    """
    conn = cx_Oracle.connect(dsn="geoslearn", user="s2606314", password="fudge")
    c = conn.cursor()
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

@app.route('/enterPuzzle/1')
def puzzle1json():
    puzzle1query="""
    SELECT SDO_UTIL.TO_GEOJSON(LOCATION) AS geojson, DESCRIPTION 
    FROM GEOMETRIES WHERE GEOMETRY_ID=19
    """
    puzzle1json_data=fetch_geojson(puzzle1query)
    #return jsonify(puzzle1json_data)

    #get coordinates of polygon
    coordinates = puzzle1json_data['features'][0]['geometry']['coordinates'][0]
    # get the coordinates of the second point
    second_point = coordinates[1]
    x, y = second_point

    srid = 8307 

    #update current location
    update_query = """
    UPDATE players 
    SET current_location = SDO_GEOMETRY('POINT (' || :x || ' ' || :y || ')', :srid)
    WHERE player_id = :player_id
    """

    conn = cx_Oracle.connect(dsn="geoslearn", user="s2606314", password="fudge")
    c = conn.cursor()

    try:
        # update
        c.execute(update_query, x=x, y=y, srid=srid, player_id=1)
        conn.commit()

        # add update result
        #response_data = {'message': 'Update successful', 'geojson_data': puzzle1json_data}
        return jsonify(puzzle1json_data)

    except Exception as e:
        return jsonify({'error': str(e)})

    finally:
        c.close()
        conn.close()

@app.route('/enterPuzzle/2')
def puzzle2json():
    enterpuzzle(2,1)
    CL=fetch_CL(1)
    return jsonify(CL)

@app.route('/path/1/s1',endpoint='path1s1')
def paths1():
    return get_path(33)
        
@app.route('/path/1/s2',endpoint='path1s2')
def pathp2():
    return get_path(35)
        
@app.route('/path/1/s3',endpoint='path1s3')
def pathp3():
    return get_path(34)

@app.route('/move/11')
def move11():
    update_current_location(1,1)
    update_interactions(1,1)
    CL=fetch_CL(1)
    return jsonify(CL)

@app.route('/path/2/s1',endpoint='path2s1')
def pathp3():
    return get_path(39)

# @app.route('/update_interactions')
# def updatetest():
#     return update_interactions(1,3)

@app.route('/collected_items/1')
def collectitems1():
    return get_items(1)

@app.route('/path/1/12',endpoint='path112')
def paths1():
    return get_path(37)

@app.route('/path/1/13',endpoint='path113')
def paths1():
    return get_path(36)

@app.route('/move/12')
def move12():
    update_current_location(1,2)
    update_interactions(1,2)
    CL=fetch_CL(1)
    return jsonify(CL)

@app.route('/path/1/23',endpoint='path123')
def paths1():
    return get_path(38)

@app.route('/move/13')
def move13():
    update_current_location(1,3)
    update_interactions(1,3)
    CL=fetch_CL(1)
    return jsonify(CL)

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
