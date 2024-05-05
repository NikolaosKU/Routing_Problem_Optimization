"""
Class to create distance matrices from a list of latitudes and longitudes. 
Leveraging the OSRM API for real-distance calculations. 

- The 'fetch_osrm_route_geometry' function can fetch not only the distance but also the route geometry, allowing for further analysis or visualization if required. 
- The 'get_real_distance' function is streamlined to return just the distance or an infinite distance in case of an error, preserving the integrity of the distance matrix by ensuring all entries are filled.

Author: Achilles Demey, Nikolaos Kales
"""
import math
import pandas as pd
import geopy.distance
import requests
import polyline

def fetch_osrm_route_geometry(from_node, to_node):
    """
    Fetches the route geometry from the OSRM API between two points.
    It returns the distance and the route geometry.
    """
    try:
        response = requests.get(
            f"http://router.project-osrm.org/route/v1/driving/"
            f"{from_node[1]},{from_node[0]};{to_node[1]},{to_node[0]}?overview=full"
        )
        if response.status_code == 200:
            route = response.json()['routes'][0]
            distance = route['distance']  # Get distance in meters
            # Decode polyline to a list of coordinates if needed
            route_geometry = polyline.decode(route['geometry'])
            return distance, route_geometry
        else:
            response.raise_for_status()
    except Exception as e:
        print(f"Error fetching OSRM route: {e}")
        return None, None
        
        
def osrm_all_points_geometry(points):
    # Convert list of points to a semicolon-separated string
    points_str = ";".join([f"{point[1]},{point[0]}" for point in points])
    print('points_str',points_str)
    
    response = requests.get(
    f"http://router.project-osrm.org/route/v1/driving/"
    f"{points_str}?overview=full")

    if response.status_code == 200:
        route = response.json()['routes'][0]
        # Decode polyline to a list of coordinates
        route_geometry = polyline.decode(route['geometry'])
        distance = route['distance']  # Get distance in meters
        return distance,route_geometry
    else:
        raise Exception("OSRM request failed")
    



def fetch_osrm_table_service(points):
    # Convert list of points to a semicolon-separated string
    points_str = ";".join([f"{point[1]},{point[0]}" for point in points])
    
    response = requests.get(
    'https://router.project-osrm.org/table/v1/driving/points_str?annotations=distance,duration',verify=False)
    if response.status_code == 200:
        print('response', response.json())
        distance_matrix = response.json()['distances']
        duration_matrix = response.json()['durations']
        return distance_matrix,duration_matrix
        #return None
    else:
        raise Exception("OSRM request failed")
    

    

# Function to get the route geometries
def get_route_geometries(data, route):
    """ gets the route geometries for a given route"""
    geometries = []
    for i in range(len(route) - 1):
        geom = fetch_osrm_route_geometry(data['locations'][route[i]], data['locations'][route[i+1]])
        geometries.extend(geom[1])
    #geometries = [ x for xs in geometries for x in xs ]
    return geometries



def get_real_distance(coord1, coord2):
    """
    Get the real distance between source and destination coordinates based on an API."""
    distance, _ = fetch_osrm_route_geometry(coord1, coord2)
    return distance if distance is not None else float('inf')



def get_euclidean_distance(coord1, coord2):
    """calculates the Euclidean distance between two points."""
    return math.hypot((coord1[0] - coord2[0]), (coord1[1] - coord2[1]))



def get_straight_line_distance(coord1, coord2):
    """calculates the straight-line distance between two points using the geodesic distance."""
    return geopy.distance.geodesic(coord1, coord2).m
    
def get_straight_line_distance_matrix(coordinate_list):
    distance_matrix = []
    for from_counter, from_node in enumerate(coordinate_list):
        distance_matrix.append([])
        for to_counter, to_node in enumerate(coordinate_list):
            if from_counter == to_counter:
                distance_matrix[from_counter] += [0]
            else:
                distance_matrix[from_counter].append(geopy.distance.geodesic(from_node, to_node).m)
    return distance_matrix

def get_real_distance_matrix(coordinate_list):
    distance_matrix = []
    for from_node in coordinate_list:
        row = []
        for to_node in coordinate_list:
            if from_node == to_node:
                row.append(0)
            else:
                distance = get_real_distance(from_node, to_node)  
                row.append(distance)
        distance_matrix.append(row)
    return distance_matrix


def get_route_real_distance(coordinate_list):
    """Calculates the total real distance for a sequence of coordinates. 
    It iterates over each pair of consecutive coordinates in the sequence, 
    calculates the real distance between them using the get_real_distance function (which fetches the real distance from the OSRM API),
    and adds this distance to a running total. 
    The total distance is then returned."""
    total_distance = 0
    for index in range(len(coordinate_list)-1):
        coord_1 = coordinate_list[index]
        coord_2 = coordinate_list[index+1]
        total_distance += get_real_distance(coord_1, coord_2)
    return total_distance

