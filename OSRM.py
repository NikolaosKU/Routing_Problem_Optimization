import requests
import polyline
from Distances import get_straight_line_distance

def osrm_get_route(coordinate_list, local=True):

    if local:
        url = "http://127.0.0.1:5000/"
    else:
        url = "http://router.project-osrm.org/"
    endpoint = url + "route/v1/car/"

        # Convert list of points to a semicolon-separated string
    points_str = ";".join([f"{point[1]},{point[0]}" for point in coordinate_list])
    request = f"{endpoint}{points_str}?overview=full&steps=true"
    response = requests.get(request)
    if response.status_code == 200:
        legs = response.json()['routes'][0]['legs']
        distance = response.json()['routes'][0]['distance']
        segmented_route = []
        for leg in legs:
            leg_geometry = []
            for step in leg['steps']:
                leg_geometry += polyline.decode(step['geometry'])
            segmented_route.append(leg_geometry)
        return segmented_route, distance
    else:
        print('OSRM request failed')
        exit()    

def osrm_get_matrix(coordinate_list, local=True, curb=True):
    """
    Returns the distance matrix and the time matrix
    """
    if local:
        url = "http://127.0.0.1:5000/"
    else:
        url = "http://router.project-osrm.org/"
    endpoint = url + "table/v1/car/"

    # Convert list of points to a semicolon-separated string
    coordinates = ";".join([f"{point[1]},{point[0]}" for point in coordinate_list])+"?annotations=duration,distance"
    if curb:
        coordinates = coordinates
    #print(len(coordinate_list))
    # Build the request url
    request = f"{endpoint}{coordinates}"
    #print(request)
    response = requests.get(request)
    if response.status_code == 200:
        distance_matrix = response.json()['distances']
        time_matrix = response.json()['durations']
        return distance_matrix, time_matrix
    else:
        return None, None
    