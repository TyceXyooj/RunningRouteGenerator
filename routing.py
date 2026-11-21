#Author: Tyce Xiong
#This file contains methods to generate a path and return them as usable files or data
#see README.md for credits
import random as rand
import math as m
import osmnx as ox
import networkx as nx
import geopandas as gpd
import json

#returns a graph with the nodes/edges of a route the distance of the number, plus the start node
def _find_path(street, city, state, zip, distance):
    #creating necessary variables
    result = nx.MultiDiGraph()
    min_len = distance - 800
    max_len = distance + 800
    address = f'{street}, {city}, {state} {zip}'
    print('Downloading Map...')

    try:
        map = ox.graph_from_address(address, distance, simplify=False)
    except Exception as e:
        print(f'Geocoding failed for {address}: {e}')
        return -1, None
        
    map = ox.simplify_graph(map)
    map = ox.convert.to_digraph(map, weight='length')
    addlat, addlon = ox.geocode(address)
    start_node = ox.nearest_nodes(map, X=addlon, Y=addlat)
   
    print('Starting route search...')
    # limits attempts to 1000 to avoid an infinite loop
    for attempts in range(1000):
        print(f'Attempt #{attempts + 1}')
        path_out_len = 0.0
        current_node = start_node
        temp = nx.MultiDiGraph()
        # converts standard graph to map graph
        temp.graph['crs'] = map.graph['crs']
        temp.add_node(start_node)
        
        route_edges = []
        out_goal = rand.uniform(0.53, 0.6) * distance
        portion_of_out_goal = rand.uniform(0.35, 0.75) * out_goal
          
        print('Building first half...')
        # builds a path taking the edge that results in the furthest distance from the start
        # until portion_of_out_goal has been reached
        while path_out_len < portion_of_out_goal:
            options = list(map.out_edges(current_node, data=True))
            previous_node = route_edges[-1][0] if route_edges else None
            
            recent_targets = {e[1] for e in route_edges[-10:]}
            valid_options = [
                edge for edge in options 
                # 1. Must not be one of the last 10 target nodes traveled
                if edge[1] not in recent_targets
                # 2. Must not lead right back to where we just came from (prevents immediate U-turns)
                and edge[1] != previous_node
            ]
            
            # Fallback: if we hit a dead end, allow backtracking to previous_node
            if len(valid_options) == 0 and previous_node is not None:
                valid_options = [edge for edge in options if edge[1] == previous_node]

            if len(valid_options) == 0:
                print("First third hit a dead end. Retrying attempt...")
                break
    
            # scores potential edges and chooses the one that results in the furthest node
            next_edge = _run_away(start_node, valid_options, map)
            # updates trackers
            temp.add_edge(current_node, next_edge[1], **next_edge[2])       
            route_edges.append((current_node, next_edge[1], next_edge[2]))
            path_out_len += next_edge[2]['length']
            current_node = next_edge[1]
           
        if path_out_len < portion_of_out_goal:
            continue

        print(f'Path has completed {path_out_len} meters')

        # turn 90 degrees
        runlat, runlon = _get_perpendicular(start_node, current_node, map)
        run_away_from = ox.nearest_nodes(map, X=runlon, Y=runlat)
        
        # go until out_goal has been reached
        steps = 0
        while path_out_len < out_goal:
            options = list(map.out_edges(current_node, data=True))
            previous_node = route_edges[-1][0] if route_edges else None
            
            recent_targets = {e[1] for e in route_edges[-10:]}
            valid_options = [
                edge for edge in options 
                if edge[1] not in recent_targets
                and edge[1] != previous_node
            ]
            
            # Fallback for dead ends
            if len(valid_options) == 0 and previous_node is not None:
                valid_options = [edge for edge in options if edge[1] == previous_node]

            if len(valid_options) == 0:
                print("Second third hit a dead end. Retrying attempt...")
                break

            # scores potential edges and chooses the one that results in the furthest node
            next_edge = _run_away(run_away_from, valid_options, map)
            # updates trackers
            temp.add_edge(current_node, next_edge[1], **next_edge[2])       
            route_edges.append((current_node, next_edge[1], next_edge[2]))
            path_out_len += next_edge[2]['length']
            current_node = next_edge[1]
            steps += 1
            
            if steps > 1000:
                print("Second third got stuck. Retrying attempt...")
                break

        if path_out_len < out_goal:
            continue

        # Finds a path from current_node to start_node that results in a total distance +/- 800m from distance
        try:
            paths_back = nx.shortest_simple_paths(map, current_node, start_node)

            # checks each path back until it finds a path in range
            for paths_back_nodes in paths_back:
                edges_back = []
                return_len = 0
                for i in range(len(paths_back_nodes) - 1):
                    u, v = paths_back_nodes[i], paths_back_nodes[i+1]
                    edge_data = map.get_edge_data(u, v)
                    return_len += edge_data['length']
                    edges_back.append((u, v, edge_data))

                total_len = return_len + path_out_len

                if min_len <= total_len <= max_len:
                    for u, v, data in edges_back:
                        temp.add_edge(u, v, **data)

                    # adds geodata to each node
                    for node in temp.nodes():
                        if node in map.nodes:
                            temp.nodes[node]['x'] = map.nodes[node]['x']
                            temp.nodes[node]['y'] = map.nodes[node]['y']

                    print('Complete!')
                    print(f'Path has completed {total_len} meters')
                    return temp, start_node
                elif total_len > max_len:
                    break

        except nx.NetworkXNoPath:
            continue

    return -1, None