def get_route_straight_line_distance(coordinate_list):
    total_distance = 0
    for index in range(len(coordinate_list)-1):
        coord_1 = coordinate_list[index]
        coord_2 = coordinate_list[index+1]
        total_distance += get_straight_line_distance(coord_1, coord_2)
    return total_distance


class StraightLineDistanceMatrix:

    def __init__(self, locations):
        self.LOCATIONS = locations
        self.MATRIX = None
        self.TYPE = "STRAIGHT LINE"
        self.calculate_distance_matrix()



    def calculate_distance_matrix(self):
        distance_matrix = []
        for from_counter, from_node in enumerate(self.LOCATIONS):
            distance_matrix.append([])
            for to_counter, to_node in enumerate(self.LOCATIONS):
                if from_counter == to_counter:
                    distance_matrix[from_counter] += [0]
                else:
                    distance_matrix[from_counter].append(geopy.distance.geodesic(from_node, to_node).m)
        self.MATRIX = distance_matrix



    def get_matrix(self):
        return self.MATRIX



    def __str__(self):
        if self.MATRIX is None:
            return "No matrix calculated"
        else:
            print("Matrix type: ", self.TYPE)
            print(pd.DataFrame(self.MATRIX))
            return ""

class RealDistanceMatrix:

    """This class represents a matrix of real distances (based on routes from the OSRM API) between a set of locations."""

    def __init__(self, locations, depot=[51.0206803530003, 3.7406690974811703]):

        """
        The constructor takes a list of locations and an optional depot location as input
        and initializes the DEPOT, LOCATIONS, MATRIX, and TYPE attributes. 
        It then calls the calculate_distance_matrix method to calculate the distance matrix.
        """

        self.DEPOT = depot
        self.LOCATIONS = locations
        self.TYPE = "REAL DISTANCE"
        self.MATRIX = fetch_osrm_table_service(self.LOCATIONS)





    def get_matrix(self):
        """ returns the distance matrix """
        return self.MATRIX
    


    def __str__(self):


        """
        Returns a string representation of the distance matrix. 
        If the matrix is None, it returns the string “No matrix calculated”.
        Otherwise, it prints the type of the matrix and the matrix itself as a pandas DataFrame.
        """
        if self.MATRIX is None:
            return "No matrix calculated"
        else:
            print("Matrix type: ", self.TYPE)
            print(pd.DataFrame(self.MATRIX))
            return ""

    # Modified fetch function to also get and return geometry
    def fetch_osrm_route_geometry(from_node, to_node):
        response = requests.get(
            f"http://router.project-osrm.org/route/v1/driving/"
            f"{from_node[1]},{from_node[0]};{to_node[1]},{to_node[0]}?overview=full"
        )
        if response.status_code == 200:
            route = response.json()['routes'][0]
            # Decode polyline to a list of coordinates
            route_geometry = polyline.decode(route['geometry'])
            return route_geometry
        else:
            raise Exception("OSRM request failed")

    # Function to get the route geometries
    def get_route_geometries(route):
        geometries = []
        for i in range(len(route) - 1):
            geom = fetch_osrm_route_geometry(data['locations'][route[i]], data['locations'][route[i + 1]])
            geometries.extend(geom)
        return geometries


    def calculate_distance_matrix(self, locations, type="REAL DISTANCE", add_depot=True):
        distance_matrix = [[0 if i == j else None for j in range(len(locations))] for i in range(len(locations))]
        # Create a thread pool executor to send requests in parallel
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Dictionary to hold future to location index mappings
            future_to_location = {}
            # Submit all OSRM requests to the executor
            for i, origin in enumerate(locations):
                for j, destination in enumerate(locations):
                    if i != j:
                        # Submit the fetch function to the executor
                        future = executor.submit(fetch_osrm_distance, origin, destination)
                        future_to_location[future] = (i, j)
            
            # As each request completes, record the result in the distance matrix
            for future in as_completed(future_to_location):
                i, j = future_to_location[future]
                try:
                    # Get the result from the future
                    distance_matrix[i][j] = future.result()
                except Exception as e:
                    print(f"Request failed: {e}")
                    distance_matrix[i][j] = float('inf')

        # Fill in any missing entries in the distance matrix
        for i in range(len(locations)):
            for j in range(len(locations)):
                if distance_matrix[i][j] is None:
                    distance_matrix[i][j] = distance_matrix[j][i]

        self.MATRIX = distance_matrix



