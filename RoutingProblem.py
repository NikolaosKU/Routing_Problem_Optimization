import json
import folium.plugins
import plotly.graph_objects as go
from IPython.display import display
import os
import seaborn as sns
import folium
from OSRM import osrm_get_route
import pandas as pd
import webbrowser
from Distances import get_straight_line_distance
from colour import Color

class RoutingProblem:
    
    def __init__(self, problem_name):
        self.name = problem_name
        self.data = {
            'name': problem_name,
            'coordinate_list': None,
            'depot_index': 0,
            'distance_matrices': {},
            'nb_vehicles': None,
            'capacities': None,
            'demands': None,
            'solutions': {},
        }

    def add_coordinates(self, coordinate_list):
        self.data['coordinate_list'] = coordinate_list

    def get_coordinates(self):
        return self.data['coordinate_list']

    def set_demands(self, demands):
        self.data['demands'] = demands

    def get_demands(self):
        return self.data['demands']

    def set_capacities(self, nb_vehicles, capacities):
        assert nb_vehicles == len(capacities)
        self.data['nb_vehicles'] = nb_vehicles
        self.data['capacities'] = capacities
    
    def get_nb_vehicles(self):
        return self.data['nb_vehicles']
    
    def get_capacities(self):
        return self.data['capacities']

    def change_depot_index(self, index):
        self.data['depot_index'] = index
    
    def get_depot(self):
        return self.get_coordinates()[self.data['depot_index']]

    def add_distance_matrix(self, matrix_name, matrix):
        self.data['distance_matrices'][matrix_name] = matrix

    def get_all_distance_matrices(self):
        return self.data['distance_matrices']
    
    def get_distance_matrix(self, matrix_name):
        return self.data['distance_matrices'][matrix_name] 

    def save(self, prefix=""):
        with open('./RoutingProblems/'+prefix+self.name+'.json', 'w') as output_file:
            json.dump(self.data, output_file)

    def load(self):
        with open('./RoutingProblems/'+self.name+'.json', 'r') as inp:
            self.data = json.load(inp)
            self.name = self.data['name']

    def is_saved(self):
        return os.path.isfile('./RoutingProblems/'+self.name+'.json')

    def add_solution(self, solution_name, solution):
        '''
        Store a solution for this problem with a given name for the solution
        Input arguments: solution_name, solution
        solution_name must be a string
        solution is a dict that contains 1 or more key-value pairs. 
            key: string which indicates the name of the route 
            value: a list of indices of coordinates in coordinate_list in the visiting order
        '''
        self.data['solutions'][solution_name] = solution

    def get_solutions(self):
        return self.data['solutions']
    
    def get_solution(self, solution_name):
        return self.data['solutions'][solution_name]

    def get_metrics(self, original_solution_name=None ,add_osrm_route_metric=False):
        """
        Calculates and compares the following metrics of every solution:
        - Total straight line distance of all routes
        - Total real distance of all routes (OSRM)
        - Total real distance of all routes (openrouteservice)
        """
        header = ['Routing Problem', 'Solution', 'Metric', 'Total', 'Improvment']
        results = []
        # Loop over every solution for this problem
        for solution_name, solution in self.get_solutions().items():
            # Loop over every metric for this problem
            for matrix_name, matrix in self.get_all_distance_matrices().items():
                # Calculate the total value of the selected solution using this metric
                total_metric = 0
                for route_name, indices in solution.items():
                    route_metric = 0
                    for i in range(len(indices) - 1):
                        index_from = indices[i]
                        index_to = indices[i+1]
                        route_metric += matrix[index_from][index_to]
                    total_metric += route_metric
                # Calculate the total value of the selected solution using this metric and the improvement
                if original_solution_name is not None:
                    total_metric_original = 0
                    for route_name, indices in self.get_solution(original_solution_name).items():
                        route_metric = 0
                        for i in range(len(indices) - 1):
                            index_from = indices[i]
                            index_to = indices[i+1]
                            total_metric_original += matrix[index_from][index_to]
                        total_metric_original += route_metric
                    improvement = (total_metric_original - total_metric) / total_metric_original
                else:
                    improvement = 0
                # Add a row to the results
                results.append([self.name, solution_name, matrix_name, total_metric, improvement])
            # Add the OSRM route metric (if applicable)
            if add_osrm_route_metric:
                # Calculate the total value of the selected solution using this metric
                total_metric = 0
                for route_name, indices in solution.items():
                    coordinate_list = [self.get_coordinates()[index] for index in indices]
                    segments, route_distance = osrm_get_route(coordinate_list)
                    total_metric += route_distance
                # Calculate the total value of the selected solution using this metric and the improvement
                if original_solution_name is not None:
                    total_metric_original = 0
                    for route_name, indices in self.get_solution(original_solution_name).items():
                        coordinate_list = [self.get_coordinates()[index] for index in indices]
                        segments, route_distance = osrm_get_route(coordinate_list)
                        total_metric_original += route_distance
                    improvement = (total_metric_original - total_metric) / total_metric_original
                else:
                    improvement = 0
                results.append([self.name, solution_name, 'osrm_route', total_metric, improvement])
        return pd.DataFrame(results, columns=header)

    def plot_folium(self):
        # Create the map
        colors = ['#174EA6','#A50E0E','#E37400','#0D652D','#34A853','#4285F4','#EA4335','#FBBC04','#9AA0A6','#202124']
        map = folium.Map(location=self.get_depot(), zoom_start=13, control_scale=True)
        folium.TileLayer('openstreetmap').add_to(map)
        folium.TileLayer('CartoDB Positron').add_to(map)

        color_index = 0
        for solution_name, solution in self.get_solutions().items():
            for route_name, index_list in solution.items():
                
                # Create a new layer with real route
                color_index += 1
                if color_index == len(colors):
                    color_index = 0
                real_layer = folium.FeatureGroup(name=solution_name+" "+"ON ROAD", show=False).add_to(map)
                coordinate_list = [self.get_coordinates()[index] for index in index_list]
                segmented_route_coordinates, distance = osrm_get_route(coordinate_list)
                # Add the stops and walking lines
                for stop_index, segment_coordinates in enumerate(segmented_route_coordinates):
                    folium.PolyLine(locations=segment_coordinates, color=colors[color_index]).add_to(real_layer)
                    """
                    folium.PolyLine(locations=[segment_coordinates[0], coordinate_list[stop_index]], color='#202124').add_to(real_layer)
                    folium.CircleMarker(location=segment_coordinates[0], radius=2, color=colors[color_index], fill_color='white', fill_opacity=1).add_to(real_layer)
                    """

                # Create a new layer with direct route
                color_index += 1
                if color_index == len(colors):
                    color_index = 0
                direct_layer = folium.FeatureGroup(name=solution_name+" "+"DIRECT", show=False).add_to(map)
                coordinate_list = [self.get_coordinates()[index] for index in index_list]
                folium.PolyLine(locations=coordinate_list, color=colors[color_index]).add_to(direct_layer)

                # Create a new layer with markers
                marker_layer = folium.FeatureGroup(name=solution_name+" "+"MARKERS", show=False).add_to(map)
                coordinate_list = [self.get_coordinates()[index] for index in index_list]
                segmented_route_coordinates, distance = osrm_get_route(coordinate_list)            
                # Add stops as Markers with the number
                for index, stop_coordinate in enumerate(coordinate_list):
                    folium.Marker(location=stop_coordinate,
                                  icon=folium.plugins.BeautifyIcon(
                                    icon="arrow-down", 
                                    icon_shape="marker", 
                                    border_color='#cc7a00', 
                                    background_color='#ff9900',
                                    number=str(index))).add_to(marker_layer)

        # Create demo layer
        index_from = 0
        index_to = 25
        current_index = 20
        solution_name = 'OPTIMAL (REAL)'
        # Create a new layer with real route
        demo_layer = folium.FeatureGroup(name="DEMO", show=False).add_to(map)
        index_list = self.get_solution(solution_name)['TSP_1']
        coordinate_list = [self.get_coordinates()[index] for index in index_list]
        segmented_route_coordinates, distance = osrm_get_route(coordinate_list)
        # Add the stops and walking lines
        for stop_index, segment_coordinates in enumerate(segmented_route_coordinates):
            if stop_index <= current_index:
                folium.PolyLine(locations=segment_coordinates, color='#9AA0A6').add_to(demo_layer)
                folium.Marker(location=segment_coordinates[-1],
                                  icon=folium.plugins.BeautifyIcon(
                                    icon="arrow-down", 
                                    icon_shape="marker", 
                                    border_color='#9AA0A6', 
                                    background_color='#9AA0A6',
                                    number=str(stop_index))).add_to(demo_layer)
            elif stop_index <= index_to:
                folium.PolyLine(locations=segment_coordinates, color=colors[0]).add_to(demo_layer)
                folium.Marker(location=segment_coordinates[-1],
                                  icon=folium.plugins.BeautifyIcon(
                                    icon="arrow-down", 
                                    icon_shape="marker", 
                                    border_color=colors[0], 
                                    background_color=colors[0],
                                    number=str(stop_index))).add_to(demo_layer)

        # Add layer control and open map
        folium.LayerControl().add_to(map)
        map.fit_bounds(map.get_bounds())
        map_name = './maps/map'+'_'+self.name+".html"
        map.save(map_name)
        #webbrowser.open(map_name, new=2)
    
    def plot(self, real=False):
        # Depot
        fig = go.Figure()
        
        # Routes
        for solution_name, solution in self.get_solutions().items():
            for route_name, index_list in solution.items():
                coordinate_list = [self.get_coordinates()[index] for index in index_list]
                if real:
                    plot_coordinate_list, distance = osrm_get_route(coordinate_list)
                else:
                    plot_coordinate_list = coordinate_list
                latitude, longitude = [list(x) for x in zip(*plot_coordinate_list)]
                fig.add_trace(go.Scattermapbox(
                    name= solution_name+' '+route_name,
                    mode = 'lines',
                    line=go.scattermapbox.Line(
                        width=3,
                        color='rgb(120, 120, 120)',
                    ),
                    lon = longitude,
                    lat = latitude))
            
                # Markers
                latitude, longitude = [list(x) for x in zip(*coordinate_list)]
                fig.add_trace(go.Scattermapbox(
                    name= solution_name+' '+route_name,
                    mode = 'markers+text',
                    marker=go.scattermapbox.Marker(
                        size=30,
                        color='rgb(255, 255, 255)',
                        opacity=1.0
                    ),
                    text= [i for i in range(len(latitude))],
                    lon = longitude,
                    lat = latitude))
                fig.add_trace(go.Scattermapbox(
                    name= solution_name+' '+route_name,
                    mode = 'markers+text',
                    marker=go.scattermapbox.Marker(
                        size=25,
                        color='rgb(230, 96, 14)',
                        opacity=1.0
                    ),
                    text= [i for i in range(len(latitude))],
                    lon = longitude,
                    lat = latitude))

                


        fig.update_layout(
            margin ={'l':0,'t':0,'b':0,'r':0},
            mapbox = {
                'style': 'open-street-map',
                #'style': 'carto-positron',
                'zoom': 10,
                'center': go.layout.mapbox.Center(lat=self.get_depot()[0], lon=self.get_depot()[1])
                }
            )

        fig.show()