# returns the lat/lon of a point that forms a 90 degree angle with the vertex ab
def _get_perpendicular(a, b, g, rotate_left=True):
    anchor_dist = 3000.0
    R = 6371000.0 # earth's radius in meters
    deg_to_rad = m.pi / 180.0
    rad_to_deg = 180.0 / m.pi
    lat_s = g.nodes[a]['y']
    lon_s = g.nodes[a]['x']
    lat_c = g.nodes[b]['y']
    lon_c = g.nodes[b]['x']

    cos_lat = m.cos(lat_c * deg_to_rad)
    dx = (lon_c - lon_s) * deg_to_rad * R * cos_lat
    dy = (lat_c - lat_s) * deg_to_rad * R

    # checks if a and b are the same
    dist = m.hypot(dx, dy)
    if dist == 0:
        return lat_s, lon_s

    # rotates for the desired direction
    if rotate_left:
        perp_x, perp_y = -dy, dx
    else:
        perp_x, perp_y = dy, -dx

    # project backwards
    ax = -(perp_x / dist) * anchor_dist
    ay = -(perp_y / dist) * anchor_dist

    # convert back to meters
    res_lat = lat_c + (ay / R) * rad_to_deg
    res_lon = lon_c + (ax / (R * cos_lat)) * rad_to_deg

    return res_lat, res_lon

# returns edge that results in the furthest option from start_node
def _run_away(start_node, valid_options, map):
    start_y = map.nodes[start_node]['y']
    start_x = map.nodes[start_node]['x']
    scored_options = []
    for edge in valid_options:
        target_node = edge[1]
        target_y = map.nodes[target_node]['y']
        target_x = map.nodes[target_node]['x']
        dist_from_start = (target_y - start_y)**2 + (target_x - start_x)**2
        scored_options.append((edge, dist_from_start))
    scored_options.sort(key=lambda x: x[1], reverse=True)
    top_pool_size = max(1, len(scored_options) // 2)
    top_choices = [item[0] for item in scored_options[:top_pool_size]]
    next_edge = top_choices[rand.randint(0, len(top_choices) - 1)]
    return next_edge

# helper method that returns an ordered list of coordinates
def _ordered_coords(route, start_node):
    current_node = start_node
    ordered_list = []
    visited_edges = set()

    def add_point(lat, lon):
        if not ordered_list or ordered_list[-1] != (lat, lon):
            ordered_list.append((lat, lon))

    while True:
        current_node_data = route.nodes[current_node]
        add_point(current_node_data['y'], current_node_data['x'])

        out_edges = list(route.out_edges(current_node, keys=True))

        valid_edges = [
            (source_node, target_node, edge_key) for source_node, target_node, edge_key in out_edges
            if (source_node, target_node, edge_key) not in visited_edges
        ]

        if len(valid_edges) == 0:
            break

        source_node, target_node, edge_key = valid_edges[0]
        visited_edges.add((source_node, target_node, edge_key))

        edge_data = route[source_node][target_node][edge_key]

        if 'geometry' in edge_data:
            coords = list(edge_data['geometry'].coords)
            source_lat, source_lon = route.nodes[source_node]['y'], route.nodes[source_node]['x']
            first_lon, first_lat = coords[0]
            last_lon, last_lat = coords[-1]
            first_to_source = (first_lat - source_lat)**2 + (first_lon - source_lon)**2
            last_to_source = (last_lat - source_lat)**2 + (last_lon - source_lon)**2
            
            if last_to_source < first_to_source:
                coords.reverse()
                
            for lon, lat in coords:
                add_point(lat, lon)

        current_node = target_node

        if current_node == start_node:
            add_point(route.nodes[start_node]['y'], route.nodes[start_node]['x'])
            break

    return ordered_list

def route_as_gpx(street, city, state, zip, distance):
    route, start_node = _find_path(street, city, state, zip, distance)
    if route == -1:
        print('No valid route was found')
        return

    file_name = f'{city}_route_{distance}m.gpx'    
    coordinates = _ordered_coords(route, start_node)

    with open(file_name, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<gpx version="1.1" creator="Tyce Xiong" xmlns="http://www.topografix.com/GPX/1/1">\n')
        f.write('  <trk>\n')
        f.write('    <trkseg>\n')
        for lat, lon in coordinates:
            f.write(f'      <trkpt lat="{lat}" lon="{lon}"></trkpt>\n')
        f.write('    </trkseg>\n')
        f.write('  </trk>\n')
        f.write('</gpx>\n')
    
    print(f'File saved as {file_name}')

def route_as_json(street, city, state, zip, distance):
    route, start_node = _find_path(street, city, state, zip, distance)
    if route == -1:
        return 'No route was found'

    coordinates = _ordered_coords(route, start_node)
    geojson_coordinates = [[lon, lat] for lat, lon in coordinates]

    geojson_data = {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": geojson_coordinates
        },
        "properties": {
            "street": street,
            "city": city,
            "state": state,
            "zip": zip,
            "distance": distance,
            "point_count": len(coordinates)
        }
    }

    return json.dumps(geojson_data)