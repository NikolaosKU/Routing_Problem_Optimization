from DatasetClasses import DatasetReader
from RoutingProblem import RoutingProblem
from Distances import get_straight_line_distance_matrix, get_route_straight_line_distance
from Solvers import get_tsp_solution
from OSRM import osrm_get_matrix
import pandas as pd

dataset_name = 'DATASET_SERVICEFREQS_NODUP_20240405.csv'
dataset = DatasetReader(file=dataset_name)

metrics_df = None

for day in range(1, 8):
    routes = dataset.get_routes_of_day(day)
    for route in routes:
        print(route)
        problem_name = str.replace(route, ' ', '_')
        routing_problem = RoutingProblem(problem_name)
        if routing_problem.is_saved():
            # Load a routing problem
            routing_problem.load()
        else:
            # Create a routing problem with the add coordinates and original solution)
            coordinate_list, original_solution = dataset.get_routing_problem_data_for_route(route)

            routing_problem.add_coordinates(coordinate_list)
            routing_problem.add_solution('ORIGINAL', original_solution)

            # Calculate the straight line distance matrix and solution and store
            straight_line_matrix = get_straight_line_distance_matrix(routing_problem.get_coordinates())
            solution_straight_line_indices = get_tsp_solution(straight_line_matrix)

            routing_problem.add_distance_matrix('straight_line', straight_line_matrix)
            routing_problem.add_solution('OPTIMAL (STRAIGHT-LINE)', solution_straight_line_indices)

            # Calculate the OSRM distance and time matrix, get the solutions and store
            osrm_dist, osrm_time = osrm_get_matrix(routing_problem.get_coordinates())
            solution_osrm_dist_indices = get_tsp_solution(osrm_dist)
            solution_osrm_time_indices  = get_tsp_solution(osrm_time)
            
            routing_problem.add_distance_matrix('osrm_distance', osrm_dist)
            routing_problem.add_solution('OPTIMAL (REAL)', solution_osrm_dist_indices)
            """
            routing_problem.add_distance_matrix('osrm_time', osrm_time)
            routing_problem.add_solution('solution (osrm_time)', solution_osrm_time_indices)
            """
            # Save routing problem to a JSON file
            routing_problem.save()
        
        # PLOT ROUTING PROBLEM
        routing_problem.plot_folium()

        # CALCULATE METRICS OF THE ROUTING PROBLEM SOLUTIONS
        routing_problem_metrics_df = routing_problem.get_metrics(original_solution_name='ORIGINAL', add_osrm_route_metric=True)
        if metrics_df is None:
            metrics_df = routing_problem_metrics_df
        else:
            metrics_df = pd.concat([metrics_df, routing_problem_metrics_df])
        print(metrics_df)

    # SAVE METRICS
    metrics_df.to_csv('solution_metrics.csv', sep=';', index=False)
